# Reader RW5d: "Show me", explorable figures from a question, a passage or both, a sketch tier, and exploration as evidence (v1)

**Status:** owner-approved 2026-10-25: every recommended answer in §18 adopted as decided. Specification only: no code changed, no model or paid call made, no test run, no vault opened.
- **Base:** `main` at `eae00d58a` (migration head `220_retrieval_spaces.sql`; RW5a and RW5b landed). In flight and read from their specs only: LP claim fixes (migration 221), curriculum C0a (migration 222, `section_coverage` and `reader.correspondents`), Reader CA1 and CA2, the teacher spec rev 4 (approved, not built).
- **Parent specs:** `docs/specs/spec_reader_workbench_v1.md` (§8 RW5, W1–W14, D28, D46, §17), `docs/specs/ux_reader_workbench_v1.md` (§4.0, §4.7, §4.10, §4.12), `docs/specs/ux_reader_compare_ask_v1.md` (§7 Ask, §8.5, §13). This spec adds a phase family, **RW5d**, under RW5. It changes no landed rule; where it amends one, the amendment is named.
- Code paths are under `src/learnloop/` unless they say otherwise. "The figure service" is `figures/service.py`.

---

## 0. Owner direction (verbatim, 2026-10-25)

> "Imagine if we could prompt the tutor/teacher within the reader to make a diagram from a textbook excerpt or natural language query (or jointly). It can build something the user can explore to gain a better intuition on concepts."

The owner approved the orchestrator's framing (three gaps: entry, range, evidence) and said "Draft it". Read as four requirements:
1. **Ask for a figure in your own words**, with or without a passage: a question alone, a passage alone (today's "make this explorable"), or both ("this passage, but with complex eigenvalues").
2. **The figure comes from your books when it can**, and says so when it can't.
3. **When the figure language can't express the idea**, LearnLoop can still build something explorable, honestly labelled.
4. **Exploring is not learning.** What the learner does with a figure is formative, and LearnLoop should learn, over months, whether figures help this learner.

## 1. Thesis

RW5a/b built a good figure *pipeline* with a narrow *door*. The pipeline (a closed declarative grammar, a model author, numeric verification, a trusted renderer, predictions, "not right?", reuse by input hash) is the right core and stays the only figure service. Three things are missing:

- **The door takes no words.** A figure request today is a set of span ids; the learner's text is dropped, and a request with no selection is refused (`figures/service.py:513-515`, "Select a passage, an equation or a figure first."). RW5d adds `FigureRequestV1`: a goal in the learner's words, an optional anchor, and the host it came from. With no anchor, the request is grounded in the learner's library through the existing `find_sources`, so the figure cites their books, or says plainly that it doesn't.
- **The grammar has a ceiling.** Simulations, stochastic processes, agent-based and geometric constructions are refused as "can't draw this yet". RW5d adds a **sketch tier**: a small model-written program that runs in a sealed interpreter with no access to anything, returns a display list the trusted renderer draws, and exposes declared **probes** that code checks against equations stated in the existing grammar. The grammar stays preferred.
- **Exploration evidence goes nowhere new.** Missed predictions already reach learner-text gaps (`service.py:952-956`), which is right and stays. RW5d makes a figure **a help kind**: counted honestly when opened during an attempt, offered by the hint chooser with a logged propensity, and read by RW2c's help outcomes, so "do visuals help you" becomes estimable later without any figure ever certifying anything.

One service, every host: the Reader (selection, intent box, Ask), the Ask panel on practice and feedback (after CA2), the tutor's answer, the teacher's lesson `visual`, and later MCP chat (C2) all send a `FigureRequestV1` to `figures/service.py`.

## 2. Goals and non-goals

**Goals**
- G-a. "Show me" from a question, a passage, or both, on every host that can render a figure, through one request contract and one service.
- G-b. Grounding: a question-only request cites the learner's own passages when retrieval finds them; otherwise it is built anyway and labelled *not from your books*.
- G-c. A sketch tier for what the grammar cannot express, with a stated threat model, a sealed runtime, headless verification of declared probes, honest element-scoped labels, reuse and repair.
- G-d. Exploration as formative evidence: figures as a help kind in attempts, in the hint chooser's sampled kinds, in RW2c's outcomes and in the diagnoser's trace, under the existing tiers (W1).
- G-e. Fit: kept figures resurface on corresponding sections of other books (C0a), and the teacher uses figures as manipulatives in discovery steps.

**Non-goals**
- N-a. "Matches the book's equation (checked)". That claim stays RW5c's, designed and reviewed before code (`spec_reader_workbench_v1.md` §8.3 amendment). Nothing in RW5d says a figure matches the book.
- N-b. Generated HTML, CSS or DOM. A sketch never touches the page; it returns data.
- N-c. Figures as certification, or any numeric update of a posterior from exploration (W1 tier 2; the numeric weak-observation row in §17 of the parent stays deferred).
- N-d. Learner-adaptive figure content. The figure author receives no learner state (§10.4 explains, and the teacher is the route for state).
- N-e. Turning a whole paper into an interactive system (the parent's §17 ambition). Sketches are bounded, one idea each.
- N-f. Phone rendering in v1, and MCP chat figures (C2 owns them; §13).
- N-g. The dropped MCP anti-cheating idea. Not designed here.

## 3. Standing constraints (binding)

The parent's W1–W14 hold. Restated where RW5d leans on them, with what each means here:

- **SM1 (W1, tiers).** Figure play, slider moves and opening a figure are tier 1 (engagement). Predictions, "what changed?" text and a figure's goal text are tier 2 (formative). Nothing a figure produces is tier 3. The only evidence an attempt produces is its submitted, blind-graded answer.
- **SM2 (W2, honest labels).** The badge slot is code-owned (`FIGURE_FRAME`, `apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx:27`). "Checked" appears only for what a non-LLM check ran, scoped to the element it covers. Every figure says *not checked against the book* until RW5c.
- **SM3 (W3, generous defaults).** Every RW5d phase ships on behind its own kill switch. No confirmation dialog guards a safe action. The sketch tier's safety comes from its runtime, not from a click (§9.6).
- **SM4 (W7 and D46, cold).** During a check on your own, no figure is shown or built unless the learner takes it as help, which converts the attempt (§11.3). The figure-only stimulus rule (`ux_reader_compare_ask_v1.md` §8.5, Q10) is a source crop, not an explorable, and is unchanged.
- **SM5 (W8, blind grading).** The grader never sees a figure, its spec, predictions or exploration.
- **SM6 (A8, exam material).** Exam and held-out material is never sent to the figure author, never retrieved for grounding, never shown in a figure; the existing one predicate (`exam_material(...)`, `spans_withheld`) is asked before any call and on every later delivery, as today (`service.py:219-258`).
- **SM7 (bitter lesson).** Which tier, which passages, what to draw and whether a figure should be offered as help are model judgments with receipts. No word list, no keyword routing.
- **SM8 (no made-up constants).** RW5d adds no weight, margin or threshold to the learner model. Its numbers are caps on money, time, memory or display, or numerical tolerances, each a labelled `keep` guardrail (§15).
- **SM9 (T1 plan-first).** Every route runs plan-first (`chatgpt_plan`). A pressed action that finds the plan down may offer OpenRouter (redesign D: the offer is the grant, keyed by the origin RPC method, `ai/plan_fallback.py:1-31`). Nothing builds in the background, and no figure is pre-built for an offer.
- **SM10 (W12, attention).** Nothing LearnLoop starts moves focus, animates on its own, or opens a modal or toast. A figure lands where its request was made.

## 4. Code truth (audited on `main` at `eae00d58a`)

### 4.1 The figure pipeline (RW5a, RW5b)

| What | Where | Notes |
|---|---|---|
| Package overview and the content-only promise | `figures/__init__.py:1-24` | "nothing here writes an attempt, evidence, mastery, certification, scheduling, FSRS or adaptive-difficulty state", enforced by the `evidence-never-reads-figures` import contract |
| The spec `InteractiveFigureSpecV1` (`ifs-v1`) and its caps | `figures/spec.py:48-99`, `:313-337` | ≤4 parameters, ≤4 panels, ≤3 predictions, `MAX_TEXT` 400, `MAX_LABEL` 80; RW5b's panels and work cap `MAX_PANEL_WORK` 250,000 at `:71-90` |
| The grammar: hand-written parser and evaluator, no `eval` | `figures/grammar.py:48-760` | adaptive Simpson `:566`, exact sums `:618`; TypeScript twin `apps/learnloop-tauri/src/screens/reader/figures/figureGrammar.ts`, kept identical by the golden corpora (`figureGoldenCorpus.json`, `figurePanelsCorpus.json`, `figurePropertyCorpus.json`; `tests/figure_corpus.py`, `tests/figure_panels_corpus.py`, `tests/figure_property_corpus.py`) |
| Verification, steps 1–2 | `figures/verify.py:96-461` | outcomes `illustrative`, `failed`, `unsupported` (`:48-53`); the parameter grid (`:96`); shaded-area cross-check (`:340`); claim quotes (`:398`); decidable predictions (`:415`). Step 3 is RW5c's |
| The author route `figure_author` | `figures/routes.py:40-308` | two attempts (`:45`); isolated tool-free turn, refused if the provider can't isolate (`:249-256`); daily envelope `figures.max_daily_cost_usd` at `figures.price_per_million` (`:179-184`); the author may answer `unsupported` with a kind and reason (`:52-60`, `:93-110`) |
| The request, its validation and the held-out refusal | `figures/service.py:126-134`, `:506-557` | `FigureRequest{extraction_id, span_ids, region, origin, supersedes_id, revision_note}`; origins `selection`, `library`, `tutor` (`:88-90`); **no goal text field**; empty spans refused (`:513-515`) |
| Source context sent to the author | `service.py:261-292` | the selection, two paragraphs each side (held-out ones left out), the crop when a figure block or region is selected |
| Reuse by input hash, one build per input | `service.py:470-503`, `:588-661`, `:663-686` | `content_key` over spec and prompt versions and everything sent; the unique reuse index in migration 216 |
| Admission gate (switch, route, cap, price re-read before every physical request) | `figure_admission.py:174` (`FiguresGate`) | a configuration change stops a build with nothing stored |
| Predictions and "what changed?" | `service.py:888-956` | code decides `matched`; a miss is queued as a `reader_formative` text for learner-text gaps (`diagnosis/text_gaps/jobs.py:163`, `:177`), only while `learner_text_gaps.enabled` and `reader_formative.enabled` |
| Offers (RW5b) | `learnloop_sidecar/handlers/figures.py:160-207`; `figure_admission.py:88`, `:132`; `tutor/ai_contracts.py:208-219`; `source_retrieval/library_ask.py:249-263` | the organizer and the Reader tutor judge `explorable: yes/no` in the call they already make; the press builds; code then allows only `equation`/`figure` blocks |
| RPCs, pinned desktop-only | `handlers/figures.py:48-56` | `reader.figure_request`, `_revise`, `_job`, `_job_cancel`, `reader.figures`, `_predict`, `_explain` |
| Tables | `migrations/216_interactive_figures.sql` | `interactive_figures` (WORKFLOW; `extraction_id NOT NULL`; `origin` CHECK of three values; `verification` CHECK of four), `figure_predictions` (RAW_LEDGER, append-only, explanation set once); roles at `db/table_roles.py:238`, `:285` |
| Switches and money | `config/schema.py:2511-2557` (`FiguresConfig`) | `enabled`, `predictions_enabled`, `region_enabled`, `revisions_enabled`, `advanced_panels_enabled`, `offers_enabled` (all default on), `max_daily_cost_usd` 1.0, `price_per_million` unset; classified at `params/parameter_registry.py:1253-1281` |
| T1 metered setting | `ai/plan_fallback.py:78` | `figure_author` → `figures.price_per_million`: OpenRouter is offered only once the price is set |
| The intent box action | `reader/reader_intent.py:181-186` | `make_explorable` ("make this explorable"); the learner's typed text is not passed to the figure |
| Frontend | `api/client.ts:1635`; `screens/reader/figures/useFigures.ts:180-182`; `FigureInline.tsx`; `FigurePanels.tsx` (SVG); `AdvancedPanels.tsx` | the request carries spans and region only; the frame lists the property checks code ran under *checked by LearnLoop:* (`FigureInline.tsx:27-45`) |
| The report | `reader/reader_report.py:809-815` | figures by verification and `unsupported_by_kind` (`learnloop reader report --json`) |

### 4.2 Animations (the other visual route)

`content/authoring/concept_animation.py` turns a concept into a Manim CE scene: model-written **Python**, checked by an AST allowlist (`:68-77`, `:156`), rendered by a local `manim` subprocess under bubblewrap on Linux (`:339-374`: every namespace unshared, read-only system mounts, the scratch dir the only writable path). Its own docstring says the allowlist "is NOT a sandbox" (`:9-20`), which is why the RPC demands a per-run consent tick (`learnloop_sidecar/handlers/animation.py:109-120`). Output is an mp4, not interactive. It is the precedent RW5d's sketch tier must improve on, not copy (§9.2).

### 4.3 Retrieval, help and evidence

- `find_sources` (`source_retrieval/find_sources.py:613`; intents `explain`, `remediate`, `alternative`, `worked_example`, `compare` at `:74`) and `find_sources_for_caller` (`:899`), with policy derived on the server from a `CallerContext` (`source_retrieval/policy.py:23`, `:78-93`; caller kinds include `reader`, `tutor`, `learner`; no `figure` or `teacher` yet). Exam material is withheld inside (`find_sources.py:753-756`).
- `help_assists` (`migrations/210_help_assists.sql:22-60`): `assist_kind` CHECK `hint, check, discriminate_answer, bridge, example, compare_methods, feedback`; `hint_kind` CHECK of twelve kinds. No figure kind.
- RW2c's `help_outcomes` (`workbench/help_outcomes.py:99`): `_HELP_KINDS = ("hint", "bridge", "example", "compare_methods")`. The parent spec's §5.10 says it reads "figure views"; **the code does not**, and there is no row that records a figure being used as help.
- The hint chooser's preconditions (`hints/options.py:99`: `worked_parallel` needs a worked example or another instance at hand) are the pattern a figure kind follows.
- `source_object_versions.object_type` already allows `artifact` (`migrations/094_source_objects.sql:27-29`).

### 4.4 The desktop webview

Tauri 2 (`apps/learnloop-tauri/src-tauri/Cargo.toml:15`), one capability for the `main` window (`capabilities/default.json`), two custom protocols (`llpdf`, `llmedia`; `src-tauri/src/main.rs:204-210`). The CSP (`tauri.conf.json:27`) already allows `script-src 'self' 'wasm-unsafe-eval'` and `worker-src 'self' blob:`, so a WebAssembly engine in a Worker needs no CSP change. The parent's §17 row worried about Tauri iframe isolation on Linux; the design below puts no model code in any frame (§9.3). The B3 Rust-toolchain blocker in that row appears fixed (`cargo check` passes in landing gates, e.g. `docs/reviews/ux-phase2.md:515`); P2's first task re-confirms it.

### 4.5 Corrections to the framing

Each of these refines the approved framing against the code:

1. **"Prediction answers and 'what changed?' go to the grader/diagnoser."** The grader, never (W8, SM5). The diagnoser only through an attempt's help trace, as RW2b's discriminating answers do (`spec_reader_workbench_v1.md` §5.4, `+workbench-v1`). Missed predictions already reach learner-text gaps, so outside attempts nothing new is needed (§11.1).
2. **"Passing → checked, else not checked."** A sketch whose own stated claim *fails* is demonstrably wrong, so showing it as "not checked" would mislead. RW5a's rule (fail steps 1–2 → not shown) is kept: a failed claim gets the second attempt, then the honest failure line. *Not checked* is for a sketch that states no checkable claim (§9.5).
3. **"Kept figures become source objects."** Every built figure is already persisted and tied to its spans. Surfacing it on corresponding sections needs a read through the figure's section, not a second store; mirroring into `source_objects` is Q8, recommended no.
4. **"Figure complexity keyed off the AD predicted level."** Not earned: it would put learner state in the author's prompt (today it has none, `routes.py:21-24`), break reuse by input hash across sessions, and duplicate the teacher, which already reads the latent state and can say what to hand over in the goal text (§10.4, Q9).
5. **"A model judgment chooses the tier."** Yes, and it is already there: the author's `unsupported` verdict is a model judgment with a receipt. RW5d widens that verdict to `spec | sketch | unsupported` in the same call (§8.4) instead of adding a routing call.

## 5. Principles

1. **One request contract, one service.** Hosts differ in where a figure lands and what the press costs, never in how a figure is built.
2. **The learner's words shape the figure; they never grade.** The goal text goes to the figure author, like "not right?" does today (UX §4.10).
3. **Books first, then honest abstention.** Grounded figures cite and quote; ungrounded ones say *not from your books* (RW1c's abstention pattern).
4. **Data, not code, crosses into the page.** Grammar figures are data; sketches compute in a sealed interpreter and return data. The trusted renderer draws both.
5. **Checks are scoped to what they checked.** A probe check names the element, the stated equation and the settings it covered.
6. **The grammar is preferred.** It is cheaper, verified more strongly, reusable and accessible by construction. A sketch must say why the grammar could not do it.
7. **Exploring is help, not evidence.** It counts as help where help counts, and its effect is measured later against cold outcomes.

## 6. The surfaces

States everywhere follow UX §4.0 (pending with a measured *about N s* only once the report has a p50, landed, failed with the request kept, model unreachable with T1's offer when pressed, sidecar down, capped naming the cap, switched off = absent).

### 6.1 The Reader: selection and the intent box (P1)

Today the intent box routes "make this explorable" and drops the words. RW5d keeps one action (`make_explorable`) and passes the text as the goal. The Decider's option text gains one clause ("the learner's words, if any, say what the figure should show or vary"), under a new `reader_intent` prompt version.

```
  §6.4 ¶2  ... the eigenvalues of a real 2×2 matrix are real or a conjugate pair ...
           ▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔ (selected)
  ┌───────────────────────────────────────────────────────────────┐
  │ show me this, but with complex eigenvalues▏                   │
  │ ↵ go · tab actions · esc                                      │
  └───────────────────────────────────────────────────────────────┘
  → Understand · show me · from your selection and your words · change
```

- The routed line says what will be used: *from your selection*, *from your selection and your words*. "change" opens the palette with the text kept, as today.
- The palette's entry reads **show me…** (was *make this explorable*); with an empty box it behaves exactly as today.
- The result lands where RW5a's does: one dim pending line under the passage, then the collapsed figure line inline under it (UX §4.7, S9). The collapsed line quotes the goal in the learner's voice:

```
  ▸ interactive version · › "but with complex eigenvalues" · AI-built illustration · not checked against the book
```

### 6.2 The Reader's Ask rail (P1)

The Ask tab's box gains a second way to send: **show me ▸** (`Alt+↵`), which sends the box's text as a figure goal instead of a question. It is shown only while `figures.show_me_enabled`; the key bar advertises it only then.

```
  ┌ Ask ───────────────────────────────────────────┐
  │ about › §6.4 (open) · this thread       ⓘ       │
  │ › why does the trajectory spiral?               │
  │ ◇ LearnLoop · helping you reason …              │
  │                                                 │
  │ ◐ building an interactive version from          │
  │   § Strang §6.4 ¶2 · § Axler §5.C · keep reading│
  │ ─────────────────────────────────────────────── │
  │ ask in your words▏                              │
  │ ↵ ask · alt+↵ show me ▸ · ⓘ where this goes     │
  └─────────────────────────────────────────────────┘
```

- **Where it lands.** The thread gets one line: *▸ interactive version · from your books: § Strang §6.4 ¶2 · open*. Opening it expands the figure **inline under the passage the learner was reading when they asked** (the inquiry's anchor, else the first visible block), at the text column's full measure, because the 360 px rail is too narrow (S9). The cited passages are `§` chips that peek, as RW1c's citations do. If the learner has scrolled away, *open* jumps there with a crumb (*back to where I was*, `reader_source_restored`); the learner pressed, so the jump is theirs.
- **Grounded or not.** With grounding (§8.3), the line says *from your books* and lists the passages. Without it: *not from your books — LearnLoop's model's illustration*, and the figure's badge carries the same words.
- **ⓘ where this goes** for show me: *"Sent with your selection or the passages LearnLoop finds to the model that builds the figure — never to grade you."*

### 6.3 The tutor's answer (P1)

RW5b's tutor already judges cited blocks explorable in the call it makes (`tutor/ai_contracts.py:208-219`). P1 adds one optional field to the same answer, `figure_goal` (≤ 160 characters, AI-written): when the tutor judges that an explorable would help *this question* even though no cited block is a ready equation, it writes the goal. Same call, no extra spend, under the tutor's next prompt version. The Reader renders it as a button under the answer (D28: the tutor requests, the learner presses):

```
  ◇ LearnLoop · helping you reason · from your books
  ┊ The trajectory spirals because the eigenvalues are a ± bi; the real
  ┊ part a decides whether it grows or shrinks …
  ┊ § Strang §6.4 p.312  § Axler §5.C
  ┊ ▸ show me: ◇ "vary a and b and watch the spiral open or close"
  ┊ ▸ make this explorable (§ Strang eq. 6.4.3)      ← RW5b, unchanged
```

Pressing it sends a `FigureRequestV1` with origin `tutor`, the goal as written (labelled AI-written in the figure's line), and the answer's cited spans as grounding. The press is the grant (SM9). Off (`figures.show_me_enabled = false` or `figures.offers_enabled = false`), the tutor's prompt and output are as before.

### 6.4 The Ask panel on practice, feedback and the workbench (P3, after CA2)

The CA2 panel (`ux_reader_compare_ask_v1.md` §7.1) gets the same *show me ▸*. What it costs depends on the host, and the box says so before sending, in the CA2 vocabulary:

| Host | The dim line under the box | What pressing it records |
|---|---|---|
| Feedback (after Submit) | *show me is free here* | Nothing on the attempt |
| Practice answer box, Work in Steps, the Reader workbench (an open attempt) | *a figure on this counts as a hint* | One hint-equivalent and a `help_assists` row (§11.2) |
| A check on your own | *a figure on this makes this practice with help ◌* | The take step converts the attempt first, then builds (§11.3) |

Where it lands: in the docked panel's thread at panel width with *widen ↔* (the panel is resizable, CA2), or under the focused step in the workbench, where a hint lands (CA2 §7.6). No figure is ever built from the item's own exercise, solution or answer-overlapping passages: the caller's policy is `assisted_practice` (§8.3).

```
  ┌ Ask · about › Exercise 6.1.12 · your draft ──────── help style: balanced ▾ ┐
  │ › show me what changes when the off-diagonal entry goes negative           │
  │ ▸ interactive version · from your books: § Strang §6.1 ¶5 · counts as a hint│
  │   [ expanded figure at panel width · widen ↔ ]                              │
  │ ─────────────────────────────────────────────────────────────────────────── │
  │ ask in your words▏                                                          │
  │ ↵ ask · alt+↵ show me ▸ · a figure on this counts as a hint                 │
  └─────────────────────────────────────────────────────────────────────────────┘
```

### 6.5 A teacher lesson step (P4, built with TE1)

`TeacherTurnV1.message.visual` (`spec_teacher_v1.md` §8.2) is a `FigureRequestV1` with origin `teacher`: a goal the teacher writes from the latent state (which parameter to hand over, which to hold fixed), anchored to the lesson's sections. The figure renders in the turn, and the teacher's own `prediction` or `check` refers to it:

```
  ◇ teacher · step 3 of your plan
  ┊ You've seen that real eigenvalues give straight-line solutions. Here only the
  ┊ imaginary part is yours to move; the real part is fixed at −0.2.
  ┊ ┌ interactive version · AI-built illustration · not checked against the book ┐
  ┊ │  b ──────●──────────  0.80          [ phase portrait, one trajectory ]     │
  ┊ │  ▸ play b                                                                  │
  ┊ └────────────────────────────────────────────────────────────────────────────┘
  ┊ Drag b until the trajectory stops spiralling. What did you have to do?
  ┊ your answer▏                                         (a lesson check · collapsed until you've explored)
```

- **The figure's own predictions are suppressed in a lesson** (`context.host = lesson`): the teacher poses the prediction or check, so the learner never gets two prompts for one move.
- **The answer is lesson-check evidence** when the teacher poses it as a check (`pose_check`): a minted held item, `reconstruction_after_walkthrough`, blind-graded against the committed solution, entering mastery with the learned mass `m` (`spec_teacher_v1.md` §12, §12.1). As a prediction it is a `lesson_turns` row, formative. The grader sees the question text, never the figure (SM5); the committed solution is written knowing what the figure does.
- The lesson's opening is the press: the visual builds with the turn (the turn is waiting on it anyway). If the plan is down, the T1 offer is keyed by the lesson's RPC method (§12.3).

### 6.6 The sketch tier on any host (P2)

A sketch renders in the same frame and slot as a grammar figure. Only the badge and the checks list differ:

```
  ▾ interactive version · AI-written simulation · sandboxed · not checked against the book   ⓘ
    ◇ shows: a random walk's spread grows like √n                                      (AI-written)
    ◇ assumes: steps of ±1 with equal probability                                       (AI-written)
    n  ───●────────────── 200      walkers ──●──────── 400      ▸ play   ↻ new sample
    [ display list: 400 paths, a ±√n envelope, a histogram of positions at n ]
    checked by LearnLoop:
      · the envelope is √n at 27 tested settings
      · the histogram's spread agrees with √n within sampling error at 27 settings
      · not covered: the individual paths (drawn, not checked)
    t values as a table · not right?
```

- **ⓘ how this runs:** *"Written by LearnLoop's model as a small program. It runs in a sealed sandbox inside LearnLoop: it can't see your files, your notes, the network or the rest of the app — it only computes what's drawn here."* (The glass box, on demand; no jargon in the badge.)
- **States specific to sketches:** *paused — this simulation is too slow here · step ▸* (the frame watchdog, §9.4), and *this simulation hit an error at these settings · not right? (prefilled)*. Neither moves focus.
- Reduced motion: *play* becomes step buttons, as D39 requires; nothing moves until pressed.

### 6.7 The phone page (none in v1)

Figures stay desktop-only (`handlers/figures.py:48-56`). A view-only grammar figure on the phone is a later mobile item (§16, trigger). The sketch engine is portable (WebAssembly in Safari), so the phone would need only an allowlisted read RPC, an owner decision as in CA7.

## 7. The request contract

### 7.1 `FigureRequestV1`

```text
FigureRequestV1
  goal_text        text | null         # the learner's words, or a tutor/teacher goal (author recorded); ≤ 600 chars
  goal_author      learner | tutor | teacher
  anchor           {extraction_id, span_ids[≤40], region?: {span_id, bbox}} | null   # today's request, unchanged
  origin           selection | library | tutor            # RW5a/b, unchanged
                 | show_me                                 # Reader intent box or Ask rail with words
                 | ask                                     # the CA2 Ask panel on practice, feedback, workbench
                 | teacher                                 # a lesson's visual (TE1)
                 # chat (C2) is reserved, added by C2's own migration
  host_ref         {question_event_id? | item_id + submission_id? | workbench_session_id?
                    | attempt_id (feedback)? | lesson_id + node_id?}   # references only; each verified on the server
  reading_at       {extraction_id, span_id} | null         # where the learner was (the home when there is no anchor)
  offer_ref        text | null                             # RW5b's, and the tutor answer for a tutor goal
  supersedes_id, revision_note                             # "not right?", unchanged
```

**Validation.** At least one of `goal_text` and `anchor`. A goal alone needs `figures.show_me_enabled`. `goal_author` is never taken from the client: `learner` for the box, `tutor` only when `offer_ref` names a stored tutor answer whose `figure_goal` equals the text (read from the stored output, as `offered_spans` does today, `handlers/figures.py:160-207`), `teacher` only from the lesson service. Every `host_ref` is resolved on the server into a `CallerContext` (`source_retrieval/policy.py:38`); a client never states its policy.

**The RPC.** One method for every host, `figure.request(FigureRequestV1)`, answering at once with a build job (read with `reader.figure_job`, cancel with `reader.figure_job_cancel`, as today). `reader.figure_request` stays as a thin wrapper for anchor-only requests so RW5a/b's callers and tests are unchanged. Both are pinned desktop-only. Because redesign D's grant is keyed by the origin RPC method, `figure.request` is one grantable action whatever the host.

### 7.2 What the server derives

| Derived | From | Rule |
|---|---|---|
| Caller and policy | `host_ref`, via `derive_policy` | Reader reading, Ask rail, feedback: `reading` or `post_attempt`. An open attempt: `assisted_practice` for that item. A cold administration: `cold_attempt`, refused unless the request carries the take-step token from the converted attempt (§11.3). A lesson: `reading` under caller kind `teacher` (added by TE1, `spec_teacher_v1.md` §9.1) |
| Caller kind | origin | `reader` for selection/show_me/library; `tutor` for tutor; `learner` for ask; `teacher` for teacher. `figure` is not a new caller kind: the figure service calls `find_sources_for_caller` on the requester's behalf |
| Home | anchor, else `reading_at`, else the host | Where the figure lists and expands (§6.2). A practice-host figure with no reading position has no extraction (§14.1) |
| Grounding | §8.3 | `anchor` (the anchor is the source), `retrieved`, or `none` |
| Predictions on | host | Off in a lesson (§6.5); otherwise `figures.predictions_enabled` |

## 8. Building a figure from a request

### 8.1 The pipeline

```
FigureRequestV1 ─► validate, derive caller/policy, refuse held-out (SM6)
               ─► grounding: anchor context (today's source_context)  |  find_sources (§8.3)
               ─► reuse? input hash over everything the author is sent (+ goal, + grounding, + tier versions)
               ─► author (figure_author, ≤ 2 attempts): status spec | sketch | unsupported
                     spec   ─► parse_spec ─► verify_numerics (RW5a/b, unchanged)
                     sketch ─► sketch verification (§9.5)
               ─► store row + judgment_ledger verdicts (figure_verified; figure_tier)
               ─► deliver to the host's landing place
```

Everything after grounding is RW5a/b's code path with two additions: the goal and grounding enter the author's context and the hash, and the author may answer `sketch` when the sketch tier is on.

### 8.2 What the author is sent

RW5a's payload (`service.py:566-585`) plus:
- `learner_request`: the goal text with its author (`learner`, `tutor`, `teacher`), labelled as data, never instructions (the existing injection sentence in `AUTHOR_INSTRUCTIONS`, `routes.py:93-110`, extends to it);
- `passages` from grounding when there is no anchor, each with its `(extraction_id, span_id)` key, so quotes are verified against the right block;
- `grounding: none` when nothing was found, with the instruction to build an illustration that quotes nothing.

**Privacy changes, disclosed.** Today the author receives no learner data except a "not right?" note (`routes.py:21-24`). The goal text is learner-written and now reaches the author route (`ai/disclosures.py:37`'s `figure_author` row gains "your request in your words"). No other learner data is sent: no history, no state, no attempt text, no item stem unless the learner typed it.

### 8.3 Grounding a question

When `anchor` is null:
1. `find_sources_for_caller(query=goal_text, caller=<derived>, intent="explain", verify=True, limit=GROUNDING_PASSAGES)`, with `reading_at`'s section as retrieval context. This is the sources service's existing verified retrieval; its policy layer withholds exam material (`find_sources.py:753-756`) and, under `assisted_practice`, the item's own blocks and answer-overlapping passages. Its manifest is stored on the request row.
2. The verified hits, at most `GROUNDING_PASSAGES` (3, `keep`: prompt size) blocks across any of the learner's sources, become the author's passages, each with its two neighbours as today.
3. **No verified hit:** the request is built with `grounding = none`. The figure's kind is forced `illustrative`, it may quote nothing (any `source_claims` are dropped by the existing quote check, `verify.py:398`), and its badge reads *AI-built illustration · not from your books*. This mirrors RW1c's abstention: helpful and honest, never pretending.
4. Each kept span is rechecked with `spans_withheld` before the author call and on every later delivery (`_figure_spans`, extended to span keys across extractions, §14.1).

**Joint requests** (anchor and goal) use the anchor's context exactly as today and add the goal. They are not retrieved for: the learner chose the passage.

### 8.4 The tier choice

With `figures.sketch_enabled`, the author's output contract widens (a new prompt version, so RW5a/b's reuse keys are unchanged while the sketch tier is off, the RW5b pattern at `routes.py:112-160`):

```text
FigureAuthorOutputV2
  status            spec | sketch | unsupported
  spec_json         InteractiveFigureSpecV1 as JSON text            (status spec)
  sketch_json       SketchProgramV1 as JSON text                    (status sketch)
  why_not_spec      one sentence: what the grammar can't express    (status sketch; required)
  unsupported_kind, unsupported_reason                              (status unsupported)
```

- **The instruction prefers the grammar:** "If the declarative spec can express it, write the spec. Write a sketch only for what it cannot express (a random process, a simulation with state, a geometric construction, a discrete structure), and say why in `why_not_spec`."
- **The receipt.** The author's status is the tier judgment. Each build appends a `judgment_ledger` row (task `figure_tier`, judge `llm`, verdict `spec | sketch | unsupported`, rationale `why_not_spec` or the unsupported reason, the model and prompt version), beside today's `figure_verified` row. The report shows the tier mix and the `why_not_spec` reasons by kind, so grammar erosion is visible (R3).
- **No second call to decide.** A separate Decider pre-call would add latency and a route for a decision the author is better placed to make (it is the one that knows whether its spec can express the idea). Q1.
- Off, the output contract is RW5b's byte for byte, and `unsupported` keeps meaning "can't draw this yet".

### 8.5 Reuse, versions and repair

- **Reuse key.** `request_hash` (`service.py:473-485`) gains `goal_text` (whitespace-normalized, case kept), `goal_author`, the grounding keys and texts, and the tier versions (`sketch-v1`, the engine digest, §9.3). Origin stays out of the key (`REUSE_ORIGIN`, `:470`), so the same input from the Reader and from a tutor offer is built once.
- **Engine upgrades.** A stored sketch records the engine digest it was verified under. A later engine re-runs the stored sketch's verification (code only, no model call) before showing it; one that now fails shows *couldn't run under this version · rebuild* and is never shown as checked.
- **"Not right?"** works on both tiers unchanged: the note and the earlier spec or program go to the author for a new version that supersedes the old (kept). A runtime error the learner hit prefills the note with the code-written error and the parameter values.

## 9. The sketch tier

### 9.1 What a sketch is

```text
SketchProgramV1
  program_version   "sketch-v1"
  demonstrates      text                                   # as ifs-v1; AI-written, labelled
  assumptions       [{text, span_key?, quote?}]            # quote-verified where quoted
  source_claims     [{span_key, quote}]                    # quote-verified; none when grounding = none
  parameters        [{name, label, min, max, step, default, animate?}]     # ifs-v1's Parameter model, ≤ 4
  clock             {dt, t_max} | null                     # a stateful simulation's fixed step, driven by the host
  seeded            bool                                   # uses rand(); "↻ new sample" appears
  code              JavaScript text, ≤ SKETCH_MAX_SOURCE_BYTES, defining:
                      init(p, seed)            -> state
                      step(state, p, dt)       -> state           # only with a clock
                      view(state, p)           -> Scene
                      probes(state, p)         -> {name: number | number[]}
  probes            [{name, label, shape: scalar | series | pairs}]          # declared; the values table
  claims            [Claim]                                # what code will check (§9.5)
  bindings          [{element_id, probe}]                  # drawn elements that ARE a probe's values
  predictions       [{prompt, change: {param: value} | {run_to: t}, observe: {kind: direction | choice, probe}}]
  annotations       [{target, text}]

Scene  (the display list; every coordinate in data units, every number finite)
  viewport   {x: [min, max], y: [min, max]}, axes?: {x_label, y_label}
  elements   [ polyline | polygon | points | segment | arrow | circle | rect | text | heat_cells
             | handle {id, x, y, binds: {x?: param, y?: param}} ]
             each with an optional id and a style from a closed palette (series0–3, muted, accent; dash; width ≤ 3)
```

- **No HTML, CSS, URLs or images.** The renderer draws elements as SVG primitives (as `FigurePanels.tsx` does) and text as text nodes, never markup. Text elements are capped at `MAX_LABEL` and render inside the frame in the model voice.
- **Interaction is the host's.** Sliders and numeric fields come from `parameters` (trusted controls); a `handle` is a draggable point bound to one or two parameters within their ranges; *play* advances the host's clock; *↻ new sample* changes the seed. The sketch never receives pointer events, timers or keys.
- **Determinism.** The only source of randomness is the host's `rand()` (a seeded PRNG); `Date` and `Math.random` are absent. The same parameters, seed and step count give the same scene, bit for bit, on every host.
- **Accessibility.** The *values as a table* toggle (`t`) shows the declared probes at the current state, so every sketch has the data-table equivalent RW5a requires.

### 9.2 Engine choice: JavaScript in a sealed interpreter

| Option | For | Against | Verdict |
|---|---|---|---|
| **A. JS in QuickJS(-ng) compiled to WebAssembly, no imports, in a Worker; the same `.wasm` bytes in the sidecar under `wasmtime`** | The program can reach nothing: the interpreter has no host bindings beyond returning values, and wasm memory is isolated from the webview's realm. The same bytes run in the desktop and the verifier, so verified values equal drawn values exactly (one implementation, unlike the grammar's twin evaluators). ~1 MB. Starts in milliseconds. Fuel metering gives deterministic work caps. Runs in Safari for a later phone. Models write JS well | Interpreted: roughly tens of times slower than a JIT. One new Python dependency (`wasmtime`) and one tracked engine binary | **Chosen** |
| B. Pyodide (CPython in wasm) with numpy | Models write numerical Python best; numpy | ~10 MB core plus ~8 MB numpy; seconds to start; the sidecar would still need its own sealed runner; a heavier phone story | Rejected for v1; revisit if sketches hit the work cap often (§16) |
| C. Model JS in a sandboxed iframe (`sandbox="allow-scripts"`, opaque origin, own CSP), JIT speed | Fast; DOM drawing | The model's code becomes a JS realm inside the app's webview: the boundary is the webview's iframe and IPC isolation, which Tauri itself warns about on Linux, and every DOM API is attack surface. Headless verification would need a browser in the sidecar. Drawn ≠ verified | Rejected |
| D. Python under bubblewrap (the manim pattern) | Exists | Not a sandbox off Linux, needs a consent click (`handlers/animation.py:109-120`), a subprocess per frame is not interactive | Rejected |

**Why the speed is enough.** One frame's budget (`SKETCH_FRAME_MS`, 16 ms, `keep`) under an interpreter covers on the order of hundreds of thousands of simple operations: hundreds of walkers, a 64×64 cellular automaton, a 16×16 attention matrix, a few thousand Monte Carlo samples per frame. Larger ideas are summarized (a histogram, not every path) or are out of scope (N-e). The report counts watchdog pauses (§16 trigger for option B).

### 9.3 The runtime

**In the desktop.** A dedicated Web Worker (no DOM, terminable) instantiates the engine from the tracked `.wasm` (hash-pinned) with **no imports except a deny-all WASI shim** (no files, clock, randomness, environment or network; `fd_write` captures error text only). The host loads the sketch's `code`, calls `init`/`step`/`view`/`probes` with plain JSON values and receives plain JSON back, validated against the `Scene` and probe schemas before anything is drawn. Caps (`keep`): memory `SKETCH_MEMORY_BYTES` (64 MiB), per-call work through QuickJS's interrupt handler, and a wall-clock watchdog that terminates the worker past `SKETCH_FRAME_MS × SKETCH_WATCHDOG_FRAMES` and shows the *paused* state.

**In the sidecar (verification and predictions).** The same `.wasm` under `wasmtime` with no imports beyond the same deny-all shim, a fuel limit per call (`SKETCH_FUEL_PER_CALL`), a memory limit (`Store` limits) and an epoch deadline. In-process: wasm's memory safety is the boundary, so no subprocess or bubblewrap is needed. Prediction outcomes are computed here, by code, as `S.prediction_outcome` does for grammar figures (`spec.py:1067`).

**Packaging.** The engine is built reproducibly from a pinned QuickJS-ng release by a checked-in script, and the artifact is tracked under `apps/learnloop-tauri/` assets, which the public-tip guard allows (G8); the sidecar loads the same file by path and refuses a digest mismatch. Q2.

### 9.4 Threat model (proportionate, stated honestly)

The adversary is the author's output: a model that may follow injected text in a book or paper, or simply write a bad program. The learner is not the adversary.

| Asset | Harm | Path | Control | Residual |
|---|---|---|---|---|
| The vault, notes, learner data | Read or tamper | Sketch code reaching IPC, the filesystem or the sidecar | The interpreter has no bindings; the Worker has no DOM; the sidecar's wasm has no imports. **Gate G-SM14:** a request from inside the Worker to the IPC endpoint is refused; if Tauri does not refuse it, the Worker moves into an opaque-origin frame before P2 ships | Needs a WebAssembly-engine escape in WebKit or wasmtime, then a payload aimed at LearnLoop's IPC. Not realistic for model output (proportionate bar) |
| API keys, plan token | Exfiltrate | Network from the sketch; network from what it draws | No network capability inside; the Scene has no URLs, images or markup, so drawing it fetches nothing; the sketch is never given secrets or learner data, only parameters | None found |
| Money | Spend | A sketch triggering model calls | It can't call anything. Builds are pressed, capped (two attempts, `figures.max_daily_cost_usd`), plan-first | — |
| The learner's trust | A misleading figure presented as checked | A sketch that draws something other than what its claims cover; a tautological claim; a sketch contradicting its own claim | Code-owned badge; checks listed per element; bindings verified (drawn element = probe); a failed claim is not shown (§4.5 item 2); every sketch says *not checked against the book*; the *not covered* line names unbound elements | A correct-by-its-own-claims sketch of a wrong idea. Same as any AI explanation; labelled AI-written; "not right?" |
| UI integrity | Fake LearnLoop UI (a "sign in" panel) | Text and shapes inside the frame | No inputs, links or markup can be drawn; text is capped, inside the frame, in the model voice; the badge slot is code-owned (SM2) | A misleading sentence inside a labelled AI frame |
| The machine | Hang, memory blow-up, UI freeze | Infinite loops, huge allocations, huge scenes | Fuel, memory and scene caps (`SKETCH_MAX_ELEMENTS`); Worker off the UI thread; watchdog terminate | A paused sketch |
| The supply chain | A tampered engine | The `.wasm` | Pinned digest, reproducible build script, refused on mismatch | — |

**Review.** The sandbox gets its own adversarial review before P2 merges (Codex, or Opus when Codex is out), against a **hostile-sketch corpus**: IPC attempts, `fetch`/`XMLHttpRequest`/`import()` probing, prototype-pollution attempts on the host's returned objects, oversized scenes, infinite loops in each entry point, NaN and Infinity everywhere, deep recursion, giant strings, text that imitates LearnLoop's badges, and claims written to be tautological. The reviewer is asked: "find a way for a sketch to reach anything but its return value, or to make the frame claim a check that didn't run."

### 9.5 Headless verification

Run in the sidecar after parsing, before anything is stored as shown. Steps 1–4 decide whether a sketch is shown at all; step 5 decides what it may claim.

1. **Structure.** The JSON validates; the code parses in the engine; the four entry points exist; parameters validate as `ifs-v1`'s do; probes and bindings name declared things; size caps hold.
2. **Runs everywhere it can be moved.** On RW5a's parameter grid (`verify.parameter_grid`, `verify.py:96`: three points per parameter, at most 81 combinations) and, with a clock, at `SKETCH_TIME_SAMPLES` points from 0 to `t_max`: every call returns within fuel, every probe is finite, every scene validates and is within caps.
3. **Deterministic.** Two runs with the same seed give identical probes and scenes (catches reliance on anything the shim refuses).
4. **Bindings hold.** At every grid point, each bound element's coordinates equal its probe's values (the same run produced both, so equality is exact). This is what lets a check speak for a drawn element.
5. **Claims.** Each claim is written in the existing grammar (`figures/grammar.py`) and evaluated by the existing Python evaluator, the oracle, at the same points:

| Claim kind | Says | Code checks | Tolerance |
|---|---|---|---|
| `equals` | a probe (scalar or series over a declared index variable) equals an expression of the parameters | the evaluator's value at each point | `CLAIM_REL_TOL` (1e-9 relative, the golden corpus's; numerical `keep`) |
| `follows` | a probed path follows the system `dx/dt = f, dy/dt = g` | integrate the claimed system with the grammar's RK4 (RW5b's `trajectory_2d`, `spec.py:954-1025`) at the sketch's step and at half the step; the tolerance is the difference between those two runs (a Richardson estimate of the integration error), times `ODE_SAFETY` | derived, with `ODE_SAFETY` (4, `keep`) |
| `invariant` | `finite`, `bounded`, `nonnegative`, `sums_to_one`, `monotone_nondecreasing` over a probe | as `verify.check_invariant` (`verify.py:251`) | RW5a's |
| `distribution` | a seeded Monte Carlo probe estimates an expression (a mean, a variance, a probability) | the sketch must also probe its sample size and sample variance; the check is the estimate within z·SE of the expression, with z from `MC_FALSE_ALARM` | `MC_FALSE_ALARM` (1e-6 per check, `keep`: strictness of a guard, not a learner-model number) |

**Outcomes.**
- Steps 1–4 fail, or any claim fails after the second attempt: **failed**, not shown (*couldn't build a reliable version of this*, with the reason), as RW5a.
- All pass and at least one claim covers a bound element: shown, `verification = illustrative`, with the passing checks listed under *checked by LearnLoop:* as RW5a lists its property checks (`FigureInline.tsx:27-45`), each naming the element, the stated equation (rendered from the claim's expression by code, marked AI-stated) and how many settings were tested. Unbound drawn elements are named in a *not covered* line.
- All pass and no claim is stated: shown as *AI-written simulation · nothing in it checked*.
- **Never** "matches the book". A claim's equation may be quoted from the source and quote-verified, but equality with the book's equation is RW5c's question (N-a).

These per-element lines are property checks of the kind RW5a already ships, not RW5c's book claim, so P2 does not wait for RW5c. Their wording rules (a schema walk over every model-written label so none can impersonate a check) go through the same adversarial review as the sandbox.

### 9.6 Why no consent click

The manim route asks for consent because its own boundary "is NOT a sandbox" (`concept_animation.py:9-20`). The sketch tier's boundary is a sealed interpreter with nothing to reach (§9.3–9.4). A click would protect nothing the runtime doesn't, and W3 forbids confirmation dialogs on safe actions. The frame says how the sketch runs, on demand (ⓘ). Q3.

## 10. Fit with the rest of LearnLoop

### 10.1 The Reader is the surface

Figures land inline under their passage (or under the passage the learner was reading), one expanded at a time, at the text column's measure (UX §4.7, S9). A built figure leaves the learner's own `◇▸` margin mark, outside the cue budget (UX §4.4, S8), because the learner asked for it.

### 10.2 Figures follow the section (P4, after C0a)

A figure is anchored to spans, so it has a section (`extraction_sections`). When the learner reads a section in another book that `reader.correspondents` (C0a; `spec_deliverable_curriculum_v1.md` §6.4) says corresponds to it, the Guide's *also in your books* entry (CA5) can list *an interactive version from Strang §6.4 ▸*. This is a read: figures joined through their anchor's section to the correspondents' sections, filtered by `figure_withheld` (`service.py:246`). Nothing is copied. Opening it shows the figure in place with its home named (*from your reading of Strang §6.4*). Q8 asks whether kept figures should also be `source_objects` (`artifact`) rows; recommended no.

### 10.3 The tutor requests, the learner presses

D28 holds: the tutor's `figure_goal` (§6.3) is a request; the press builds. The tutor never builds, and nothing is pre-built for an offer (SM9).

### 10.4 The teacher uses figures as manipulatives (P4, with TE1)

- **Doctrine.** The row "Instruments over description" (`spec_teacher_v1.md` §2.1) becomes concrete: in a discovery step (principle ii, motivated discovery), the teacher hands the learner one parameter and asks what they had to do (§6.5).
- **The latent state picks the parameter, in the goal.** The teacher reads the brief (AD readiness, misconceptions, last lessons) and writes the goal: which parameter to hand over, which to fix, what to watch. The figure author never sees learner state; the teacher's words carry what it decided. This keeps figures reusable content and keeps state where it is already governed.
- **Evidence.** Predictions are `lesson_turns` (formative). A posed check is lesson-check evidence with the learned weight (§12.1 of the teacher spec). The figure's own predictions are off in lessons.
- **Adaptive difficulty.** No figure-level coupling (§4.5 item 4). If TE1's receipts later show that lessons with manipulatives resolve delayed checks differently, that belongs in the teacher's own measurement (its §21), not in the figure service.

### 10.5 MCP chat (C2)

C2 owns chat figures. Its spec already lets hosts generate their own visuals (`spec_mcp_frontend_v1.md` §9.2) and routes reproducible ones through RW5 (§9.3). RW5d's contribution is the contract: a C2 `show_me` tool sends `FigureRequestV1` with origin `chat` (C2's own migration adds the value) and returns the spec or the sketch program with its verification report for an instrumented MCP App component. §9.3's sentence "never execute arbitrary model code in the learning service" is read as allowing the sealed verifier, which executes no host-language code and imports nothing; Q13 asks the owner to confirm, with a one-line amendment to that spec.

## 11. Exploration as evidence: the contracts

### 11.1 Outside attempts (reading, Ask rail, feedback, lessons)

Unchanged and already right: figure play is tier 1; a prediction is a `figure_predictions` row; a missed prediction and its "what changed?" are a `reader_formative` text for learner-text gaps (`service.py:888-956`); RW6a's recap lists misses. Show-me figures inherit this. **Goal text is not read for gaps** (it is a request to build, like "not right?"; Q6). Nothing outside an attempt reaches the diagnoser or any posterior.

### 11.2 Inside an open attempt (P3)

An open attempt is the practice answer box, Work in Steps, the Reader workbench session and guided redo.

| Event | Record | Evidence meaning |
|---|---|---|
| A figure built or opened on the attempt's host (show me, or the chooser's figure kind) | A `help_assists` row: `assist_kind = 'figure'`, the figure id, the host's `submission_id` or `workbench_session_id`, and the chooser fields when the chooser offered it | **One hint-equivalent** (`hints_used` += 1) folded at Submit as hints are (`spec_adaptive_hints_v1.md` §5), once per figure per attempt. Opening the same figure again adds nothing |
| The figure's text overlapping the item's key | The existing reveal kind `tutor_answer` with basis `figure:<id>`, over the figure's text (demonstrates, assumptions, labels, annotations, readouts at their defaults as formatted) through the existing overlap check | Reveal-aware rules as today |
| A prediction, a "what changed?" | `figure_predictions` as today, linked to the assist row | Tier 2. Enters the attempt's diagnoser trace (below), never the grader |

**Why a hint-equivalent and not "primed".** Primed means part of the solution was written for the learner (levels 4–5). A figure explores the idea; the item's own blocks and answer-overlapping passages are never its source (policy `assisted_practice`), and an overlap still writes a reveal. One hint-equivalent is the existing field with its existing meaning, the same mapping CA2 made for rereading an earlier thread (`ux_reader_compare_ask_v1.md` §7.3).

**The diagnoser's trace.** When an attempt used a figure, the split diagnoser's context gains the figure's goal, what it demonstrates, the prediction with its observed answer and the "what changed?" text, under a prompt-version suffix `+figures-v1` used only when such a trace exists (the `+workbench-v1` precedent, `spec_reader_workbench_v1.md` §5.4). Every other attempt's context hashes as before.

### 11.3 A check on your own

- Existing figures under the passage are hidden during a cold administration; the figure-only stimulus crop (CA1, Q10) is unchanged and is not an explorable.
- *show me* stays reachable (U11): its line reads *a figure on this makes this practice with help ◌*. Sending it is the take step: the attempt converts (one hint-equivalent, as above, banner *Practice with help ◌ — you asked for a figure*), and only then is the request built, under `assisted_practice`. The take step issues a token the request carries, so a cold policy is never bypassed by a crafted request.
- The chooser never offers the figure kind on a cold check, as it offers no hint there unasked.

### 11.4 Figures as a help kind (P3)

- **A chooser kind.** `explore_figure` at level 2 (label *a figure to explore*) joins the hint chooser's options (`spec_adaptive_hints_v1.md` §4.5) **only when a shown figure already exists** whose anchor section treats the item's LOs, that is not built from the item's own blocks, and that is not withheld now. The precondition is the `worked_parallel` pattern (`hints/options.py:99`). No figure is built for a hint: it costs no wait and no spend, and figures the learner built while reading become help later.
- **Sampled with a propensity.** The Decider gives the kind a probability like any other; the service samples and logs the propensity (§4.5 and §6.2 there). A served figure kind lands where a hint lands, as one line that opens the figure, and is recorded as above. This is the "randomized help-kind draw" the framing asked for, and it withholds nothing (the parent §17's rule).
- **Outcomes.** RW2c's `help_outcomes` adds `figure` to `_HELP_KINDS` (`workbench/help_outcomes.py:99`) and derives continuation, the attempt's grade and the later independent outcome from the assist rows, as for bridges. The hints report shows the kind with its sample size and interval, and its off-policy estimate once supported (`spec_adaptive_hints_v1.md` §6.3). This is the data the parent's deferred row "a learned, causal model of which help works for this learner" waits for; RW5d does not fit it.
- **Reader-side draw.** RW2c's passage draw (`workbench.passage_draw_enabled`) may include a kept figure among its judged options for a bridge, with its propensity, once the figure kind exists. Owned by RW2c's switch.

### 11.5 What never happens

No figure event writes `grading_evidence`, `facet_recall_state`, `facet_capability_evidence`, `probe_observations`, a certification, FSRS or AD state. The `evidence-never-reads-figures` import contract (`figures/__init__.py:21-23`) stays; P3's hint-equivalent fold goes through the hint service's existing submit fold, which already writes `hints_used` and does not import `learnloop.figures`.

## 12. Routes, spend, privacy

### 12.1 Routes

| Route | Use | New? |
|---|---|---|
| `figure_author` | Both tiers; grammar and sketch prompts are separate prompt versions | No (wider output contract, P2) |
| `source_rerank` and T6's rewrite/embedding routes | Grounding through `find_sources(verify=True)` | No |
| The Reader tutor's route | `figure_goal` in the answer it already writes | No (a field, P1) |
| `hint_chooser` | The `explore_figure` option | No (an option, P3) |
| The teacher's route | `visual` requests | TE1's |

### 12.2 Caps (money and time)

- Two author attempts per request, one physical request each, as today. `figures.max_daily_cost_usd` (1.0) covers both tiers on a metered route; a sketch's larger output is metered like any other. The call cap per request (`MAX_AUTHOR_ATTEMPTS`) and the token cap (`SpendCaps.max_total_tokens`, `routes.py:257-258`) are unchanged.
- Grounding uses the sources service's own caps.
- Sketch runtime caps are `keep` guardrails (§15).

### 12.3 T1

All routes plan-first. A pressed `figure.request` that meets a plan-down route gets UX §4.0's line, *ChatGPT plan isn't answering right now · use OpenRouter for this figure? ▸*, keyed by `figure.request`; for a lesson, by the lesson's turn method. OpenRouter is offered only once `figures.price_per_million` is set (`plan_fallback.py:78`). Background work: none (no prefetch, no pre-build for offers, no rebuild on engine upgrade beyond code-only re-verification).

### 12.4 Privacy

Sent to the author: source text (the anchor and neighbours, or retrieved passages), the crop when a figure or region is selected, the goal text and who wrote it, and for "not right?" the earlier version and the note. Never: learner history, state, attempts, the item's stem, key or rubric. The disclosure row for `figure_author` gains the goal text. Nothing leaves the machine from a sketch's runtime.

## 13. Data model

### 13.1 One migration in P1 (next free number at landing; 223 expected)

Main's head is 220; LP claim fixes hold 221 and C0a 222. Allocate at implementation time (`ls migrations/` on main and on the in-flight branches). Following RW1a's precedent ("one migration and no later rebuild", parent §4.3), P1's migration carries the columns P2 needs on these tables, so the sketch tier needs no rebuild.

**`figure_requests`** (new, RAW_LEDGER: what was asked, append-only; `figure_id` set once by trigger, as `figure_predictions.explanation_text`):

| Column | Contents |
|---|---|
| `id` | `frq_` + ULID |
| `origin` | `selection`, `library`, `tutor`, `show_me`, `ask`, `teacher` |
| `goal_text`, `goal_author` | The words and who wrote them (`learner`, `tutor`, `teacher`); NULL for anchor-only |
| `anchor_json`, `reading_at_json` | As sent, normalized |
| `host_ref_json` | The verified references (§7.1) |
| `policy`, `caller_kind` | As derived, with `policy_derived_from` |
| `grounding` | `anchor`, `retrieved`, `none` |
| `grounding_manifest_json` | The `find_sources` manifest and the kept span keys |
| `figure_id` | The result (built or reused), set once |
| `created_at` | |

**`interactive_figures`** (rebuilt, WORKFLOW as before; every existing row copied unchanged):
- `origin` CHECK widened to the six values;
- `extraction_id` nullable, with `CHECK (extraction_id IS NOT NULL OR request_id IS NOT NULL)` (a practice-host figure with no reading position, P3);
- `request_id` (nullable, references `figure_requests`; NULL on RW5a/b rows);
- `goal_text` (nullable, denormalized for listing and the collapsed line);
- `grounding` (`anchor` default, `retrieved`, `none`);
- `input_span_keys_json` (default `'[]'`): `(extraction_id, span_id)` pairs for retrieved passages in other sources; `_figure_spans` and every held-out recheck read it beside `input_span_ids_json`;
- `tier` (`grammar` default, `sketch`), and for sketches `program_version` and `engine_sha256`; a sketch's `SketchProgramV1` is stored in `spec_json` with `spec_version = 'sketch-v1'`, so the reuse index (`input_hash, spec_version`) and the shown-row CHECKs hold unchanged;
- indexes as before plus `(request_id)`.

The table-role classification (`db/table_roles.py`) adds `figure_requests` as RAW_LEDGER; no DERIVED table, so no replayer. Update the head fixture per CLAUDE.md (`fixtures/migration_head_<N>/`, its README and the five hard-coded paths, then the DB reference scripts).

### 13.2 P3's migration (`help_assists`)

`help_assists` is rebuilt to widen `assist_kind` with `'figure'` and `hint_kind` with `'explore_figure'`, and to add a nullable `figure_id`. Its own migration because it is the hint service's table and lands with P3 (it would be dead weight in P1). Next free at P3's landing.

### 13.3 What persists, and what replay does

| Row | Role | Replay |
|---|---|---|
| `figure_requests` | RAW_LEDGER | Never cleared, never re-run |
| `interactive_figures` (both tiers) | WORKFLOW (paid outputs) | Never re-run (W9) |
| `figure_predictions` | RAW_LEDGER | As today |
| `judgment_ledger` `figure_verified`, `figure_tier` | RECEIPT | Append-only |
| `help_assists` `figure` rows | as the table | As the hint service's rows |
| Sketch runtime state, scenes, slider positions | not persisted | — |

### 13.4 Events

Existing kinds with a payload `event` and `authority_class = 'salience_only'` (parent §4.3): `reader_action_invoked` gains `show_me_requested`, `figure_opened`, `figure_played`, `sketch_paused`, `sketch_error`. Each gets a salience-firewall case.

## 14. Successor ruling

**None, in every phase**, checked against `docs/algorithm-change-playbook.md` step 1 ("Decide whether the change alters persisted meaning"):
- **P1, P2:** content and display. Figures write nothing that scoring, scheduling, projection or serving reads (parent §8.6). The goal text reaches learner-text gaps never (§11.1).
- **P3:**
  - The figure hint-equivalent maps onto `hints_used` with its existing meaning (the hints spec's §10.1 ruling; CA2's §13 ruling for K6). It applies to new attempts only, and no existing attempt can be reclassified: no figure could be opened during an attempt before P3.
  - The `explore_figure` chooser kind changes which help is served, not evidence: a kill switch and no successor, as the hints spec rules for its learned layer (§6.4 there).
  - The diagnoser's `+figures-v1` suffix follows the `+workbench-v1` precedent (no successor; contexts without a trace hash as before).
  - If the P3 agent finds any of these changes an existing attempt's classification in a way the field doesn't already express, it stops and makes it a successor (the next free `mvp-0.N`), as CA2's ruling says.
- **Deferred, and a successor if built:** prediction outcomes as numeric weak observations (the parent's §17 row).

## 15. Every number

None of these is a learner-model weight, margin or threshold (SM8). Each is classified in `params/parameter_registry.py` (module constants are declared explicitly; config leaves get `_ConfigRule`s).

| Number | Value | Class | Why it exists |
|---|---|---|---|
| `GROUNDING_PASSAGES` | 3 | structural, operational, `keep` | Prompt size; more passages dilute the author's context |
| `figures.show_me_enabled`, `figures.sketch_enabled`, `figures.help_kind_enabled` | true | structural, operational | Kill switches |
| `SKETCH_MAX_SOURCE_BYTES` | 32 KiB | structural, operational, `keep` | Bounds a program to one idea; reviewable |
| `SKETCH_MEMORY_BYTES` | 64 MiB | structural, operational, `keep` | Machine safety |
| `SKETCH_FUEL_PER_CALL` | set so one call fits `SKETCH_FRAME_MS` on carson, measured at P2 and recorded | structural, operational, `keep` | Deterministic work cap, identical in verifier and desktop |
| `SKETCH_FRAME_MS`, `SKETCH_WATCHDOG_FRAMES` | 16 ms, 30 | structural, display, `keep` | Interactivity; pause instead of freezing |
| `SKETCH_MAX_ELEMENTS` | 4,000 | structural, display, `keep` | Renderer cost |
| `SKETCH_TIME_SAMPLES` | 9 | structural, numerical, `keep` | Verification coverage of a clocked sketch |
| `CLAIM_REL_TOL` | 1e-9 | structural, numerical, `keep` | Float equality, the golden corpus's |
| `ODE_SAFETY` | 4 | structural, numerical, `keep` | Margin on a derived integration-error estimate |
| `MC_FALSE_ALARM` | 1e-6 per check | structural, numerical, `keep` | How often a correct Monte Carlo sketch may be refused by chance |
| The figure hint-equivalent | 1 per figure per attempt | structural form | Maps to the existing field's meaning; not a weight |
| `explore_figure` level | 2 | structural form | The ladder's position; levels 1–3 count the same (Q7) |
| Existing figure caps | unchanged | — | `spec.py:50-90`, `routes.py:45`, `FiguresConfig` |

## 16. Phases, smallest valuable first

| Phase | Ships | Needs | Size | Migration | Kill switch |
|---|---|---|---|---|---|
| **P1 — "Show me" in the Reader** (**first slice**) | `FigureRequestV1`, `figure.request`; goal text into the author's context and the hash; grounding through `find_sources` with abstention; joint requests; the intent box passing its text (the `reader_intent` prompt clause); *show me ▸* in the Reader's Ask rail; the tutor's `figure_goal` offer; the landing line, home passage and *not from your books* badge; the report's show-me block (requests, grounding mix, abstentions, unsupported kinds, "not right?" rate) | — (Reader-only; CA2 not needed) | **S–M** | One (§13.1) | `figures.show_me_enabled` (off: today's figures exactly; the tutor's prompt and output as RW5b) |
| **P2 — the sketch tier** | The engine build script and pinned artifact; the Worker runtime and the sidecar `wasmtime` runner; `SketchProgramV1` and `Scene` schemas, both validators; the display-list renderer (SVG primitives, handles, play, new sample, values table); `FigureAuthorOutputV2` and `figure_tier` receipts; verification steps 1–5; labels; engine-upgrade re-verification; "not right?" with errors; the hostile-sketch corpus; the sandbox review | P1 (the request); B3 re-confirmed | **M–L** | None (P1 carried the columns) | `figures.sketch_enabled` (off: the author's contract is RW5b's byte for byte; stored sketches list as *can't draw this yet*) |
| **P3 — exploration as evidence** | Figures in attempts (the CA2 panel's *show me ▸* with its cost line, the workbench step, feedback); the `help_assists` figure row, fold and reveal check; the cold take step and token; `explore_figure` in the chooser; `figure` in RW2c's `help_outcomes` and the hints report; the diagnoser's `+figures-v1` trace | P1; CA2 for the practice host (the Reader workbench works without it) | **S–M** | One (§13.2) | `figures.help_kind_enabled` (off: no figure in attempts, no chooser kind; `help_outcomes` unchanged) |
| **P4a — figures follow the section** | The correspondents read and the *also in your books* line | C0a, CA5 | **S** | None | `reader.correspondence.enabled` (CA5's) |
| **P4b — the teacher's manipulatives** | The `visual` contract as `FigureRequestV1`, predictions suppressed in lessons, the doctrine paragraph | TE1 (built there) | **S** inside TE1 | None | TE1's |

**Why P1 first.** It answers the owner's request on its own ("from a natural language query, or jointly"), uses the pipeline and retrieval that exist, touches no evidence, and needs no new runtime. P2 is the largest and the only security boundary, so it goes second with its own review. P3 is small but waits for the help record CA2 builds, so it doesn't build on the overlay CA2 replaces.

**Gates and tests** (targeted while iterating, the full suite once at landing, memory-capped):

| Gate | Phase | Asserts |
|---|---|---|
| G-SM1 | P1 | A goal-only request with `figures.show_me_enabled = false` is refused; with it on, a request with neither goal nor anchor is refused |
| G-SM2 | P1 | Held-out and exam spans never reach the author: anchor, neighbours, retrieved passages across extractions; and a figure whose retrieved span becomes held out later is not listed or delivered (extends `test_figures_rw5b_review.py`'s pattern) |
| G-SM3 | P1 | Grounding `none` forces `illustrative`, drops quotes, and the badge reads *not from your books* |
| G-SM4 | P1 | The reuse key changes with the goal text and grounding and not with origin; an RW5a/b request hashes byte-identically to before the migration |
| G-SM5 | P1 | `goal_author = tutor` only for a stored `figure_goal` (a forged goal is refused); `teacher` only from the lesson service |
| G-SM6 | P1 | The intent box passes its text; the routed line names what is used; empty text is today's behaviour |
| G-SM7 | P1 | Switched off, the tutor's prompt, output model and Reader view are RW5b's, key for key |
| G-SM8 | P1 | Migration: every RW5a/b row copied unchanged; the CHECKs; the head fixture; `table_roles` |
| G-SM9 | P2 | One engine, two hosts: a parity corpus of sketches gives bit-identical probes and scenes in vitest (the Worker) and pytest (`wasmtime`) |
| G-SM10 | P2 | Verification steps 1–5 on a corpus of good sketches (pass, with the right check lines) and planted-wrong ones (a claim off by a constant, an unbound drawn path, a nondeterministic call, a NaN at one grid corner, an over-fuel `step`), each refused for the right reason |
| G-SM11 | P2 | Hostile-sketch corpus: no IPC, network, storage, DOM or timer reachable from the Worker or the sidecar runner; caps terminate; text never lands in the badge slot |
| G-SM12 | P2 | `FigureAuthorOutputV2` off is RW5b's byte for byte; on, a `figure_tier` ledger row per build with the reason |
| G-SM13 | P2 | Engine digest mismatch refuses; an engine upgrade re-verifies with no model call |
| G-SM14 | P2 | In the real desktop webview on Linux: a request from inside the sketch Worker to the IPC endpoint is refused (if not, the opaque-origin frame is added before merge) |
| G-SM15 | P3 | A figure opened during an attempt adds exactly one hint-equivalent at Submit, however often reopened; feedback-screen figures add none; the reveal row on overlap |
| G-SM16 | P3 | On a cold check: no figure listed; *show me* converts first; a request without the take-step token is refused under `cold_attempt` |
| G-SM17 | P3 | `explore_figure` is an option only with a qualifying existing figure, never one built from the item's own blocks; its propensity is logged; never offered cold |
| G-SM18 | P3 | `help_outcomes` lists `figure` deterministically (computed twice); the diagnoser context hashes as before without a figure trace |
| G-SM19 | all | The salience firewall covers every new `event`; `lint-imports` keeps `evidence-never-reads-figures` |

The owner checkpoint for P1 is one real "show me" on a `fixtures-local` copy with the plan route; for P2, the sandbox review's report and five real sketches from the owner's subjects (probability, linear algebra, ML).

## 17. Risks

| Risk | Mitigation |
|---|---|
| **R1. The sandbox has a hole.** | Sealed interpreter with no bindings, data-only output, the hostile corpus, the IPC gate in the real webview, an adversarial review before merge, the kill switch |
| **R2. A checked-looking figure of a wrong idea.** | Element-scoped check lines, *not covered* lines, *not checked against the book* always, AI-written labels on claims, "not right?". The checks say what they checked and nothing more |
| **R3. Grammar erosion:** the author picks sketches for what the grammar could do (costlier, weaker checks) | The prompt prefers the grammar; `why_not_spec` is required and reported by kind; the tier mix is in the report; a rising sketch share with grammar-expressible reasons is a prompt fix, not a rule |
| **R4. Illusion of understanding:** exploring feels like learning | Exploration is tier 2 at most; in attempts it counts as help; the chooser's outcomes are measured against later independent success, which is what decides whether figures stay prominent |
| **R5. Slow sketches** on the interpreter | Bounded programs, summaries over raw paths, the watchdog's pause, the report's pause counts (trigger for Pyodide or a faster engine) |
| **R6. Ungrounded figures look authoritative** | The badge and the line say *not from your books*; quotes are dropped; the abstention count is in the report |
| **R7. Injection through book text** | The author is an isolated, tool-free turn (`routes.py:249-256`); source and goal are data; its output is either declarative or sealed; nothing it writes can act |
| **R8. Answer leakage on practice** | `assisted_practice` grounding, no stem or key to the author, the reveal check on the figure's text, the hint-equivalent |
| **R9. One more dependency and binary** (`wasmtime`, the engine) | Pinned, hashed, reproducibly built; the grammar tier keeps working with the sketch tier off |

## 18. Open questions, each with a recommended answer

**Decided (owner, 2026-10-25): all fifteen recommendations below are adopted as written.**

| # | Question | Recommendation |
|---|---|---|
| Q1 | Choose the tier inside the author's one call (`spec | sketch | unsupported`), or with a separate Decider call first? | **One call.** The author knows whether its spec can express the idea; a pre-call adds latency and a route for a worse-informed judgment. The `figure_tier` ledger row is the receipt |
| Q2 | Sketch engine: QuickJS-in-wasm (same bytes in the desktop and the sidecar via `wasmtime`), Pyodide, or a sandboxed iframe? | **QuickJS-in-wasm.** Strongest boundary, exact parity between drawn and verified values, small and fast to start, portable to the phone. Pyodide only if watchdog pauses become common |
| Q3 | A consent click before a sketch runs, as manim has? | **No.** The runtime, not a click, is the protection (§9.6); the frame's ⓘ explains how it runs |
| Q4 | Show a sketch whose own stated claim fails, labelled "not checked"? | **No.** It is demonstrably wrong; RW5a's "fail → not shown" stands. *Not checked* is for sketches that state no checkable claim |
| Q5 | Sketch tier on by default once its review passes? | **Yes** (W3), behind `figures.sketch_enabled` |
| Q6 | Should learner-text gaps read a show-me goal? | **No.** It is a request to build, like "not right?"; the box says where it goes. Questions still go through Ask |
| Q7 | A figure opened during an attempt: one hint-equivalent (level 2 in the chooser)? | **Yes.** It explores the idea and writes no step, so not primed; levels 1–3 count the same, so the level only places it on the ladder |
| Q8 | Mirror kept figures into `source_objects` (`artifact`)? | **No, for now.** A join through the anchor's section serves correspondents; P3's review path has no use for figure rows. Revisit if source-object review needs them |
| Q9 | Key figure complexity or scaffolding to the AD predicted level? | **No.** It would put learner state in a content prompt and break reuse. The teacher, which reads the state, says what to hand over in the goal |
| Q10 | Figures on the phone? | **Not in v1.** Later, view-only, with an allowlisted read RPC (an owner decision, as CA7) when the mobile client is used most days |
| Q11 | In a lesson, build the visual without a separate press? | **Yes.** Opening the lesson is the press; the turn waits on it anyway; T1's offer is keyed by the lesson's turn method |
| Q12 | Put P2's columns in P1's migration? | **Yes,** RW1a's precedent: one rebuild of `interactive_figures`, not two. `help_assists` waits for P3 |
| Q13 | Read the MCP spec's "never execute arbitrary model code in the learning service" (§9.3) as allowing the sealed verifier? | **Yes,** with a one-line amendment there: a sealed interpreter with no imports, fuel and memory caps is "the sandbox runs it" (as RW5c's sympy check), not arbitrary execution |
| Q14 | Build a figure when retrieval finds nothing? | **Yes,** labelled *not from your books*, as RW1c abstains and still explains |
| Q15 | One intent-box action (`make_explorable` that takes words), or a separate "show me"? | **One action,** relabelled *show me…*; an empty box is today's behaviour |

## 19. Deferred, with triggers

Triggers are `keep`: they decide when to spend engineering effort.

| Deferred | What it would take | Revisit when |
|---|---|---|
| Pyodide (numpy) sketches | A second sealed engine, its parity corpus and review | Watchdog pauses on more than 1 in 10 opened sketches over a month |
| 3-D scenes | A projection primitive in `Scene` and the renderer | 3-D among the top three `why_not_spec` or unsupported kinds over a month |
| Phone view-only figures | An allowlisted read RPC and the renderer in the phone client | The mobile client is used most days and the owner asks |
| MCP chat figures | C2's `show_me` tool and an MCP App component | C2 lands |
| Prediction outcomes as numeric weak observations | The parent's §17 row (an observation model, a harness arm, a successor) | That row's trigger |
| A learned figure-vs-other-help policy | The hints spec's learned chooser over kinds, with `explore_figure` as a kind | The hints spec's §13 trigger, with `explore_figure` among the supported kinds |

## 20. Cross-spec notes (record when each phase merges)

- `spec_reader_workbench_v1.md`: §8 RW5 and the phase list point here; its §17 row "Generated-code figures" is built here as the sketch tier (P2) and its trigger is superseded by the owner's 2026-10-25 direction and this design's review gate (the unsupported-kind counts remain its evidence); §5.10's "figure views" become real in P3.
- `spec_teacher_v1.md`: `TeacherTurnV1.message.visual` is a `FigureRequestV1` (origin `teacher`); the doctrine row "Instruments over description" is served by RW5d; the deferred row "Teacher-built demos with headless verification" is built here as the sketch tier, so its trigger is superseded.
- `spec_adaptive_hints_v1.md`: `explore_figure` joins §4.2's kinds at level 2 with its precondition (P3).
- `ux_reader_compare_ask_v1.md`: §7.1's box gains *show me ▸* with its cost line (P3); §7.7's cold rules cover it.
- `spec_mcp_frontend_v1.md`: §9.3's sentence amended per Q13; C2 adds origin `chat`.
- `ux_reader_workbench_v1.md`: §4.7 gains the show-me entry and the sketch badge; §11.2's "AI-generated code, sandboxed" label becomes *AI-written simulation · sandboxed*; §4.10 gains the show-me box row.
