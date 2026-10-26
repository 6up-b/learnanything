# Reader RW5d: "Show me", explorable figures from a question, a passage or both, a sketch tier, rich tiers (JS and Manim), figures built ahead of need, and exploration as evidence (v1, revision 2)

**Status:** owner-approved. Rev 1 (2026-10-25): Q1–Q15 adopted as recommended. Rev 2 (2026-10-26): Q16–Q27 adopted as recommended.

## Revision 2 (owner, 2026-10-25)

> "for the spec_reader_show_me_figures_v1.md, I want to have the model extensibility to render manim animations or regular js animations. We dont want to limit the model's best output artificially. Is there a way also we could be proactive in generating a manim/js visual explanation since they might take a few minutes for the coding models to fully generate? If not I'm fine with just 'Show me' with latency"

What changed, by section:
- **No artificial ceiling (owner decision).** The author's one-call tier choice widens to `spec | sketch | js_animation | manim | unsupported`. It is chosen by what best explains the idea, with a receipt. The prompt states each tier's cost and latency and does not otherwise steer toward the cheaper tier (§8.4; principle 6 and R3 rewritten). The two rich tiers are a new section, §9b:
  - **`js_animation`:** full JavaScript (canvas, WebGL, SVG or DOM) with its own animation loop and controls, in an opaque-origin sandboxed iframe (§9b.2);
  - **`manim`:** the existing concept-animation pipeline (Python scene → mp4), reused rather than rebuilt (§9b.3).
- **Proportionate checks per tier** (§9b.4). A rich figure that declares checkable claims has them probed where feasible: JS model functions in P2's sealed engine; Manim's declared pure functions inside its existing bubblewrap sandbox. A figure with no declared claims is labelled *not checked*. Rev 1's rule stands: a figure whose own stated claim fails is not shown.
- **Manim's per-run consent click** gives way, for figures on Linux under the mandatory bubblewrap sandbox, to a standing opt-in (recommended, Q17; §9b.3).
- **Progressive delivery** (§8.6, §6.8). The fast tier answers in seconds when it can. The richer tier keeps building and arrives with one quiet cue: *a fuller animation is ready*.
- **Figures built ahead of need** (new §10b, phase P5). Sources of what to build:
  - the plan's next reading section;
  - blocks that RW5b judged explorable;
  - a TE1 lesson's planned visuals;
  - the diagnoser's open gaps.

  Whether to prebuild is a learned decision with seeded, labelled priors, logged with its outcome. It runs only on the ChatGPT plan, quietly, on mains power, never for exam material, and is capped by `keep` guardrails. The switch is `figures.prefetch_enabled`.
- **Amended rules:** SM3, SM7–SM10, N-b, §4.5 item 5, §9.2 option C, §10.3, §12.3.
- **Updated sections:** phases (new P2b, P5), data model (P1's migration carries the rich-tier columns; P5 adds one table), routes, numbers, risks, gates G-SM20–G-SM30 and §18 (Q2, Q3, Q5 amended; Q16–Q27 new).

---

- **Base (revision 2):** audited on `main` at `a58dae89f` (migration head `221_learner_claim_application_point.sql`; C0a holds 222 on its landing branch; CA2's stage branch carries a `221_workbench_earlier_opened.sql` that renumbers when it lands, so 223 is likely taken before RW5d's P1).
- **Base (revision 1):** `main` at `eae00d58a` (migration head `220_retrieval_spaces.sql`; RW5a and RW5b landed). In flight and read from their specs only: LP claim fixes (migration 221), curriculum C0a (migration 222, `section_coverage` and `reader.correspondents`), Reader CA1 and CA2, the teacher spec rev 4 (approved, not built).
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

**Revision 2 (2026-10-25)** adds two requirements (verbatim at the top):

5. **No ceiling on the medium.** The model may answer with a Manim animation or a full JavaScript animation when that explains best. LearnLoop never caps it at the grammar for its own convenience.
6. **Don't make the learner wait when it can be avoided.** Rich builds take minutes. LearnLoop answers fast where it can, and builds ahead where it already knows what is next. The owner accepts plain latency if this isn't possible; §10b shows it is.

## 1. Thesis

RW5a/b built a good figure *pipeline* with a narrow *door*. The pipeline (a closed declarative grammar, a model author, numeric verification, a trusted renderer, predictions, "not right?", reuse by input hash) is the right core and stays the only figure service. Three things are missing:

- **The door takes no words.** A figure request today is a set of span ids; the learner's text is dropped, and a request with no selection is refused (`figures/service.py:513-515`, "Select a passage, an equation or a figure first."). RW5d adds `FigureRequestV1`: a goal in the learner's words, an optional anchor, and the host it came from. With no anchor, the request is grounded in the learner's library through the existing `find_sources`, so the figure cites their books, or says plainly that it doesn't.
- **The grammar has a ceiling.** Simulations, stochastic processes, agent-based and geometric constructions are refused as "can't draw this yet". RW5d adds a **sketch tier**: a small model-written program that runs in a sealed interpreter with no access to anything, returns a display list the trusted renderer draws, and exposes declared **probes** that code checks against equations stated in the existing grammar. The grammar stays preferred.
- **Exploration evidence goes nowhere new.** Missed predictions already reach learner-text gaps (`service.py:952-956`), which is right and stays. RW5d makes a figure **a help kind**: counted honestly when opened during an attempt, offered by the hint chooser with a logged propensity, and read by RW2c's help outcomes, so "do visuals help you" becomes estimable later without any figure ever certifying anything.

**Revision 2** removes two more limits:
- **The ceiling.** A sealed sketch is still bounded by the interpreter's speed and the display list. Some ideas are explained best by a narrated Manim video, or by a JavaScript animation with WebGL, its own loop and its own controls. The author may now choose either, and the choice is a judgment with a receipt. Each rich tier runs behind the strongest boundary its medium allows:
  - a Manim scene renders under the existing bubblewrap sandbox;
  - a JS animation runs in an opaque-origin frame with no network and no IPC.

  Each is checked where its declared claims can be checked, and labelled honestly where they can't.
- **The wait.** A rich build takes minutes. The fast tier answers first when it can, and the rich one arrives later with one quiet cue. Where LearnLoop already knows what comes next (tomorrow's reading, a lesson's plan, an open gap), it builds ahead, decided by a learned estimate of whether the learner will open the figure. This uses plan headroom only, on mains power, and never touches exam material.

One service, every host: the Reader (selection, intent box, Ask), the Ask panel on practice and feedback (after CA2), the tutor's answer, the teacher's lesson `visual`, and later MCP chat (C2) all send a `FigureRequestV1` to `figures/service.py`.

## 2. Goals and non-goals

**Goals**
- G-a. "Show me" from a question, a passage, or both, on every host that can render a figure, through one request contract and one service.
- G-b. Grounding: a question-only request cites the learner's own passages when retrieval finds them; otherwise it is built anyway and labelled *not from your books*.
- G-c. A sketch tier for what the grammar cannot express, with a stated threat model, a sealed runtime, headless verification of declared probes, honest element-scoped labels, reuse and repair.
- G-d. Exploration as formative evidence: figures as a help kind in attempts, in the hint chooser's sampled kinds, in RW2c's outcomes and in the diagnoser's trace, under the existing tiers (W1).
- G-e. Fit: kept figures resurface on corresponding sections of other books (C0a), and the teacher uses figures as manipulatives in discovery steps.
- G-f. *(rev 2)* The model's best medium. There are two rich tiers: `js_animation` (full JS in a sealed frame) and `manim` (the existing pipeline). The author chooses the tier with a receipt. Checks are proportionate to each tier, and every tier follows the same evidence rules.
- G-g. *(rev 2)* No needless wait:
  - progressive delivery: a fast answer, then the rich one with one quiet cue;
  - learned prebuilding ahead of need, quiet, on the plan, on mains power, and reused by input hash when the learner asks.

**Non-goals**
- N-a. "Matches the book's equation (checked)". That claim stays RW5c's, designed and reviewed before code (`spec_reader_workbench_v1.md` §8.3 amendment). Nothing in RW5d says a figure matches the book.
- N-b. Generated HTML, CSS or DOM **in the app's page**. A sketch never touches the page; it returns data. *(Rev 2 amendment.)* A `js_animation` does write HTML, CSS and DOM, but only inside its own opaque-origin frame. It has no reach into the app's document, its IPC or the network (§9b.2).
- N-c. Figures as certification, or any numeric update of a posterior from exploration (W1 tier 2; the numeric weak-observation row in §17 of the parent stays deferred).
- N-d. Learner-adaptive figure content. The figure author receives no learner state (§10.4 explains, and the teacher is the route for state). *(Rev 2.)* A gap prebuild's goal is written from one open gap's statement (§10b.2, Q23). That is like a teacher's goal: state reaches the author only as a goal sentence, never as history or scores.
- N-e. Turning a whole paper into an interactive system (the parent's §17 ambition). Sketches are bounded, one idea each.
- N-f. Phone rendering in v1, and MCP chat figures (C2 owns them; §13).
- N-g. The dropped MCP anti-cheating idea. Not designed here.
- N-h. *(rev 2)* What prebuilding never does:
  - build on battery, on the phone host or the MCP host;
  - build on OpenRouter;
  - build anything from exam or held-out material, or from an item's own blocks;
  - change what is scheduled or served in practice.
- N-i. *(rev 2)* Video-model renders (`[animation] renderer = "video_model"`) as a figure tier. They are billed per shot on OpenRouter and run no checkable code, so they stay the concept inspector's.

## 3. Standing constraints (binding)

The parent's W1–W14 hold. Restated where RW5d leans on them, with what each means here:

- **SM1 (W1, tiers).** Figure play, slider moves and opening a figure are tier 1 (engagement). Predictions, "what changed?" text and a figure's goal text are tier 2 (formative). Nothing a figure produces is tier 3. The only evidence an attempt produces is its submitted, blind-graded answer.
- **SM2 (W2, honest labels).** The badge slot is code-owned (`FIGURE_FRAME`, `apps/learnloop-tauri/src/screens/reader/figures/FigureInline.tsx:27`). "Checked" appears only for what a non-LLM check ran, scoped to the element it covers. Every figure says *not checked against the book* until RW5c.
- **SM3 (W3, generous defaults).** Every RW5d phase ships on behind its own kill switch. No confirmation dialog guards a safe action. The sketch tier's safety comes from its runtime, not from a click (§9.6). *(Rev 2.)* The same holds for `js_animation`, whose boundary is the browser sandbox (§9b.2). Manim runs native Python on the host under bubblewrap, so it takes **one standing opt-in** instead of a per-run click (§9b.3, Q17). The opt-in is a one-time permission, not a dialog on each action.
- **SM4 (W7 and D46, cold).** During a check on your own, no figure is shown or built unless the learner takes it as help, which converts the attempt (§11.3). The figure-only stimulus rule (`ux_reader_compare_ask_v1.md` §8.5, Q10) is a source crop, not an explorable, and is unchanged.
- **SM5 (W8, blind grading).** The grader never sees a figure, its spec, predictions or exploration.
- **SM6 (A8, exam material).** Exam and held-out material is never sent to the figure author, never retrieved for grounding, never shown in a figure; the existing one predicate (`exam_material(...)`, `spans_withheld`) is asked before any call and on every later delivery, as today (`service.py:219-258`).
- **SM7 (bitter lesson).** These are model judgments with receipts:
  - which tier;
  - which passages;
  - what to draw;
  - whether a figure should be offered as help;
  - *(rev 2)* which blocks in an upcoming section are worth a figure.

  There is no word list and no keyword routing. *(Rev 2.)* Nothing steers the tier toward the cheaper one except a plain statement of each tier's cost and latency (§8.4).
- **SM8 (no made-up constants).** RW5d adds no weight, margin or threshold to the learner model. Its numbers are caps on money, time, memory or display, or numerical tolerances, each a labelled `keep` guardrail (§15). *(Rev 2.)* The prebuild decision (§10b.3) is not part of the learner model. It predicts whether a figure will be opened, and is a posterior expected-utility rule over learned quantities. Each prior is seeded and labelled with its `prior_basis` and width, and registered in the parameter registry. The only fixed numbers are its `keep` caps on background builds, render minutes and concurrency.
- **SM9 (T1 plan-first).** Every route runs plan-first (`chatgpt_plan`). A pressed action that finds the plan down may offer OpenRouter (redesign D: the offer is the grant, keyed by the origin RPC method, `ai/plan_fallback.py:1-31`). ~~Nothing builds in the background, and no figure is pre-built for an offer.~~ **Rev 2 (owner, 2026-10-25):**
  - *Prebuilds run in the background* under T1's quiet rule (`plan_fallback.quiet()`, `:216-228`). They use the plan only: no offer, no grant honoured. If the plan is down they wait, and they are dropped when their horizon ends (§10b.5).
  - *The rich half of a pressed request* is spawned by the press. It captures `unit_origin()` at creation (`:524`), so a grant the learner gave on `figure.request` covers it. If no grant exists, it waits for the plan and never asks again.
- **SM10 (W12, attention).** Nothing LearnLoop starts moves focus, animates on its own, or opens a modal or toast. A figure lands where its request was made. *(Rev 2.)* A JS animation starts paused until the learner presses inside it or presses *▸ play*, which the host enforces (§9b.2). The *fuller animation is ready* cue and a prebuilt figure's line are static text under their passage. They are never counts, toasts or badges elsewhere (§6.8, §6.9).

## 4. Code truth (audited on `main` at `eae00d58a`; revision 2 additions on `a58dae89f`)

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

**Revision 2 audit (`a58dae89f`): the pieces the `manim` tier reuses.**

| What | Where | Notes |
|---|---|---|
| Config | `config/schema.py:725-770` (`AnimationConfig`) | `enabled`; `renderer: manim \| video_model`; `quality` (`qm` default); `timeout_seconds` 600; the pacing band, 30–60 s; `latex_enabled` (off); `auto_repair`; `manim_executable`, `venv_path`, `auto_provision_venv` |
| Route | `ai/routing.py:88`, `:202-203` | AITask `animation`, used by purposes `concept_animation` and `video_storyboard`. Not in `METERED_PRICE_SETTINGS` (`ai/plan_fallback.py:78-96`) |
| Scene contract, scaffold, prompt | `content/authoring/ai_contracts.py` (`ManimAnimation`, `CONCEPT_ANIMATION_SCENE_SCAFFOLD`, `concept_animation_prompt`) | The context is concept-shaped (`ConceptAnimationContext`), with no source spans |
| Validator | `concept_animation.py:156-195` (`validate_scene_code`) | Imports limited to `manim`, `numpy`, `math` (`:68`); forbidden builtins and dunder access (`:70-76`); a required `Scene` subclass |
| Pacing lint | `:441-581` | A static duration estimate. One repair round-trip |
| The render sandbox | `:311-374` (`_sandboxed_command`), `:583-668` (`render_scene`) | `bwrap --unshare-all --die-with-parent --new-session`; read-only system and interpreter mounts; `/tmp` as tmpfs; the scratch directory is the only writable path; `HOME` set to the scratch directory. **Refuses on Linux without `bwrap`**; runs unsandboxed elsewhere. No memory or CPU limit beyond the wall-clock timeout |
| Job body and repairs | `:900-1116` (`generate_concept_animation`) | generate → validate (one corrective round) → pacing (one round) → render → one stderr repair when `auto_repair` → store. It never leaves a row wedged. Cancel through `report()` |
| Store and playback | `_store_video` `:866`; `vault/paths.py:102-110` (`media/animations/sha256-<hex>.mp4`); `animation_media.py` (faststart remux, duration probe) | Content-addressed. Served over `llmedia://` (`src-tauri/src/main.rs:211-220`). The player fetches the bytes into a blob URL, because WebKitGTK does not range-request a custom scheme (`components/ConceptAnimationSection.tsx:60-130`) |
| Consent | RPC `handlers/animation.py:109-120`; service `concept_animation.py:688-694`; UI `ConceptAnimationSection.tsx:352-400` | A per-run tick, re-checked on the server. The copy says the scene runs locally and "is not reviewed by a human before running" |
| Table | `migrations/114_concept_animations.sql`, `157_concept_animation_renderer.sql`; `db/table_roles.py:155` (RAW_LEDGER) | Keyed by `concept_id` (with an optional LO), not by spans or an input hash. One pending row per concept |
| Tests | `tests/test_concept_animation_validator.py` (bwrap required on Linux `:201`, wrapped `:180`), `test_concept_animation_service.py` (repairs, the store, no wedged rows), `test_sidecar_animation.py` (consent and missing manim `:71`), `test_animation_media.py` | The figure tier reuses these code paths, so their tests keep covering it |

**What this means for rev 2.**
- The **boundary is bubblewrap, not the allowlist.** The docstring's "is NOT a sandbox" (`:9-20`) is about the AST allowlist alone. On Linux, `--unshare-all` with no home, vault or network mounted is a real sandbox. It is weaker than a browser's: native CPython, numpy and ffmpeg against the host kernel. That is why rev 2 asks for one standing opt-in rather than none (§9b.3).
- The **per-run click is incompatible with prebuilding** (§10b), and per W3 it guards an action whose safety comes from the sandbox.
- The **concept-shaped, unkeyed table** is why figures store their Manim output in `interactive_figures`, keyed by input hash like every other tier, rather than in `concept_animations`.

### 4.3 Retrieval, help and evidence

- `find_sources` (`source_retrieval/find_sources.py:613`; intents `explain`, `remediate`, `alternative`, `worked_example`, `compare` at `:74`) and `find_sources_for_caller` (`:899`), with policy derived on the server from a `CallerContext` (`source_retrieval/policy.py:23`, `:78-93`; caller kinds include `reader`, `tutor`, `learner`; no `figure` or `teacher` yet). Exam material is withheld inside (`find_sources.py:753-756`).
- `help_assists` (`migrations/210_help_assists.sql:22-60`): `assist_kind` CHECK `hint, check, discriminate_answer, bridge, example, compare_methods, feedback`; `hint_kind` CHECK of twelve kinds. No figure kind.
- RW2c's `help_outcomes` (`workbench/help_outcomes.py:99`): `_HELP_KINDS = ("hint", "bridge", "example", "compare_methods")`. The parent spec's §5.10 says it reads "figure views"; **the code does not**, and there is no row that records a figure being used as help.
- The hint chooser's preconditions (`hints/options.py:99`: `worked_parallel` needs a worked example or another instance at hand) are the pattern a figure kind follows.
- `source_object_versions.object_type` already allows `artifact` (`migrations/094_source_objects.sql:27-29`).

### 4.4 The desktop webview

Tauri 2 (`apps/learnloop-tauri/src-tauri/Cargo.toml:15`), one capability for the `main` window (`capabilities/default.json`), two custom protocols (`llpdf`, `llmedia`; `src-tauri/src/main.rs:204-210`). The CSP (`tauri.conf.json:27`) already allows `script-src 'self' 'wasm-unsafe-eval'` and `worker-src 'self' blob:`, so a WebAssembly engine in a Worker needs no CSP change. The parent's §17 row worried about Tauri iframe isolation on Linux; the design below puts no model code in any frame (§9.3). The B3 Rust-toolchain blocker in that row appears fixed (`cargo check` passes in landing gates, e.g. `docs/reviews/ux-phase2.md:515`); P2's first task re-confirms it.

**Revision 2 (the `js_animation` frame).**
- **Versions.** Tauri `2.11.2`, wry `0.55.1` (`src-tauri/Cargo.lock`).
- **CSP.** The page's CSP has `frame-src https://www.youtube-nocookie.com` and nothing else, so a figure frame needs one CSP addition: its own scheme.
- **Inherited CSP.** A `srcdoc`, `blob:` or `data:` frame would inherit the page's policy, which forbids inline script. So the frame document is served by a new custom protocol with its own CSP header (§9b.2).
- **Capabilities.** The window's capability grants `core:default`, `dialog:default` and `opener:default` (`capabilities/default.json`). A frame that reached IPC could open URLs or dialogs, which is why G-SM14 is extended to the frame.
- **One web process.** WebKitGTK runs a page's iframes in that page's web process, on its main thread; it does not isolate frames by site. A tight loop inside a frame stalls the whole Reader, and the host cannot pre-empt it from JavaScript. That is why the frame carries code-inserted loop guards and a crash marker (§9b.2), not only a heartbeat.

### 4.5 Corrections to the framing

Each of these refines the approved framing against the code:

1. **"Prediction answers and 'what changed?' go to the grader/diagnoser."** The grader, never (W8, SM5). The diagnoser only through an attempt's help trace, as RW2b's discriminating answers do (`spec_reader_workbench_v1.md` §5.4, `+workbench-v1`). Missed predictions already reach learner-text gaps, so outside attempts nothing new is needed (§11.1).
2. **"Passing → checked, else not checked."** A sketch whose own stated claim *fails* is demonstrably wrong, so showing it as "not checked" would mislead. RW5a's rule (fail steps 1–2 → not shown) is kept: a failed claim gets the second attempt, then the honest failure line. *Not checked* is for a sketch that states no checkable claim (§9.5).
3. **"Kept figures become source objects."** Every built figure is already persisted and tied to its spans. Surfacing it on corresponding sections needs a read through the figure's section, not a second store; mirroring into `source_objects` is Q8, recommended no.
4. **"Figure complexity keyed off the AD predicted level."** Not earned: it would put learner state in the author's prompt (today it has none, `routes.py:21-24`), break reuse by input hash across sessions, and duplicate the teacher, which already reads the latent state and can say what to hand over in the goal text (§10.4, Q9).
5. **"A model judgment chooses the tier."** Yes, and it is already there: the author's `unsupported` verdict is a model judgment with a receipt. RW5d widens that verdict to `spec | sketch | unsupported` in the same call (§8.4) instead of adding a routing call. *(Rev 2.)* The verdict widens again, to `spec | sketch | js_animation | manim | unsupported`, still in one call. For a rich tier, the author writes the brief and the optional fast figure, and a second **authoring** call writes the program (§8.6). That second call writes the figure; it does not decide the tier.

### 4.6 What proactive work can hang on (rev 2)

| Signal | Where | Use in §10b |
|---|---|---|
| T1's quiet block | `ai/plan_fallback.py:216-228` (`quiet()`: "automatic work (keep-ahead on reading progress) … A grant is never for background work") | Every prebuild runs inside it |
| Spawned units inherit the press | `plan_fallback.py:524` (`unit_origin`), `:532` (`unit_token`) | The rich half of a pressed request |
| Keep-ahead on reading progress | `learnloop_sidecar/handlers/reader.py:1718-1764` (`reader.mark_section_progress`, `keep_ahead`); `content/pipeline/add_source.py:2026` (`keep_ahead_for_reader`) | The existing precedent for quiet work one step ahead of the reader. The section-progress hook is a prebuild trigger |
| The plan's reading block | `daily_plan/reading.py:81` (`next_reading_target`); RW7b's path filter (`reading_path_plan_upgrade.py`; `split_json["reading_path"]`) | The next section the plan will open |
| RW5b's explorable judgments | `figure_admission.py:110-150` (`explorable_yes`, `tutor_explorable_yes`); `handlers/figures.py:160-207` | Blocks already judged able to support a figure |
| The lesson plan (TE1, not built) | `spec_teacher_v1.md` §9 (`write_plan`, `:540`), §8.2 (`visual`) | A lesson's planned visuals |
| Open gaps and misconceptions | the diagnoser's hypotheses and learner-text gaps (`diagnosis/text_gaps/jobs.py`), read through the lesson brief's `nodes` shape (`spec_teacher_v1.md` §8.1) | Candidate goals for the next session's help figures |
| The job queue | `ctx.ingest_jobs` (`enqueue_concept_animation`, leases, heartbeats, `report()` cancellation) | Background builds and their cancellation |
| The parameter registry | `params/parameter_registry.py`; LP §2 fields (`treatment`, `prior_basis`, `prior_scale`) | The prebuild model's priors and caps |
| Power state | **nothing in the code reads it today** | A new small reader (§10b.4) |

## 5. Principles

1. **One request contract, one service.** Hosts differ in where a figure lands and what the press costs, never in how a figure is built.
2. **The learner's words shape the figure; they never grade.** The goal text goes to the figure author, like "not right?" does today (UX §4.10).
3. **Books first, then honest abstention.** Grounded figures cite and quote; ungrounded ones say *not from your books* (RW1c's abstention pattern).
4. **Data, not code, crosses into the page.** Grammar figures are data; sketches compute in a sealed interpreter and return data. The trusted renderer draws both. *(Rev 2.)* Rich tiers never cross into the page either:
   - a JS animation runs in its own opaque-origin frame, reached only through a narrow message channel;
   - a Manim figure crosses as an mp4.
5. **Checks are scoped to what they checked.** A probe check names the element, the stated equation and the settings it covered.
6. ~~The grammar is preferred.~~ **(Rev 2, owner decision.) The best medium for the idea, chosen by the model.** Each tier's cost, latency, checks and reach are stated plainly to the author, and nothing else steers it. A grammar figure is still cheapest, most strongly verified and accessible by construction, and the author is told so as fact, not as a preference. Every tier must say why it was chosen (`why_this_tier`).
7. **Exploring is help, not evidence.** It counts as help where help counts, and its effect is measured later against cold outcomes.
8. **(Rev 2) Same rules, every tier.** A figure counts as help when opened in an attempt, stays hidden on a cold check and is never seen by the grader, whatever its tier and however it was built (pressed or prebuilt).
9. **(Rev 2) Build ahead where the next step is already known, and only there.** The plan, the path, a lesson's plan and open gaps say what is next. A learned estimate says whether it is worth building, and quiet plan headroom pays for it.

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

Figures stay desktop-only (`handlers/figures.py:48-56`). A view-only grammar figure on the phone is a later mobile item (§16, trigger). The sketch engine is portable (WebAssembly in Safari), so the phone would need only an allowlisted read RPC, an owner decision as in CA7. *(Rev 2.)* Still none for every tier. A Manim mp4 would be the easiest to show on the phone later, and a JS animation the hardest (it would need its own sandbox review in Safari). Prebuilding never runs on the phone host (N-h).

### 6.8 Rich tiers and progressive delivery (P2b)

**A fast answer first, the fuller one later.** The author chose `js_animation` and also wrote a fast figure (§8.6):

```
  §6.4 ¶2  ... the eigenvalues of a real 2×2 matrix are real or a conjugate pair ...
  ▾ interactive version · AI-built illustration · not checked against the book
    [ grammar figure: phase portrait, sliders a, b ]
    ◌ a fuller animation is being written · usually about 3 min · keep reading · cancel
```

- The dim `◌` line sits inside the figure's frame, under the figure. It never sits elsewhere, and it never moves. *usually about N min* appears only once the report has a p50 for that tier (UX §4.0). It is never a countdown.
- When the rich figure lands, the line becomes:

```
    ◇ a fuller animation is ready · open ▸
```

- *open ▸* swaps the frame's content to the rich figure, and *◂ the quick version* swaps back. Both stay listed under the passage as one figure line with two versions, never two lines.
- If the learner has collapsed the figure or left the passage, the cue sits on the figure's collapsed line instead: *▸ interactive version · a fuller animation is ready*. Nothing appears anywhere else: no toast, no count, no rail badge.
- **When it fails**, the line reads *the fuller animation couldn't be built · why ▸* (the code-written reason), and the quick version stays. When the plan is down and no grant exists, it reads *the fuller animation is waiting for the ChatGPT plan*.

**When only a rich tier fits** (no fast figure), the pending line under the passage shows the build's real phases, in plain words:

```
  ◐ writing an animation for this passage · usually about 4 min · keep reading · cancel
  ◐ checking it · ◐ rendering the video (manim) · ◐ getting it ready (js)
```

Each phase is reported by the job's `report()` heartbeat (as `generate_concept_animation` does, `concept_animation.py:900-922`). There are no percentages and no fake progress.

**A JS animation in its frame:**

```
  ▾ interactive version · AI-written animation · sandboxed · not checked against the book   ⓘ
    ◇ shows: how a softmax attention head redistributes weight as the query rotates    (AI-written)
    ┌──────────────────────────────────────────────────────────────────────────────┐
    │  [ the model's own canvas/WebGL drawing and its own controls ]               │
    │                                         ▸ paused — press to start            │
    └──────────────────────────────────────────────────────────────────────────────┘
    checked by LearnLoop:
      · the weights it draws from sum to 1 at 27 tested settings
      · the drawing itself is not checked
    ◂ the quick version · values as a table · not right?
```

- The badge, the checks list and *not right?* are code-owned chrome **outside** the frame (SM2). The frame has a fixed border and a capped height. It is never full-screen and never overlays the page.
- **ⓘ how this runs:** *"Written by LearnLoop's model as a small web page. It runs walled off inside LearnLoop: it can't reach your files, your notes, the network or the rest of the app."*
- **States:**
  - *paused — this animation was too slow here · resume ▸* (the loop guard);
  - *this animation stopped LearnLoop last time · run it again ▸* (the crash marker, §9b.2);
  - *this animation hit an error · not right? (prefilled)*.

**A Manim figure:**

```
  ▾ animation · AI-made video · not checked against the book   ⓘ
    ◇ shows: why the trajectory spirals when the eigenvalues are complex       (AI-written)
    [ ▶ video, 0:48 ]                                     transcript ▸
    checked by LearnLoop:
      · the curve is drawn from x(t) = e^{at}cos(bt), which matches the stated equation at 27 settings
      · the video itself is not checked frame by frame
    not right?
```

- *transcript ▸* shows the narration (`narration_md`), the text alternative a video needs.
- **ⓘ** for Manim: *"Written by LearnLoop's model as a short animation script and rendered on this computer in a sealed sandbox, with no network and no access to your files."*

### 6.9 Prebuilt figures (P5)

A prebuilt figure is invisible until it is useful:
- **Instantly, when asked.** A press that would build the same input (*show me* with an empty box, RW5b's *make this explorable*, a lesson step, the chooser's *a figure to explore*) gets the prebuilt figure at once, by input hash (§8.5). The pending line is skipped.
- **One quiet line where it belongs** (recommended, Q22). On its block in the Reader, one dim line, *▸ interactive version*, the same collapsed line a built figure has. It counts against the Reader's cue budget (UX §4.4, S8), so a section never shows more than the budget allows, and the line takes its place in the budget like any LearnLoop cue. It is never shown during a check on your own (SM4), and never as a count, a badge on the plan, or a "N figures ready".
- **In a lesson,** the planned visual is simply there when the teacher's turn shows it.
- **On the Today plan:** nothing. The plan never advertises figures.
- **Opening a prebuilt figure** is the same as opening any figure. It is tier 1 outside an attempt and one hint-equivalent inside one (§11). An unopened prebuilt figure records nothing about the learner.

## 7. The request contract

### 7.1 `FigureRequestV1`

```text
FigureRequestV1
  goal_text        text | null         # the learner's words, or a tutor/teacher goal (author recorded); ≤ 600 chars
  goal_author      learner | tutor | teacher | prefetch    # prefetch: written by the prebuild judge (rev 2, §10b.2)
  anchor           {extraction_id, span_ids[≤40], region?: {span_id, bbox}} | null   # today's request, unchanged
  origin           selection | library | tutor            # RW5a/b, unchanged
                 | show_me                                 # Reader intent box or Ask rail with words
                 | ask                                     # the CA2 Ask panel on practice, feedback, workbench
                 | teacher                                 # a lesson's visual (TE1)
                 | prefetch                                # rev 2: a background prebuild (§10b); never from a client
                 # chat (C2) is reserved, added by C2's own migration
  tiers_allowed    derived on the server, never sent      # rev 2: which tiers the author may choose (§8.4)
  prefetch_decision_id   text | null                       # rev 2: set only by the prefetch service
  host_ref         {question_event_id? | item_id + submission_id? | workbench_session_id?
                    | attempt_id (feedback)? | lesson_id + node_id?}   # references only; each verified on the server
  reading_at       {extraction_id, span_id} | null         # where the learner was (the home when there is no anchor)
  offer_ref        text | null                             # RW5b's, and the tutor answer for a tutor goal
  supersedes_id, revision_note                             # "not right?", unchanged
```

**Validation.** At least one of `goal_text` and `anchor`. A goal alone needs `figures.show_me_enabled`. `goal_author` is never taken from the client: `learner` for the box, `tutor` only when `offer_ref` names a stored tutor answer whose `figure_goal` equals the text (read from the stored output, as `offered_spans` does today, `handlers/figures.py:160-207`), `teacher` only from the lesson service. Every `host_ref` is resolved on the server into a `CallerContext` (`source_retrieval/policy.py:38`); a client never states its policy. *(Rev 2.)* Origin `prefetch` and `goal_author = prefetch` are refused from any RPC. Only the in-process prefetch service builds them, and it calls the figure service directly under `quiet()`.

**The RPC.** One method for every host, `figure.request(FigureRequestV1)`, answering at once with a build job (read with `reader.figure_job`, cancel with `reader.figure_job_cancel`, as today). `reader.figure_request` stays as a thin wrapper for anchor-only requests so RW5a/b's callers and tests are unchanged. Both are pinned desktop-only. Because redesign D's grant is keyed by the origin RPC method, `figure.request` is one grantable action whatever the host.

### 7.2 What the server derives

| Derived | From | Rule |
|---|---|---|
| Caller and policy | `host_ref`, via `derive_policy` | Reader reading, Ask rail, feedback: `reading` or `post_attempt`. An open attempt: `assisted_practice` for that item. A cold administration: `cold_attempt`, refused unless the request carries the take-step token from the converted attempt (§11.3). A lesson: `reading` under caller kind `teacher` (added by TE1, `spec_teacher_v1.md` §9.1) |
| Caller kind | origin | `reader` for selection/show_me/library; `tutor` for tutor; `learner` for ask; `teacher` for teacher. `figure` is not a new caller kind: the figure service calls `find_sources_for_caller` on the requester's behalf |
| Home | anchor, else `reading_at`, else the host | Where the figure lists and expands (§6.2). A practice-host figure with no reading position has no extraction (§14.1) |
| Grounding | §8.3 | `anchor` (the anchor is the source), `retrieved`, or `none` |
| Predictions on | host | Off in a lesson (§6.5); otherwise `figures.predictions_enabled` |
| Tiers allowed *(rev 2)* | switches and runtime | Every tier whose switch is on and whose runtime is ready on this machine:<br>• `spec` always;<br>• `sketch` with `figures.sketch_enabled`;<br>• `js_animation` with `figures.rich_tiers_enabled`, once G-SM14 has passed for this build (a build-time flag);<br>• `manim` with `figures.rich_tiers_enabled`, Manim installed (`manim_runtime`), Linux with `bwrap`, and the standing opt-in given (§9b.3).<br>An unavailable tier is left out of the author's menu, not described as worse |
| Build mode *(rev 2)* | origin | `pressed` for every client origin; `prefetch` for origin `prefetch`. Routes, quiet and caps follow from it (§12) |

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

**Revision 2 pipeline** (P2b):

```
FigureRequestV1 ─► validate, derive caller/policy/tiers_allowed, refuse held-out (SM6)
               ─► grounding (unchanged)
               ─► reuse? input hash (+ tiers_allowed, + tier versions)  ── hit ─► deliver (both versions if built)
               ─► author (figure_author, one call): status spec | sketch | js_animation | manim | unsupported
                     spec / sketch          ─► as rev 1
                     js_animation / manim   ─► rich brief (+ optional fast figure: spec or sketch)
                                               ├─ fast figure ─► verify ─► deliver now
                                               └─ rich job (figure_rich_author, ≤ 2 attempts)
                                                    js   ─► structure ─► model checks (P2 engine) ─► instrument ─► store
                                                    manim─► validate ─► declared-function checks (bwrap) ─► render (bwrap) ─► store mp4
                                                  ─► deliver: "a fuller animation is ready"
               ─► store rows + judgment_ledger (figure_verified; figure_tier with why_this_tier)
```

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

- **The instruction prefers the grammar:** "If the declarative spec can express it, write the spec. Write a sketch only for what it cannot express (a random process, a simulation with state, a geometric construction, a discrete structure), and say why in `why_not_spec`." *(Superseded by revision 2 below. With `figures.rich_tiers_enabled` off and the sketch tier on, P2 ships this V2 contract. Once the rich tiers are on, V3's neutral instruction replaces it, and `why_this_tier` replaces `why_not_spec`.)*
- **The receipt.** The author's status is the tier judgment. Each build appends a `judgment_ledger` row (task `figure_tier`, judge `llm`, verdict `spec | sketch | unsupported`, rationale `why_not_spec` or the unsupported reason, the model and prompt version), beside today's `figure_verified` row. The report shows the tier mix and the `why_not_spec` reasons by kind, so grammar erosion is visible (R3).
- **No second call to decide.** A separate Decider pre-call would add latency and a route for a decision the author is better placed to make (it is the one that knows whether its spec can express the idea). Q1.
- Off, the output contract is RW5b's byte for byte, and `unsupported` keeps meaning "can't draw this yet".

**Revision 2: the model's best medium (owner decision, 2026-10-25).** With `figures.rich_tiers_enabled`, the contract widens again, under a new prompt version (so rev 1's keys are unchanged while the switch is off):

```text
FigureAuthorOutputV3
  status            spec | sketch | js_animation | manim | unsupported
  why_this_tier     one sentence: why this medium explains this idea best      (required for every status but unsupported)
  spec_json         InteractiveFigureSpecV1                                     (status spec; or the fast figure of a rich status)
  sketch_json       SketchProgramV1                                             (status sketch; or the fast figure of a rich status)
  rich              {tier: js_animation | manim,
                     brief: ≤ 1,500 chars — what to build, what to vary, what it must show,
                     demonstrates, assumptions[], source_claims[], claims_planned[]}   (rich statuses)
  unsupported_kind, unsupported_reason                                          (status unsupported)
```

- **The menu is `tiers_allowed`** (§7.2). A tier that isn't available is absent from the menu, not described as worse.
- **The instruction states facts, not a preference.** One neutral sentence per tier, in this order, with no ranking word:
  - *spec*: a declarative figure. Ready in seconds; every number checked by LearnLoop; sliders, predictions and a values table come with it; reusable and accessible.
  - *sketch*: a small sealed program drawing shapes. Ready in tens of seconds; stated claims checked; interactive; summaries rather than thousands of objects.
  - *js_animation*: a full web animation (canvas, WebGL, SVG, DOM, 3-D, its own controls). Takes a few minutes to write; only its declared model functions can be checked, not the drawing; desktop only.
  - *manim*: a narrated video rendered on this computer. Takes a few minutes to write and render; not interactive; only its declared functions can be checked; desktop only.

  Then: "Choose the medium that best explains this idea to this request, and say why in `why_this_tier`. If you choose a rich medium and a spec or sketch can show a useful part of it now, also write that one."
- **The fast figure is optional,** and is the author's judgment (Q20). It is verified and shown exactly as a spec or sketch would be. The rich figure is built from `rich.brief` by the rich job (§8.6).
- **The receipt.** As rev 1, task `figure_tier`, with the verdict widened to five values, `why_this_tier` as the rationale, and the tiers that were on the menu. The report shows:
  - the tier mix;
  - for each tier: opens, *not right?* rate, failures, build latency and help outcomes (P3);
  - `why_this_tier` by kind.

  A tier that does worse for this learner is visible there. Acting on it is the owner's call or a later learned policy (§19), never a prompt preference added quietly (R3).
- **Still one deciding call** (Q1 holds). The rich job's call writes a program from a decided brief; it decides nothing about the tier.

### 8.5 Reuse, versions and repair

- **Reuse key.** `request_hash` (`service.py:473-485`) gains `goal_text` (whitespace-normalized, case kept), `goal_author`, the grounding keys and texts, and the tier versions (`sketch-v1`, the engine digest, §9.3). Origin stays out of the key (`REUSE_ORIGIN`, `:470`), so the same input from the Reader and from a tutor offer is built once.
- **Engine upgrades.** A stored sketch records the engine digest it was verified under. A later engine re-runs the stored sketch's verification (code only, no model call) before showing it; one that now fails shows *couldn't run under this version · rebuild* and is never shown as checked.
- **"Not right?"** works on both tiers unchanged: the note and the earlier spec or program go to the author for a new version that supersedes the old (kept). A runtime error the learner hit prefills the note with the code-written error and the parameter values.
- *(Rev 2.)* **The key gains `tiers_allowed` and the rich tier versions:**
  - `js-anim-v1`, with the frame prelude's digest and the library shelf's digests;
  - `manim-fig-v1`, with the Manim version and the sandbox profile version.

  A prebuild and a later press therefore share a key only when the same tiers were available. Origin and build mode stay out of the key, so a prebuilt figure is reused by the press that would have built it.
- *(Rev 2.)* **"Not right?" on a rich figure** sends the note and the earlier program to `figure_rich_author`, not back to the tier choice. *"try a different kind of figure"* in the note box re-runs the tier choice with the note.
- *(Rev 2.)* **Runtime upgrades:**
  - A new frame prelude or shelf re-runs a stored JS animation's code-only checks and instrumentation (no model call).
  - A new Manim version does not re-render a stored mp4: the video is what was checked. The figure records the version it was rendered with.

### 8.6 The rich job and progressive delivery (rev 2, P2b)

- **Two outputs, one request.** A rich status stores up to two `interactive_figures` rows under one `figure_requests` row:
  - the fast figure (tier `grammar` or `sketch`), shown as soon as it verifies;
  - the rich figure, with `fuller_of_id` naming the fast one, or none.

  Without a fast figure, the request shows the rich-tier progress (§6.8).
- **The rich job** is a durable job on the sidecar's queue, as concept animations are (leases, heartbeats, `report()` cancellation, never left wedged, `concept_animation.py:900-922`). Its steps:
  1. Call `figure_rich_author`: an isolated, tool-free turn, refused if the provider can't isolate (the `figure_author` rule, `routes.py:249-256`). Send the brief, the same source context and goal the author saw, the tier's contract (§9b.1, §9b.3) and, for JS, the library shelf's names and versions.
  2. Check structure. JS: the JSON, sizes, the shelf names, a parse in the P2 engine. Manim: `validate_scene_code` and the pacing lint, reused.
  3. Check the declared claims (§9b.4).
  4. Finish the build. JS: instrument with loop guards (§9b.2). Manim: render under the sandbox (`render_scene`, reused), remux and store (`_store_video`'s store, reused).
  5. Store the row, deliver the cue, and write the ledger rows.
- **Attempts.** At most `MAX_RICH_ATTEMPTS` calls (2, `keep`: rev 1's author cap carried to the rich call). The second call carries what the first got wrong, in code's words: validator violations, a failed claim with its values, render stderr (the concept pipeline's repair pattern), or a frame load error the desktop reported. Manim's separate pacing round counts as that second attempt; there is no third.
- **The two halves are independent.** The fast figure never waits for the rich one, and a failed rich job never hides the fast one. Cancelling, on the `◌` line or the pending line, cancels only the rich job.
- **Origin of the spawned job.** It is created inside the pressed `figure.request`, so it carries `unit_origin()` and `unit_token()` (`plan_fallback.py:524-560`). Two cases:
  - **Granted press:** the job uses the grant within this session.
  - **No grant:** the job waits for the plan, and the frame line says so (§6.8). The job never makes a new offer: the learner is asked at most once, on the press.
- **Prebuilds** run both halves under `quiet()` (§10b).

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
| C. Model JS in a sandboxed iframe (`sandbox="allow-scripts"`, opaque origin, own CSP), JIT speed | Fast; DOM drawing | The model's code becomes a JS realm inside the app's webview: the boundary is the webview's iframe and IPC isolation, which Tauri itself warns about on Linux, and every DOM API is attack surface. Headless verification would need a browser in the sidecar. Drawn ≠ verified | Rejected **for the sketch tier.** *(Rev 2, owner decision: adopted as the separate `js_animation` tier (§9b.2), for the ideas a sealed display list can't carry. Its boundary is the frame plus the gates in §9b.5; it is labelled with weaker checks, and the sketch tier keeps option A)* |
| D. Python under bubblewrap (the manim pattern) | Exists | Not a sandbox off Linux, needs a consent click (`handlers/animation.py:109-120`), a subprocess per frame is not interactive | Rejected **for the sketch tier.** *(Rev 2: reused as the separate `manim` tier for narrated video, Linux only, §9b.3)* |

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

The manim route asks for consent because its own boundary "is NOT a sandbox" (`concept_animation.py:9-20`). The sketch tier's boundary is a sealed interpreter with nothing to reach (§9.3–9.4). A click would protect nothing the runtime doesn't, and W3 forbids confirmation dialogs on safe actions. The frame says how the sketch runs, on demand (ⓘ). Q3. *(Rev 2: the same reasoning covers `js_animation`. The Manim tier takes one standing opt-in, §9b.3.)*

## 9b. The rich tiers (rev 2, P2b)

### 9b.1 What a rich figure is

Both rich tiers share the figure's frame and label fields with the spec and the sketch: `demonstrates`, `assumptions` and `source_claims`, all quote-verified as today. Each adds its own program:

```text
JsAnimationV1                                       (spec_version "js-anim-v1", stored in spec_json)
  html            body markup text (no <script src>, no <link>, no <base>, no <iframe>, no <form>)
  css             text
  js              module text; the program's own loop, drawing and controls
  libraries       [name] from the shelf (§9b.2)            # inlined by code, never fetched
  model           optional pure JS module text: functions of the parameters, no DOM, no clock,
                  no randomness except the host's seeded rand(); exported names only
  model_exports   [{name, args: [name], shape: scalar | series | pairs}]
  claims          [Claim over model exports]               # the §9.5 kinds: equals, follows, invariant, distribution
  probes          [{name, label}]                          # model exports the host may ask the frame for (values table)
  alt_text        ≤ MAX_TEXT: what the animation shows, for a screen reader and the "values" view
  size            js + html + css ≤ JS_MAX_PROGRAM_BYTES; model ≤ SKETCH_MAX_SOURCE_BYTES

ManimFigureV1                                        (spec_version "manim-fig-v1", stored in spec_json)
  scene_code, scene_class, title, narration_md      # the ManimAnimation contract, reused
  functions       [{name, args: [name], shape}]     # top-level pure defs in scene_code (math/numpy only)
  claims          [Claim over functions]
  plotted_from    [{function, call_site}]           # where the scene draws from a declared function (AST-checked)
```

The `js` program may use any web API the frame allows: canvas, WebGL, SVG, DOM, `requestAnimationFrame`, pointer and key events inside the frame, and workers (none, because of CSP, §9b.2). Its controls are its own. The host adds only the chrome outside the frame (§6.8).

### 9b.2 `js_animation`: the frame

**Serving.** A new custom protocol `llfig://` (`http://llfig.localhost` on Windows) is registered beside `llpdf` and `llmedia` (`src-tauri/src/main.rs:204-220`). It serves exactly one document per `(figure_id, content_sha256)`, and refuses a hash that doesn't match the stored row. The document is assembled by code, in a fixed order:
1. the **host prelude** (below);
2. the shelf libraries the program names, inlined from tracked, digest-pinned files;
3. the `model` module;
4. the program's `html`, `css` and **instrumented** `js`.

Nothing is fetched by the document: there are no subresources at all.

**The response headers** (every directive `keep`, as a security boundary):

```
Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';
  img-src data: blob:; font-src data:; media-src 'none'; connect-src 'none'; worker-src 'none';
  frame-src 'none'; child-src 'none'; form-action 'none'; base-uri 'none'; sandbox allow-scripts
Cross-Origin-Resource-Policy: same-origin
Cache-Control: no-store
```

**The element.** `<iframe sandbox="allow-scripts" src="llfig://…" referrerpolicy="no-referrer" loading="lazy">`. It has **`allow-scripts` only**, which means:
- no `allow-same-origin`, so the origin is opaque: no cookies, storage, IndexedDB or access to `parent`;
- no `allow-forms`, `allow-popups`, `allow-top-navigation`, `allow-modals` or `allow-downloads`;
- no `allowfullscreen`.

The page's own CSP gains `llfig: http://llfig.localhost` in `frame-src`, and only there. Because the page's `frame-src` also governs where a frame may later navigate, the frame cannot navigate itself to a web address. The one exception, the existing YouTube embed origin, is a residual in §9b.5.

**The host channel** is `postMessage` only. The host checks `event.source === frame.contentWindow` and that the origin is `"null"`, and accepts a closed set of message kinds, each schema-validated:
- frame → host: `ready`, `resize {height}` (clamped to `JS_MAX_FRAME_HEIGHT`), `heartbeat`, `guard_tripped {where}`, `error {message ≤ MAX_TEXT}`, `probe_answer {name, args, value}`;
- host → frame: `play`, `pause`, `reduced_motion {on}`, `probe {name, args}`.

Nothing else is read. No message carries vault data, learner data or secrets: the frame is only ever given its own program and the parameter values it asks to display.

**The prelude** is code-owned and digest-pinned. Being inside the frame, it is a convenience layer, not the boundary:
- **Start paused.** It holds `requestAnimationFrame`, `setTimeout` and `setInterval` callbacks until the learner's first pointer or key event inside the frame, or the host's `play` (SM10). With reduced motion on, `play` steps one frame per press, as D39 requires.
- **Loop guards** (below), the heartbeat and the probe responder.
- **Defense in depth** behind CSP: it deletes `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `RTCPeerConnection`, `navigator.sendBeacon` and `window.open`, and refuses single allocations over `JS_MAX_ALLOC_BYTES`.

**Loop guards and the crash marker.** WebKitGTK runs the frame on the Reader's main thread (§4.4), so a hang can't be killed from outside. Three things handle it:
- **Instrumentation.** Before storing, code instruments the program: a guard call at the top of every loop body, every function body and every scheduled callback. It is written with a vendored JS parser (acorn, MIT) running inside P2's sealed QuickJS engine in the sidecar, so no model code runs in Python and nothing new is trusted. A guard throws once one task has run past `JS_TASK_MS`. The prelude catches it, stops scheduling and reports `guard_tripped`. The frame shows *paused — this animation was too slow here*.
- **Watchdog.** The host's heartbeat watchdog removes a frame that misses `JS_WATCHDOG_MS` of heartbeats once the thread is free again. At most one JS animation runs at a time; others are paused and unloaded when scrolled away.
- **Crash marker.** The host writes a `started` marker before a frame first runs and `ok` after its first heartbeats. A figure found `started` without `ok` after a restart (the web process died, or the app was killed) is shown as *this animation stopped LearnLoop last time · run it again ▸*, and is never auto-run.

What guards can't bound (one huge built-in call, a catastrophic regular expression, a GPU hang) is a stated residual (§9b.5).

**The library shelf** (Q19). Tracked, pinned, digest-checked JS files under `apps/learnloop-tauri/` assets, inlined on demand:
- KaTeX (already a dependency, `package.json:20`), for maths labels;
- d3, for scales, shapes and transitions;
- three.js, for 3-D and WebGL.

All three are MIT or ISC, and their licence texts go in the assets' NOTICE. A program names what it uses. The shelf grows only by owner request, not by model request. Its sizes are what G8's per-file limit allows (each well under 5 MB).

**Accessibility.** The *values as a table* toggle shows the declared probes at the current parameters (asked of the frame through `probe`), or else the `alt_text`. The frame's own controls must be keyboard-reachable; G-SM24 checks that the frame takes focus and that `esc` returns it.

### 9b.3 `manim`: the existing pipeline, reused

- **Authoring.** `figure_rich_author` writes a `ManimFigureV1`. Its scene part is the `ManimAnimation` contract and scaffold from `content/authoring/ai_contracts.py`, reused. Its context is the figure's (source passages, goal, brief), not a concept's.
- **Checks, render and store are the concept pipeline's code, called as a library:**
  - `validate_scene_code` and the pacing lint, with `[animation]`'s pacing band and `latex_enabled`;
  - `render_scene` under bubblewrap, at `[animation] quality`;
  - the content-addressed store under `media/animations/`;
  - `llmedia://` playback through the same blob-URL player (`ConceptAnimationSection.tsx:60-130`, lifted into a shared component).

  Nothing is rebuilt. The figure row records `media_file_name` and the Manim version.
- **Hardening for figure renders** (and, recommended, for the inspector's too, Q17):
  - `bwrap --cap-drop ALL --disable-userns`, added to `_sandboxed_command`'s flags;
  - the render runs in a `systemd-run --user --scope -p MemoryMax=RENDER_MEMORY_MAX -p MemorySwapMax=0 -p CPUQuota=RENDER_CPU_QUOTA` scope when `systemd-run` exists, as the owner's test-run rule does for the same oomd reason, else under `prlimit --as`;
  - background renders also run at `nice 19` and `ionice -c3`;
  - the wall-clock cap is `[animation] timeout_seconds`.
- **Linux only.** Off Linux, `render_scene` runs unsandboxed (`:606-616`), so the `manim` tier is never on the author's menu there. The concept inspector keeps its per-run click off Linux.
- **Consent: a standing opt-in replaces the per-run click** for figures on Linux with `bwrap` (recommended, Q17). It is asked once, inline, the first time the author's menu would include Manim (on a press, never in the background):
  - *"LearnLoop can make narrated animations by running AI-written animation code in a sealed sandbox on this computer (no network, no access to your files) · allow · not now"*.
  - *allow* writes `figures.manim_opt_in = "standing"` with the date (also settable in settings, and revocable there).
  - *not now* leaves Manim off the menu and doesn't ask again; settings can turn it on later. No re-ask interval exists to tune.

  Prebuilds use Manim only after the opt-in. Why standing and not none, when `js_animation` takes none: Manim is native CPython, numpy and ffmpeg facing the host kernel, while the frame is the browser's sandbox, built for hostile code. One explicit opt-in matches that difference. A per-run click would only make prebuilding impossible.

### 9b.4 Checks, proportionate per tier

| Tier | What can be checked | How | Label when it passes | When there's nothing to check |
|---|---|---|---|---|
| `spec` | Every number (RW5a/b) | Unchanged | *checked by LearnLoop:* property lines | — |
| `sketch` | Probes, bindings, claims (§9.5) | Unchanged | Per element | *nothing in it checked* |
| `js_animation` | The declared `model` exports against `claims` | **Headless, in the sidecar:** the `model` module runs in P2's sealed QuickJS engine on rev 1's grid (§9.5 steps 1–3 and 5, same tolerances). **Then at first open, in the frame:** the host asks the frame for the same exports at every grid point through `probe` (≤ 81 messages), and compares within `CLAIM_REL_TOL` (JIT and interpreter `Math` may differ in the last bits). A mismatch hides the figure (*this animation doesn't match what was checked · not right?*) | *checked by LearnLoop:* one line per claim, naming the export and the stated equation, then *the drawing itself is not checked* | *AI-written animation · not checked* |
| `manim` | The declared pure `functions` against `claims` | **Headless, in the same bubblewrap profile:** code extracts, by AST, only the declared top-level `def`s and the module constants they read, with imports limited to `math` and `numpy`. It runs them in a separate sandboxed `python` (manim never imported) on the grid, and compares with the grammar oracle. A function that needs anything else is **not checkable**: its claim is dropped from the check list, not failed. `plotted_from` is AST-checked (the declared function is the argument of a plot call) | one line per claim, *the curve is drawn from f, which matches …*, then *the video itself is not checked frame by frame* | *AI-made video · not checked* |

- **The rule rev 1 kept, kept for every tier:** a figure whose own stated claim **fails** after its second attempt is not shown (*couldn't build a reliable version of this*), as RW5a and Q4 rule. *Not checked* is only for a figure that states nothing checkable.
- **Never "matches the book"** on any tier (N-a).
- **Label wording rules.** The schema walk over model-written text that stops labels impersonating a check (§9.5) covers every model-written string in a rich figure: `demonstrates`, `assumptions`, `alt_text`, `narration_md`, and, for JS, the string literals in `html` and `js`. Text inside the frame is the model's voice by construction. The badge and the check lines are outside it.

### 9b.5 Threat model, rich tiers

The adversary is the same as §9.4: the author's output, possibly following text injected in a book. The learner is not the adversary.

| Asset | Harm | Path | Control | Residual |
|---|---|---|---|---|
| Vault, notes, learner data | Read or tamper | Frame → Tauri IPC (`window.__TAURI_INTERNALS__`, `window.ipc`, WebKit script message handlers, `fetch` to `ipc://` / `http://ipc.localhost`) | Opaque origin; CSP `connect-src 'none'`; the frame holds no data. **G-SM14 extended:** in the real Linux webview, a hostile corpus tries each IPC path and the opener and dialog plugins from inside the frame, and every one must fail. The shell's command handlers also refuse an invoke whose requesting frame URL isn't the app's own document. **If any path succeeds, `js_animation` stays off** (a build flag) until the frame moves into a separate child webview with no capability | A WebKit escape. Not realistic for model output (proportionate bar) |
| Vault, notes, learner data | Read or tamper | Manim scene → the filesystem | bubblewrap: no home, no vault, `/tmp` as tmpfs, read-only system mounts, the scratch directory only, `--cap-drop ALL --disable-userns` | A kernel exploit from native code. Hence the standing opt-in (§9b.3) |
| Keys, plan token | Exfiltrate | Network from the frame or the render | CSP `connect-src 'none'`, no forms, no popups, `frame-src` blocks navigating to the web; bwrap `--unshare-all` (no network). Neither runtime is ever given a secret | **Beacons without secrets:** WebRTC's STUN traffic, which CSP doesn't govern in WebKit (G-SM25 asserts `RTCPeerConnection` is absent in the webview; WebKitGTK ships WebRTC off unless enabled); DNS prefetch hints; a navigation to the allowed YouTube embed origin. Each could at most announce *that* a figure was opened. No learner data is in the frame to send |
| Money | Spend | The frame or a scene triggering model calls | Neither can call anything. Builds are pressed or quiet, capped (§12.2) | — |
| The learner's trust | A misleading figure looking checked | A rich figure drawing something other than what was checked | Check lines scoped to the export or function; *the drawing itself is not checked* always; a failed claim is not shown; the in-frame probe agreement at first open; *not checked against the book* always | A correct-by-its-claims animation of a wrong idea, labelled AI-written, with *not right?* |
| UI integrity | A fake LearnLoop panel ("sign in again") inside the frame | Arbitrary DOM in the frame | Code-owned chrome outside the frame; a fixed border; height capped; never full-screen or overlaid; no forms, popups or navigation, so typed text can't leave | A convincing fake inside a labelled AI frame. Its "submit" goes nowhere |
| The machine | Hang, memory or GPU blow-up | Loops, huge allocations, shaders; renders | Loop guards, the watchdog, one frame at a time, the allocation cap, the crash marker; renders in a memory- and CPU-capped scope, one at a time, niced in the background | A stall or a web-process crash that WebKit restarts, never re-run automatically |
| Supply chain | Tampered shelf, prelude or parser | The tracked JS files | Pinned digests, refused on mismatch, licences recorded | — |

**Review.** The frame and the Manim hardening get their own adversarial review before P2b merges (Codex, or Opus when Codex is out), against a **hostile rich-figure corpus**:
- every IPC path above, `parent`/`top` access, `postMessage` spoofing toward the host;
- navigation to `https:`, `javascript:` and `data:`;
- form and popup attempts;
- allocation, loop, recursion and regex bombs;
- a WebGL shader loop;
- a text imitation of the badge;
- for Manim: path escapes, `/proc` probing, network attempts, fork bombs, and memory over the cap.

The reviewer is asked: "find a way for a rich figure to reach anything outside its frame or sandbox, to send anything off the machine, or to make LearnLoop's chrome claim a check that didn't run."

## 10. Fit with the rest of LearnLoop

### 10.1 The Reader is the surface

Figures land inline under their passage (or under the passage the learner was reading), one expanded at a time, at the text column's measure (UX §4.7, S9). A built figure leaves the learner's own `◇▸` margin mark, outside the cue budget (UX §4.4, S8), because the learner asked for it.

### 10.2 Figures follow the section (P4, after C0a)

A figure is anchored to spans, so it has a section (`extraction_sections`). When the learner reads a section in another book that `reader.correspondents` (C0a; `spec_deliverable_curriculum_v1.md` §6.4) says corresponds to it, the Guide's *also in your books* entry (CA5) can list *an interactive version from Strang §6.4 ▸*. This is a read: figures joined through their anchor's section to the correspondents' sections, filtered by `figure_withheld` (`service.py:246`). Nothing is copied. Opening it shows the figure in place with its home named (*from your reading of Strang §6.4*). Q8 asks whether kept figures should also be `source_objects` (`artifact`) rows; recommended no.

### 10.3 The tutor requests, the learner presses

D28 holds: the tutor's `figure_goal` (§6.3) is a request; the press builds. The tutor never builds. ~~Nothing is pre-built for an offer (SM9).~~ *(Rev 2.)* An offer's figure may already exist because the prefetch service built it quietly (§10b). The press still decides that the learner sees it.

### 10.4 The teacher uses figures as manipulatives (P4, with TE1)

- **Doctrine.** The row "Instruments over description" (`spec_teacher_v1.md` §2.1) becomes concrete: in a discovery step (principle ii, motivated discovery), the teacher hands the learner one parameter and asks what they had to do (§6.5).
- **The latent state picks the parameter, in the goal.** The teacher reads the brief (AD readiness, misconceptions, last lessons) and writes the goal: which parameter to hand over, which to fix, what to watch. The figure author never sees learner state; the teacher's words carry what it decided. This keeps figures reusable content and keeps state where it is already governed.
- **Evidence.** Predictions are `lesson_turns` (formative). A posed check is lesson-check evidence with the learned weight (§12.1 of the teacher spec). The figure's own predictions are off in lessons.
- **Planned visuals (rev 2, with TE1).** `write_plan`'s outline nodes may carry `visual: FigureRequestV1` (origin `teacher`, the goal written from the brief). Once the plan is accepted, the prefetch service builds the visuals of nodes the learner hasn't reached yet, in plan order (§10b.2), while the learner works the earlier steps. The turn that reaches a node refers to its planned visual by node id, so it carries the identical request and hits the same input hash. A rich medium chosen for a later step is usually ready by then.
- **Adaptive difficulty.** No figure-level coupling (§4.5 item 4). If TE1's receipts later show that lessons with manipulatives resolve delayed checks differently, that belongs in the teacher's own measurement (its §21), not in the figure service.

### 10.5 MCP chat (C2)

C2 owns chat figures. Its spec already lets hosts generate their own visuals (`spec_mcp_frontend_v1.md` §9.2) and routes reproducible ones through RW5 (§9.3). RW5d's contribution is the contract: a C2 `show_me` tool sends `FigureRequestV1` with origin `chat` (C2's own migration adds the value) and returns the spec or the sketch program with its verification report for an instrumented MCP App component. §9.3's sentence "never execute arbitrary model code in the learning service" is read as allowing the sealed verifier, which executes no host-language code and imports nothing; Q13 asks the owner to confirm, with a one-line amendment to that spec. *(Rev 2.)* C2 may return a rich figure too:
- a Manim mp4 as media;
- a JS animation's program, for an MCP App host to render in its own sandbox. C2 decides whether hosts get it.

## 10b. Ahead of need: proactive generation (rev 2, P5)

The owner asked whether LearnLoop could build rich figures before they're asked for, since they take minutes. It can, where LearnLoop already knows what comes next. The service is `figures/prefetch.py`, a composition layer; nothing imports it back.

### 10b.1 The loop

```
trigger (plan built · section progress · RW5b offer · lesson plan accepted · gap opened)
   └─► candidates (code: what's next; judge: which blocks, with what goal)        quiet, plan only
         └─► filter (exam/held-out, item's own blocks, already built, switches)    code
               └─► decide per candidate: posterior EU, Thompson-sampled             code, learned (§10b.3)
                     └─► log decision (built or not, propensity)                     RAW_LEDGER
                           └─► queue builds under caps and the power condition      quiet, plan only
                                 └─► outcome at the horizon: opened / asked / neither (§10b.5)
```

### 10b.2 Triggers and candidates

| Trigger | Fires | Candidates | Goal |
|---|---|---|---|
| **The plan is built** (DL1/RW7b) | After the day's plan is stored | The plan's reading block's section (`next_reading_target`; RW7b's path step when it is in play). The read is of the stored plan; the plan never calls into figures | From the section judge (below) |
| **Section progress** | `reader.mark_section_progress` (the keep-ahead hook, `handlers/reader.py:1749`) | The next section the path or book order gives after this one | From the section judge |
| **RW5b's offers** | When the organizer or the tutor stores `explorable: yes` on a cited block (`figure_admission.py:110-150`) | That block | None: the request is anchor-only, the same input the press *make this explorable* sends |
| **A lesson plan is accepted** (TE1) | `write_plan` is accepted | Planned visuals of nodes not yet reached (§10.4) | The teacher's |
| **A gap or misconception opens** | The diagnoser or learner-text gaps store an open gap on an LO that tomorrow's plan or an open lesson touches | One help figure per open gap, anchored to a non-exam passage that treats the LO (`find_sources_for_caller`, caller kind `reader`, policy `reading`) | From the gap judge: the gap's **statement** only (Q23) |

**The section judge** (`figure_prefetch_judge`, a listwise task, plan only, background only, never offered). Input: one section's blocks, with exam and model-withheld roles removed and no learner data. Output: at most `PREFETCH_SECTION_CANDIDATES` blocks, each with:
- a `goal`, or none for anchor-only;
- `p_open_content`, the judge's probability that a reader of this section would want to explore this block. This is content-side, LP §3.0 source 3: the frontier model reading content, never learner data.

The output is cached by the section's content hash and the prompt version, so each section is judged once. For blocks the judge marks anchor-only, the prebuild is exactly the request a later *show me* with an empty box sends, so the reuse is exact.

**The gap judge** is the same task in gap mode. Input: the gap's statement, the LO and the chosen passage. Output: a goal (`goal_author = prefetch`) and `p_open_content`. It never sees an attempt, an item stem, a key or a rubric.

**Filters (code, before any call and again before the build).**
- `exam_material(...)` and `spans_withheld` on every span (SM6).
- No block of an item that is the subject of an open or cold administration, and no passage that `assisted_practice` would withhold for an item in tomorrow's plan.
- Not already built under the current key.
- `figures.enabled`, `figures.show_me_enabled` (for goals), `figures.prefetch_enabled`.

### 10b.3 The decision: learned, not a threshold

For each candidate `i`, build iff the sampled expected utility is positive:

```
EU_i = P(open_i | built, cue) · W_tier(i) · u.minute  −  C_i
```

- **`P(open_i | built, cue)`** is a logistic model whose coefficients are latent with seeded priors, updated by assumed-density filtering as AD updates its effects (AD §5.6; LP §3.1):
  - `logit P = β_kind[trigger] + α · logit(p_open_content_i) + β_src[source]`;
  - `β_kind` is partially pooled across the five trigger kinds, and its pooling scale is a posterior over an a-priori grid (AD's `ad_hyper_v1` mechanism);
  - `β_src` is a per-source offset, shrunk to 0.
- **Priors** (registered, LP §2 fields):

  | Coefficient | Prior | `prior_basis` | Rationale |
  |---|---|---|---|
  | `α` | centre 1, sd 1 | `llm_content` | The identity map: believe the judge's stated probability until the data say otherwise |
  | `β_kind` | centre 0, sd 1.5 logits | `legacy` | No population data exist, so this is LP §3.0's widest un-sourced prior, listed as debt |
  | `β_src` | centre 0 | — | The scale is the grid posterior |

- **`W_tier(i)`** is the wait a prebuild saves, in learner minutes: the posterior mean build latency of the tier the request would most likely take. It comes from the report's measured pressed builds (`figure_requests` → figure `created_at`), per tier, as a log-normal with the measured mean and variance. A tier with no measured pressed build has no estimate, so its candidates wait (structural: no data, no prebuild). The tier is the author's to choose, so `W` uses the tier mix measured for this trigger kind. It is data, not a constant.
- **`u.minute`** is the existing cost of one learner minute (LP §6; `action_loss:DEFAULT_INTERVENTION_MINUTES`). It is an owner preference, not fitted.
- **`C_i`, the cost**, is what a background build can take from foreground use. On the plan the money is zero; the scarce thing is the plan's usage window. The cost is:

  ```
  C_i = P(usage-limit pause before the window resets | plan load today + this build's expected tokens)
        · E[foreground minutes blocked by a pause] · u.minute
  ```

  - **The pause probability** is a logistic in the day's plan load, learned from the plan's own usage-limit history. Two corrections to what exists:
    - The plan session keeps **only the latest pause** in `state.json` (`chatgpt_plan/session.py:127-170`), so P5 appends each pause it observes (when it was hit, when it reset) to `plan_usage_pauses` (§13.2b).
    - Plan tokens are recorded per agent run where the provider reports them (`ai/usage.py`; `agent_runs.actual_*_tokens`, migration 131), but not for every route. So the load is the day's plan **requests**, plus tokens where known.

    Its prior has centre `logit P = −3` and a 1.5-logit slope per standardized unit of load, both 2 logits wide, basis `legacy` (debt).
  - **The blocked minutes** are measured: pressed requests refused during past pauses, times their measured latency.
  - Electricity is not costed, because the power condition (§10b.4) makes background compute happen only on mains.
- **Thompson sampling.** Draw one coefficient sample from the posterior, decide with it, and log the propensity (the share of 64 posterior draws, a Monte Carlo resolution and so `keep`, that would build). Deciding by posterior sampling explores where the model is unsure, with no ε or margin. The propensity makes off-policy estimates possible later.
- **Ordering under the caps.** Candidates that pass are queued in order of sampled `EU`. The `keep` caps (§10b.4) cut the queue; they never admit a candidate the rule refused.

**Why this and not a rule.** A rule such as "prebuild the next section's equations" would be a made-up policy. Here the content model says which blocks are worth a figure, the learner's opens say how much to believe it, and the plan's own pauses say what speculation costs. All three move with data, and the report shows them (§10b.6).

### 10b.4 Where and when it runs (guardrails, all `keep`)

- **Desktop sidecar only.** It runs in the process that serves the desktop app at the hub (carson; or a laptop running its own vault). Never in the phone host or the MCP host (`spec_storage_sync_v1.md`; S6's remote desktop mode renders at the hub).
- **Mains power only.** A small `power_state()` reader:
  - Linux: `/sys/class/power_supply/*`. A battery reporting `Discharging`, or no `Mains`/`USB` supply `online = 1` when a battery exists, means **on battery**.
  - Linux: power-profiles-daemon's active profile (`powerprofilesctl get` or its D-Bus property). `power-saver` counts as **on battery**.
  - macOS and Windows: `pmset -g batt` and `GetSystemPowerStatus`.
  - A machine with no battery is on mains.
  - Unknown counts as **on battery**: fail closed.

  On battery, nothing new starts, and a running prebuild is cancelled at its next heartbeat. Pressed builds are unaffected: the learner asked.
- **Yield to the learner.** A prebuild never starts while a pressed figure, a lesson turn, a tutor answer or a grading call is in flight. A pressed request arriving mid-prebuild pauses the prebuild queue at its next heartbeat. A render already running continues, niced.
- **Caps**, each a guardrail, not a learned number:
  - `figures.prefetch.max_daily_builds` (10): plan headroom spent on speculation per day; a lesson alone is 15–25 calls;
  - `figures.prefetch.max_daily_render_minutes` (30): wall-clock of background Manim renders per day;
  - `PREFETCH_CONCURRENT_BUILDS` (1) and `RENDER_CONCURRENCY` (1, pressed and background together): one at a time, given the oomd history.
- **Plan only, quiet.** All background work runs inside `plan_fallback.quiet()`: the judge, the author, the rich author, the gap passage search. No offer is made and no grant is honoured; plan down means wait. Nothing is metered, so `figures.max_daily_cost_usd` is untouched.
- **Never** for exam or held-out material (A8), never during a check on your own's administration window for the item concerned, and never when `figures.prefetch_enabled = false` (recommended default **on**, Q21).

### 10b.5 Outcomes and horizons

Each decision row closes once, at its **horizon**, which is structural (the moment the candidate stops being "next"), not a duration:
- the plan's day ends (plan trigger);
- the section is marked read (section trigger);
- the lesson closes (lesson trigger);
- the hit's thread is closed or the session ends (offer trigger);
- the gap closes, or the next plan is built (gap trigger).

The outcome is one of:
- `opened` (a built figure was opened);
- `asked` (no figure was built, and the learner pressed for one on this input);
- `neither`;
- `void` (the input became withheld, or the switch went off).

Only built rows inform `P(open | built, cue)`. `asked` rows on unbuilt candidates are logged as evidence about demand without the cue; they are a separate quantity, reported but not used in the decision (R11). A prebuild nobody opened before its horizon is kept as an ordinary figure. It is reused whenever its input recurs, and costs nothing more.

### 10b.6 What the report shows

`learnloop reader report --json` gains `prefetch`:
- decisions by trigger, built and not;
- opens and asks by trigger;
- the posterior of `α` and `β_kind` (prior → posterior contraction, LP §3.3);
- the measured `W` by tier;
- usage-limit pauses with and without prebuilds in the preceding window;
- builds skipped by the power condition and by caps.

These are glass-box details on demand. The learner never sees counts (UX U12).

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

### 11.4b Every tier, every build mode (rev 2)

§11.1–11.4 apply unchanged to `js_animation` and `manim` figures, and to prebuilt figures:
- **Opened during an attempt** = one hint-equivalent, once per figure per attempt. A prebuilt figure's quiet line is not an opening. For a Manim figure, opening means expanding its frame; playing adds nothing more. *◂ the quick version* and *open ▸* (the fuller version) are one figure for this count.
- **Cold.** On a check on your own, all of these are hidden (SM4, §11.3):
  - prebuilt lines;
  - *a fuller animation is ready* cues;
  - rich frames, and running JS animations are unloaded.

  The take step converts the attempt before any figure appears.
- **The reveal check** reads every model-written string of a rich figure: the fields named in §9b.4's wording rule, plus Manim's `Text`/`MathTex` arguments, found by AST. A JS animation's `html` and `js` string literals are read the same way.
- **The diagnoser's trace** (`+figures-v1`) adds the figure's tier and `demonstrates`. It never adds the program.
- **The chooser's `explore_figure`** may serve a prebuilt figure, which is the point of gap prebuilds. It is still offered only when its precondition holds (§11.4), and never cold.
- **Never seen by the grader** (SM5). Unopened prebuilt figures record nothing about the learner. A prefetch decision row is about content and opening behaviour, never evidence.

### 11.5 What never happens

No figure event writes `grading_evidence`, `facet_recall_state`, `facet_capability_evidence`, `probe_observations`, a certification, FSRS or AD state. *(Rev 2.)* Nor does any prefetch decision or outcome. The prefetch model reads tier-1 engagement only (opens, presses), which W1 permits for "suggestions, display". The `evidence-never-reads-figures` import contract (`figures/__init__.py:21-23`) stays; P3's hint-equivalent fold goes through the hint service's existing submit fold, which already writes `hints_used` and does not import `learnloop.figures`.

## 12. Routes, spend, privacy

### 12.1 Routes

| Route | Use | New? |
|---|---|---|
| `figure_author` | Both tiers; grammar and sketch prompts are separate prompt versions | No (wider output contract, P2) |
| `source_rerank` and T6's rewrite/embedding routes | Grounding through `find_sources(verify=True)` | No |
| The Reader tutor's route | `figure_goal` in the answer it already writes | No (a field, P1) |
| `hint_chooser` | The `explore_figure` option | No (an option, P3) |
| The teacher's route | `visual` requests | TE1's |
| `figure_rich_author` *(rev 2)* | Writes the `js_animation` or `manim` program from the author's brief; repairs | **New AITask** (P2b). An isolated, tool-free turn, refused if the provider can't isolate. Its default serving route is the plan's coding-strength tier (`keep`: an operational route choice, revisited after the P2b owner checkpoint). Added to `METERED_PRICE_SETTINGS` as `figures.price_per_million` (Q16) |
| `figure_prefetch_judge` *(rev 2)* | The section and gap judges (§10b.2) | **New AITask** (P5). A listwise task. Background only; never offered OpenRouter; never metered |
| `animation` | The concept inspector's own animations | Unchanged; figures don't use it (Q16) |

### 12.2 Caps (money and time)

- Two author attempts per request, one physical request each, as today. `figures.max_daily_cost_usd` (1.0) covers both tiers on a metered route; a sketch's larger output is metered like any other. The call cap per request (`MAX_AUTHOR_ATTEMPTS`) and the token cap (`SpendCaps.max_total_tokens`, `routes.py:257-258`) are unchanged.
- Grounding uses the sources service's own caps.
- Sketch runtime caps are `keep` guardrails (§15).
- *(Rev 2.)* **Pressed rich builds:**
  - one author call plus at most `MAX_RICH_ATTEMPTS` rich calls;
  - metered only when a granted press routes to OpenRouter, inside the same `figures.max_daily_cost_usd` envelope, which is re-read before every physical request by `FiguresGate` (`figure_admission.py:174`);
  - renders: one at a time, memory- and CPU-capped (§9b.3).
- *(Rev 2.)* **Background prebuilds:** plan only (no money), capped by `figures.prefetch.max_daily_builds` and `max_daily_render_minutes`, one at a time, on mains only (§10b.4).

### 12.3 T1

All routes plan-first. A pressed `figure.request` that meets a plan-down route gets UX §4.0's line, *ChatGPT plan isn't answering right now · use OpenRouter for this figure? ▸*, keyed by `figure.request`; for a lesson, by the lesson's turn method. OpenRouter is offered only once `figures.price_per_million` is set (`plan_fallback.py:78`). ~~Background work: none (no prefetch, no pre-build for offers, no rebuild on engine upgrade beyond code-only re-verification).~~ **Rev 2 (owner, 2026-10-25):**

| Work | Origin | Plan down |
|---|---|---|
| The pressed author call | `figure.request` | UX §4.0's offer, as rev 1 |
| The rich job spawned by a press | `unit_origin()` = `figure.request` | Granted this session: OpenRouter. Otherwise it waits, and the frame line says so; no new offer |
| Every prebuild: judge, author, rich author, gap passage search | none (`quiet()`) | Waits; dropped at its horizon. Never an offer, never a grant |
| Lesson planned visuals | none: quiet, **not** the lesson's grant (Q25) | Wait. If the step arrives first, the lesson turn builds the visual itself under the lesson's origin, as rev 1 |
| Engine, prelude or shelf upgrade re-checks | code only | — |


### 12.4 Privacy

Sent to the author: source text (the anchor and neighbours, or retrieved passages), the crop when a figure or region is selected, the goal text and who wrote it, and for "not right?" the earlier version and the note. Never: learner history, state, attempts, the item's stem, key or rubric. The disclosure row for `figure_author` gains the goal text. Nothing leaves the machine from a sketch's runtime. *(Rev 2.)*
- **`figure_rich_author`** receives what the author received, plus the brief. It gets its own disclosure row with the same text.
- **`figure_prefetch_judge`** receives section text only, except in gap mode.
- **In gap mode,** the judge and then the author receive **the gap's or misconception's statement**, a sentence the diagnoser wrote about the learner. It is sent on the plan only, and disclosed as *"what LearnLoop thinks you're unsure of, in one sentence, to prepare a figure"* (Q23). No attempt text, stem, key or rubric is sent.
- **The runtimes.** Nothing leaves the machine from a JS frame (CSP, §9b.2) or a Manim render (no network namespace).

## 13. Data model

### 13.1 One migration in P1 (next free number at landing; 223 at the earliest, likely later)

Main's head is 220; LP claim fixes hold 221 and C0a 222. Allocate at implementation time (`ls migrations/` on main and on the in-flight branches). *(Rev 2, verified on `a58dae89f`.)*
- Main's head is now `221_learner_claim_application_point.sql`.
- C0a's landing branch (`learnanything-merge2`) holds `222_section_coverage.sql`.
- CA2's stage branch (`learnanything-dl2`) carries `221_workbench_earlier_opened.sql`, which renumbers when it lands, most likely to 223.

So RW5d's P1 takes the next free number after those. 224 is expected if CA2 lands first; confirm at landing. Following RW1a's precedent ("one migration and no later rebuild", parent §4.3), P1's migration carries the columns P2 needs on these tables, so the sketch tier needs no rebuild.

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

*(Rev 2: P1's migration also carries what P2b and P5 need on these two tables, so neither needs a rebuild. This is Q12's precedent, extended.)*
- `figure_requests.origin` and `interactive_figures.origin` CHECKs include `prefetch`. `goal_author` includes `prefetch`. `figure_requests` gains `build_mode` (`pressed` default, `prefetch`), `tiers_allowed_json` (default `'["grammar"]'`) and `prefetch_decision_id` (nullable, no foreign key until P5's table exists; P5's migration adds the index).
- `interactive_figures.tier` CHECK is `grammar, sketch, js_animation, manim`. `spec_version` takes `js-anim-v1` and `manim-fig-v1`; the program is stored in `spec_json` as for sketches, so the reuse index holds.
- `interactive_figures` gains:
  - `runtime_digest`, generalizing `engine_sha256`: the sketch engine; the prelude, shelf and parser digests for JS; Manim's version and the sandbox profile version;
  - `instrumented_sha256` (JS: the stored instrumented program);
  - `media_file_name` (Manim: the content-addressed mp4, NULL otherwise);
  - `fuller_of_id` (nullable, references `interactive_figures`: the fast figure a rich one follows up);
  - `checks_json` (default `'[]'`: the check lines code ran, per tier).

The table-role classification (`db/table_roles.py`) adds `figure_requests` as RAW_LEDGER; no DERIVED table, so no replayer. Update the head fixture per CLAUDE.md (`fixtures/migration_head_<N>/`, its README and the five hard-coded paths, then the DB reference scripts).

### 13.2 P3's migration (`help_assists`)

`help_assists` is rebuilt to widen `assist_kind` with `'figure'` and `hint_kind` with `'explore_figure'`, and to add a nullable `figure_id`. Its own migration because it is the hint service's table and lands with P3 (it would be dead weight in P1). Next free at P3's landing.

### 13.2b P5's migration (rev 2: `figure_prefetch_decisions`, `plan_usage_pauses`)

These are two new tables, so no rebuild is needed; the number is the next free one at P5's landing. **`figure_prefetch_decisions`** is RAW_LEDGER: append-only, with the outcome columns set once by a trigger, as `figure_predictions.explanation_text` is.

| Column | Contents |
|---|---|
| `id` | `fpd_` + ULID |
| `trigger_kind` | `plan`, `section`, `offer`, `lesson`, `gap` |
| `trigger_ref` | The plan, section, judgment, lesson node or gap id |
| `input_hash` | The figure input it would build (§8.5) |
| `anchor_json`, `goal_text`, `goal_author` | As the request would carry them |
| `p_open_content` | The judge's content probability, or NULL |
| `model_version`, `posterior_digest` | The decision model's version and the posterior it sampled from, so a later audit can recompute it |
| `sampled_eu`, `propensity` | The draw's EU and the share of draws that would build |
| `w_minutes`, `cost_minutes` | `W_tier · P` terms and `C`, as used |
| `decision` | `build`, `skip`, `capped`, `deferred_power`, `deferred_plan` |
| `request_id` | The `figure_requests` row, when built |
| `horizon_kind` | Structural (§10b.5) |
| `outcome`, `outcome_at` | `opened`, `asked`, `neither`, `void`. Set once |
| `created_at` | |

**`plan_usage_pauses`** is also RAW_LEDGER, in the same migration. It has `id`, `hit_at`, `reset_at`, `plan_requests_today`, `plan_tokens_today_known` and `observed_at`. One row is appended, idempotently by `hit_at`, whenever the plan session reports a new usage limit. It is the cost model's data (§10b.3), and the only record of pauses beyond the latest.

- **Posteriors are not stored.** The decision model is recomputed from this ledger at decision time. It is a pure read over a few hundred rows, so there is no DERIVED table and no replayer. The registry holds the priors, and the ledger is the data (LP §3.2: posteriors as recomputable state).
- **The section judge's cache** is a `judgment_ledger` RECEIPT row (task `figure_prefetch_judge`, keyed by the section's content hash and prompt version). It needs no table.
- `db/table_roles.py` gains `figure_prefetch_decisions` and `plan_usage_pauses` as RAW_LEDGER. The head fixture and its five paths are updated per CLAUDE.md.

### 13.3 What persists, and what replay does

| Row | Role | Replay |
|---|---|---|
| `figure_requests` | RAW_LEDGER | Never cleared, never re-run |
| `interactive_figures` (both tiers) | WORKFLOW (paid outputs) | Never re-run (W9) |
| `figure_predictions` | RAW_LEDGER | As today |
| `judgment_ledger` `figure_verified`, `figure_tier` | RECEIPT | Append-only |
| `help_assists` `figure` rows | as the table | As the hint service's rows |
| `interactive_figures` rich rows; their mp4s under `media/animations/` *(rev 2)* | WORKFLOW; content-addressed media | Never re-run. The storage spec's snapshot step 3 must list `interactive_figures.media_file_name` among referenced digests (§20) |
| `figure_prefetch_decisions` *(rev 2)* | RAW_LEDGER | Never cleared, never re-run |
| Sketch runtime state, scenes, slider positions; a JS frame's state; crash markers | not persisted in the vault (the crash marker is per-machine desktop state) | — |

### 13.4 Events

Existing kinds with a payload `event` and `authority_class = 'salience_only'` (parent §4.3): `reader_action_invoked` gains `show_me_requested`, `figure_opened`, `figure_played`, `sketch_paused`, `sketch_error`. Each gets a salience-firewall case. *(Rev 2 adds `fuller_version_opened`, `quick_version_opened`, `rich_build_cancelled`, `js_guard_tripped`, `js_crash_marker`, `prebuilt_line_shown`.)* `figure_opened` carries `prebuilt: bool`, which is the outcome §10b.5 reads.

## 14. Successor ruling

**None, in every phase**, checked against `docs/algorithm-change-playbook.md` step 1 ("Decide whether the change alters persisted meaning"):
- **P1, P2:** content and display. Figures write nothing that scoring, scheduling, projection or serving reads (parent §8.6). The goal text reaches learner-text gaps never (§11.1).
- **P3:**
  - The figure hint-equivalent maps onto `hints_used` with its existing meaning (the hints spec's §10.1 ruling; CA2's §13 ruling for K6). It applies to new attempts only, and no existing attempt can be reclassified: no figure could be opened during an attempt before P3.
  - The `explore_figure` chooser kind changes which help is served, not evidence: a kill switch and no successor, as the hints spec rules for its learned layer (§6.4 there).
  - The diagnoser's `+figures-v1` suffix follows the `+workbench-v1` precedent (no successor; contexts without a trace hash as before).
  - If the P3 agent finds any of these changes an existing attempt's classification in a way the field doesn't already express, it stops and makes it a successor (the next free `mvp-0.N`), as CA2's ruling says.
- **P2b (rev 2):** content and display, as P1 and P2. Rich figures write nothing that scoring, scheduling, projection or serving reads. Their help counting is P3's, unchanged.
- **P5 (rev 2):**
  - Prebuilding changes **when** a figure exists, not what any learner-model quantity means. Scheduling, the plan's blocks, item serving, grading, evidence and the projection read nothing from it.
  - The prefetch decision model predicts opening behaviour, not knowledge, and lives outside the learner model (SM8). Its data moving its posterior is the same algorithm reading more data (LP §3.2).
  - A prebuilt figure can make the chooser's `explore_figure` precondition true sooner. That is the same ruling as P3: it changes which help is offered, not evidence, so it takes a kill switch and no successor.
  - The plan is not changed. The plan trigger reads the stored plan, and the plan never reads figures.
  - Stop rule as P3: if the P5 agent finds otherwise, it becomes the next free `mvp-0.N`.
- **Deferred, and a successor if built:** prediction outcomes as numeric weak observations (the parent's §17 row).

## 15. Every number

None of these is a learner-model weight, margin or threshold (SM8). *(Rev 2.)* The **learn** rows are the prefetch decision model's priors. They are not learner-model quantities, and they carry LP §2's `treatment`, `prior_basis` and `prior_scale`. Each is classified in `params/parameter_registry.py` (module constants are declared explicitly; config leaves get `_ConfigRule`s).

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
| **Revision 2** | | | |
| `figures.rich_tiers_enabled`, `figures.prefetch_enabled` | true (Q18, Q21) | structural, operational | Kill switches |
| `figures.manim_opt_in` | unset until the learner allows | structural, operational | The standing opt-in (§9b.3) |
| `RICH_BRIEF_MAX` | 1,500 chars | structural, operational, `keep` | Prompt size for the rich call |
| `MAX_RICH_ATTEMPTS` | 2 | structural, operational, `keep` | Rev 1's author cap carried over |
| `JS_MAX_PROGRAM_BYTES` | 256 KiB | structural, operational, `keep` | Bounds one animation; reviewable; libraries are not counted |
| `JS_MAX_FRAME_HEIGHT` | 720 CSS px | structural, display, `keep` | A frame never takes over the page |
| `JS_TASK_MS`, `JS_WATCHDOG_MS` | 200 ms, 2,000 ms | structural, display, `keep` | A stall the learner notices but can recover from |
| `JS_MAX_ALLOC_BYTES` | 256 MiB | structural, operational, `keep` | Machine safety within one web process |
| The CSP and sandbox directives | §9b.2 | structural, security, `keep` | The boundary |
| `RENDER_MEMORY_MAX`, `RENDER_CPU_QUOTA` | 4 GiB, 200% | structural, operational, `keep` | oomd history; a render never starves the desktop |
| `RENDER_CONCURRENCY`, `PREFETCH_CONCURRENT_BUILDS` | 1, 1 | structural, operational, `keep` | One at a time |
| `figures.prefetch.max_daily_builds` | 10 | structural, operational, `keep` (Q24) | Plan headroom spent on speculation |
| `figures.prefetch.max_daily_render_minutes` | 30 | structural, operational, `keep` (Q24) | Background compute |
| `PREFETCH_SECTION_CANDIDATES` | 3 | structural, operational, `keep` | Judge output size; one idea per block |
| `PREFETCH_POSTERIOR_DRAWS` | 64 | structural, numerical, `keep` | Monte Carlo resolution of the logged propensity |
| `α` (judge-trust slope) | prior N(1, 1²) | **learn**, `prior_basis: llm_content` | The identity map as the centre |
| `β_kind[trigger]` | prior N(0, 1.5²), pooled by a grid posterior | **learn**, `prior_basis: legacy` (debt) | No population data |
| `β_src` | centre 0, scale from the grid | **learn** | Per-source offset |
| Pause-risk logistic (intercept, slope on plan tokens) | prior centre −3 and 1.5, each sd 2 | **learn**, `prior_basis: legacy` (debt) | Learned from the plan's own usage-limit history |
| `W_tier` | measured | data | Not a parameter |
| `u.minute` | existing | utility (owner preference, LP §6) | Not fitted |

## 16. Phases, smallest valuable first

| Phase | Ships | Needs | Size | Migration | Kill switch |
|---|---|---|---|---|---|
| **P1 — "Show me" in the Reader** (**first slice**) | `FigureRequestV1`, `figure.request`; goal text into the author's context and the hash; grounding through `find_sources` with abstention; joint requests; the intent box passing its text (the `reader_intent` prompt clause); *show me ▸* in the Reader's Ask rail; the tutor's `figure_goal` offer; the landing line, home passage and *not from your books* badge; the report's show-me block (requests, grounding mix, abstentions, unsupported kinds, "not right?" rate) | — (Reader-only; CA2 not needed) | **S–M** | One (§13.1) | `figures.show_me_enabled` (off: today's figures exactly; the tutor's prompt and output as RW5b) |
| **P2 — the sketch tier** | The engine build script and pinned artifact; the Worker runtime and the sidecar `wasmtime` runner; `SketchProgramV1` and `Scene` schemas, both validators; the display-list renderer (SVG primitives, handles, play, new sample, values table); `FigureAuthorOutputV2` and `figure_tier` receipts; verification steps 1–5; labels; engine-upgrade re-verification; "not right?" with errors; the hostile-sketch corpus; the sandbox review | P1 (the request); B3 re-confirmed | **M–L** | None (P1 carried the columns) | `figures.sketch_enabled` (off: the author's contract is RW5b's byte for byte; stored sketches list as *can't draw this yet*) |
| **P2b — rich tiers and progressive delivery** *(rev 2)* | `FigureAuthorOutputV3` with `why_this_tier` and the neutral tier instruction; `tiers_allowed`; `figure_rich_author`; the rich job (§8.6); the fast-then-fuller delivery, cues and progress (§6.8). **JS:** `llfig://`, the frame, CSP, prelude, shelf, loop-guard instrumentation, crash marker, host channel, model-export checks in the P2 engine and in-frame probe agreement. **Manim:** the concept pipeline called as a library, the hardened bwrap profile and capped scope, declared-function checks, the standing opt-in, the shared player. Report tier rows; the hostile rich-figure corpus; the review | P1; P2 (the engine runs JS model checks and the instrumenter). The Manim half needs only P1 and may land first if P2 is late | **L** | None (P1 carried the columns) | `figures.rich_tiers_enabled` (off: V2 contract, no rich menu entries; stored rich figures list as *can't show this kind here*). JS also needs G-SM14's build flag |
| **P3 — exploration as evidence** | Figures in attempts (the CA2 panel's *show me ▸* with its cost line, the workbench step, feedback); the `help_assists` figure row, fold and reveal check; the cold take step and token; `explore_figure` in the chooser; `figure` in RW2c's `help_outcomes` and the hints report; the diagnoser's `+figures-v1` trace | P1; CA2 for the practice host (the Reader workbench works without it) | **S–M** | One (§13.2) | `figures.help_kind_enabled` (off: no figure in attempts, no chooser kind; `help_outcomes` unchanged) |
| **P4a — figures follow the section** | The correspondents read and the *also in your books* line | C0a, CA5 | **S** | None | `reader.correspondence.enabled` (CA5's) |
| **P4b — the teacher's manipulatives** | The `visual` contract as `FigureRequestV1`, predictions suppressed in lessons, the doctrine paragraph; *(rev 2)* `write_plan` nodes' planned `visual` | TE1 (built there) | **S** inside TE1 | None | TE1's |
| **P5 — ahead of need** *(rev 2)* | `figures/prefetch.py`; the five triggers; `figure_prefetch_judge` (section and gap modes); the filters; the learned decision with Thompson sampling and logged propensities; `figure_prefetch_decisions`; horizons and outcomes; `power_state()`; yield-to-foreground; the caps; quiet routing; the prebuilt figure's quiet line; registry entries; the report's `prefetch` block | P1 (reuse by input hash); P2b for rich prebuilds (grammar and sketch prebuilds work without it); RW7b and DL1 (landed); TE1 for the lesson trigger; P3 for gap figures to be served as help | **M** | One (§13.2b) | `figures.prefetch_enabled` (off: nothing builds in the background; rev 1's behaviour exactly) |

**Why P1 first.** It answers the owner's request on its own ("from a natural language query, or jointly"), uses the pipeline and retrieval that exist, touches no evidence, and needs no new runtime. P2 is the largest and the only security boundary, so it goes second with its own review. P3 is small but waits for the help record CA2 builds, so it doesn't build on the overlay CA2 replaces. *(Rev 2.)* Order: P1 → P2 → P2b → P3 → P5, with P4a and P4b when their dependencies land.
- P2b follows P2 because the JS checks and the loop-guard instrumenter run in P2's engine. Its Manim half can go earlier.
- P5 goes last because prebuilding pays only once rich builds are slow enough to be worth hiding. It needs measured latencies (`W_tier`) from pressed builds, which P1–P2b produce.

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
| G-SM14 | P2, **P2b** | In the real desktop webview on Linux, a request to the IPC endpoint from inside the sketch Worker is refused (if not, the opaque-origin frame is added before merge). *(Rev 2, extended to the `js_animation` frame.)* From inside an `llfig://` frame, each of these fails:<br>• `__TAURI_INTERNALS__`, `window.ipc`, WebKit message handlers;<br>• `fetch` to `ipc://` and `http://ipc.localhost`;<br>• the opener and dialog plugins;<br>• `parent` and `top` access.<br>Failing this gate keeps `js_animation` off by build flag |
| G-SM15 | P3 | A figure opened during an attempt adds exactly one hint-equivalent at Submit, however often reopened; feedback-screen figures add none; the reveal row on overlap |
| G-SM16 | P3 | On a cold check: no figure listed; *show me* converts first; a request without the take-step token is refused under `cold_attempt` |
| G-SM17 | P3 | `explore_figure` is an option only with a qualifying existing figure, never one built from the item's own blocks; its propensity is logged; never offered cold |
| G-SM18 | P3 | `help_outcomes` lists `figure` deterministically (computed twice); the diagnoser context hashes as before without a figure trace |
| G-SM19 | all | The salience firewall covers every new `event`; `lint-imports` keeps `evidence-never-reads-figures` |
| G-SM20 | P2b | V3 off: the author contract is V2's byte for byte. On: `tiers_allowed` excludes each unavailable tier (manim missing, off Linux, no `bwrap`, no opt-in, the JS build flag), and the prompt names no preference (a golden prompt test) |
| G-SM21 | P2b | Progressive delivery: the fast figure is shown before the rich job finishes; a failed or cancelled rich job leaves the fast one; one figure line with two versions; the cue text; no toast, count or focus move |
| G-SM22 | P2b | Rich job origin: under a granted press it uses the grant; without one it waits and never makes an offer; a restart never wedges a row |
| G-SM23 | P2b | JS checks: the model exports are verified in the P2 engine (good and planted-wrong corpus); a frame whose probe answers disagree is hidden; a failed claim is not shown; no claims gives *not checked* |
| G-SM24 | P2b | The frame: CSP header exact; `sandbox="allow-scripts"` only; navigation to `https:` refused by `frame-src`; message kinds outside the set dropped; height clamped; starts paused; reduced motion steps; keyboard focus in and out |
| G-SM25 | P2b | The hostile rich-figure corpus in the real webview: no network (including `RTCPeerConnection` absent), no IPC, no storage; loop, recursion and allocation bombs trip guards; the crash marker blocks auto-run after a killed web process |
| G-SM26 | P2b | Manim: the figure path calls the concept pipeline's validator, pacing lint, `render_scene` and store (no copies); the hardened flags and the capped scope are present; declared-function checks run without importing manim; an unextractable function drops its claim, it doesn't fail it; no render without the standing opt-in; off Linux the tier is absent |
| G-SM27 | P5 | Quiet: every prebuild runs under `quiet()`, makes no offer, honours no grant (including a live grant on `figure.request` and a lesson grant); plan down defers |
| G-SM28 | P5 | Power: battery, power-saver or unknown → nothing starts and a running prebuild cancels; the phone and MCP hosts never run prefetch; caps cut the queue in EU order |
| G-SM29 | P5 | Never for exam or held-out spans, never an item's own blocks, never during that item's cold administration; a span withheld later voids the decision and the figure isn't listed |
| G-SM30 | P5 | Decisions: the propensity is logged; outcomes are set once at the structural horizon; a later press reuses the prebuild by input hash (anchor-only and lesson-node cases); an unopened prebuild adds nothing to any attempt; switch off = rev 1 exactly |

The owner checkpoint for P1 is one real "show me" on a `fixtures-local` copy with the plan route; for P2, the sandbox review's report and five real sketches from the owner's subjects (probability, linear algebra, ML). *(Rev 2.)*
- **P2b:** the rich-tier review's report; three real requests where the author chose `js_animation` and two where it chose `manim`, built on the plan; their measured latencies; the owner's yes or no on the frame's feel.
- **P5:** a week of prefetch on the owner's desktop, with the report's `prefetch` block (opens versus builds, pauses, skipped-for-power).

## 17. Risks

| Risk | Mitigation |
|---|---|
| **R1. The sandbox has a hole.** | Sealed interpreter with no bindings, data-only output, the hostile corpus, the IPC gate in the real webview, an adversarial review before merge, the kill switch |
| **R2. A checked-looking figure of a wrong idea.** | Element-scoped check lines, *not covered* lines, *not checked against the book* always, AI-written labels on claims, "not right?". The checks say what they checked and nothing more |
| **R3. Tier drift** *(rev 2, rewritten; the owner decided against steering)*: the author picks a rich tier where a checked figure would teach as well, paying minutes and weaker checks | The prompt states each tier's cost, latency and checks, and `why_this_tier` is required. The report shows, per tier: opens, *not right?*, failures, latency and P3's help outcomes. Correcting a tier that does worse for this learner is the owner's decision or a later learned policy (§19), never a quiet prompt preference. Progressive delivery's fast figure keeps the wait cost low meanwhile |
| **R4. Illusion of understanding:** exploring feels like learning | Exploration is tier 2 at most; in attempts it counts as help; the chooser's outcomes are measured against later independent success, which is what decides whether figures stay prominent |
| **R5. Slow sketches** on the interpreter | Bounded programs, summaries over raw paths, the watchdog's pause, the report's pause counts (trigger for Pyodide or a faster engine) |
| **R6. Ungrounded figures look authoritative** | The badge and the line say *not from your books*; quotes are dropped; the abstention count is in the report |
| **R7. Injection through book text** | The author is an isolated, tool-free turn (`routes.py:249-256`); source and goal are data; its output is either declarative or sealed; nothing it writes can act |
| **R8. Answer leakage on practice** | `assisted_practice` grounding, no stem or key to the author, the reveal check on the figure's text, the hint-equivalent |
| **R9. One more dependency and binary** (`wasmtime`, the engine) | Pinned, hashed, reproducibly built; the grammar tier keeps working with the sketch tier off |
| **R10. The JS frame has a hole** *(rev 2)* (an IPC path from the frame, or a WebKit bug) | G-SM14 extended, in the real webview, as a build flag; CSP, sandbox and `frame-src`; no data in the frame; the review; the kill switch; the separate-webview fallback |
| **R11. Prebuild bias** *(rev 2)*: a built figure's quiet line raises opening, so `P(open \| built, cue)` learns only where it already builds | Thompson sampling explores uncertain candidates; propensities are logged; `asked` on unbuilt candidates is reported as demand without a cue; the report shows both |
| **R12. Speculation crowds out the learner** *(rev 2)* (plan pauses, a busy desktop) | Yield to foreground; quiet; the learned pause risk in the cost; daily caps; mains only; one at a time, niced |
| **R13. Battery drain on the laptop** *(rev 2)* | `power_state()` fails closed; power-saver counts as battery; running prebuilds cancel on unplug |
| **R14. A Manim render escapes or exhausts the host** *(rev 2)* | Mandatory bwrap with `--cap-drop ALL --disable-userns`; a memory- and CPU-capped scope; Linux only; the standing opt-in; the review |
| **R15. Gap figures leak learner state** *(rev 2)* | Only the gap's statement reaches the judge and author, on the plan, disclosed; no history or scores (Q23) |

## 18. Open questions, each with a recommended answer

**Decided (owner, 2026-10-25): all fifteen recommendations Q1–Q15 are adopted as written, and still decided in revision 2.** The owner's rev-2 direction amends the reach of Q2, Q3 and Q5, as noted in their rows. Q16–Q27 are new in revision 2; **decided (owner, 2026-10-26): all twelve adopted as recommended.**

| # | Question | Recommendation |
|---|---|---|
| Q1 | Choose the tier inside the author's one call (`spec | sketch | unsupported`), or with a separate Decider call first? | **One call.** The author knows whether its spec can express the idea; a pre-call adds latency and a route for a worse-informed judgment. The `figure_tier` ledger row is the receipt |
| Q2 | Sketch engine: QuickJS-in-wasm (same bytes in the desktop and the sidecar via `wasmtime`), Pyodide, or a sandboxed iframe? | **QuickJS-in-wasm.** Strongest boundary, exact parity between drawn and verified values, small and fast to start, portable to the phone. Pyodide only if watchdog pauses become common. *(Rev 2, owner decision 2026-10-25: still the sketch tier's engine. The sandboxed iframe, rejected here for sketches, is adopted as the separate `js_animation` tier, and the Manim pipeline is adopted as the `manim` tier (§9b), so the model's best medium isn't capped)* |
| Q3 | A consent click before a sketch runs, as manim has? | **No.** The runtime, not a click, is the protection (§9.6); the frame's ⓘ explains how it runs. *(Rev 2: also no click for `js_animation`. The `manim` tier takes one standing opt-in instead of the per-run click, Q17)* |
| Q4 | Show a sketch whose own stated claim fails, labelled "not checked"? | **No.** It is demonstrably wrong; RW5a's "fail → not shown" stands. *Not checked* is for sketches that state no checkable claim |
| Q5 | Sketch tier on by default once its review passes? | **Yes** (W3), behind `figures.sketch_enabled`. *(Rev 2: the rich tiers follow the same rule once their review passes, Q18)* |
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

**Revision 2: open, each with a recommended answer.**

| # | Question | Recommendation |
|---|---|---|
| Q16 | Who writes rich programs: one new route `figure_rich_author` for both JS and Manim, or the existing `animation` route for Manim? | **One figure route.** It gets the figure author's isolation rule, T1 keying by `figure.request`, the figure price and envelope, and source-grounded context. Manim's contract, scaffold, validator, renderer and store are reused as a library. `animation` stays the concept inspector's |
| Q17 | Manim consent: keep the per-run click, replace it with a standing opt-in, or drop it? | **A standing opt-in, Linux with `bwrap` only,** asked once inline on a press (*allow · not now*) and revocable in settings. It comes with the hardened profile (`--cap-drop ALL --disable-userns`, a memory- and CPU-capped scope). The inspector's Manim path on Linux follows the same setting (its click goes). Off Linux, the inspector keeps its click and figures never offer Manim |
| Q18 | Rich tiers on by default once their review passes? | **Yes** (W3), behind `figures.rich_tiers_enabled`. JS additionally needs G-SM14's build flag in the real webview |
| Q19 | A library shelf for JS animations? | **Yes: KaTeX, d3 and three.js,** vendored, pinned, digest-checked and inlined. It grows on owner request only. Without a shelf, "no ceiling" would mean hand-writing WebGL and maths typesetting |
| Q20 | When the author chooses a rich tier, may it also write a fast spec or sketch in the same call? | **Yes, optional, its judgment.** It is the "fast tier answers in seconds" half of progressive delivery, and it costs no extra call |
| Q21 | `figures.prefetch_enabled` default? | **On** (W3). It is plan-only, quiet, mains-only, capped, never exam material, and invisible until useful |
| Q22 | Should a prebuilt figure show one quiet line on its block, or appear only when asked? | **One quiet line,** the ordinary collapsed figure line, inside the Reader's cue budget, never a count and never on a cold check. A figure nobody knows exists saves nobody a wait unless they happen to ask |
| Q23 | Gap prebuilds send the gap's one-sentence statement (learner state) to the judge and the author. Allow? | **Yes, the statement only,** on the plan, disclosed in the `figure_author` row. The figures that help an open gap are the ones the chooser can serve, and the teacher already carries state in goal sentences |
| Q24 | Background caps: 10 builds a day, 30 render minutes a day, one at a time? | **Yes, as `keep` guardrails.** The report shows how often each cap bites, so the owner can move them |
| Q25 | Lesson planned visuals: build quietly on the plan only, or under the lesson's OpenRouter grant? | **Plan only.** Speculation never spends on a grant. If the step arrives first, the turn builds the visual under the lesson's origin, as rev 1 |
| Q26 | The prebuild cost: the learned risk of pushing the plan into a usage-limit pause, or a per-build cost the owner sets? | **Learned risk,** with the daily cap as the guardrail. A per-build price would be a made-up constant. The pause history is LearnLoop's own data, and `u.minute` is the existing utility |
| Q27 | Power condition: mains only, with power-saver counted as battery and unknown as battery; and may a laptop running its own vault prebuild while plugged in? | **Yes to all.** Battery is what matters (owner profile). carson has none, and a plugged-in laptop is fine |

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
| *(Rev 2)* A learned tier policy (feeding measured per-tier outcomes back to the tier choice) | Per-tier help outcomes (P3) with enough opens, and a way to give them to the author without breaking reuse | Each tier has a supported help-outcome interval in the hints report, and the owner asks |
| *(Rev 2)* JS animations in a separate child webview (own process, no capability) | Tauri multi-webview on Linux, its own CSP and a message bridge | G-SM14 fails for the iframe, or guard trips or crash markers exceed 1 in 10 opened JS animations over a month |
| *(Rev 2)* Rich figures on the phone (the mp4 first) | The mobile client's media path and an allowlisted read RPC | As the phone row above |
| *(Rev 2)* Prebuilding in the S6 remote desktop mode for the laptop's reading | Prefetch already runs at the hub; this only adds the laptop's reading triggers through `/rpc` | S6 lands |

## 20. Cross-spec notes (record when each phase merges)

- `spec_reader_workbench_v1.md`: §8 RW5 and the phase list point here; its §17 row "Generated-code figures" is built here as the sketch tier (P2) and its trigger is superseded by the owner's 2026-10-25 direction and this design's review gate (the unsupported-kind counts remain its evidence); §5.10's "figure views" become real in P3.
- `spec_teacher_v1.md`: `TeacherTurnV1.message.visual` is a `FigureRequestV1` (origin `teacher`); the doctrine row "Instruments over description" is served by RW5d; the deferred row "Teacher-built demos with headless verification" is built here as the sketch tier, so its trigger is superseded.
- `spec_adaptive_hints_v1.md`: `explore_figure` joins §4.2's kinds at level 2 with its precondition (P3).
- `ux_reader_compare_ask_v1.md`: §7.1's box gains *show me ▸* with its cost line (P3); §7.7's cold rules cover it.
- `spec_mcp_frontend_v1.md`: §9.3's sentence amended per Q13; C2 adds origin `chat`.
- `ux_reader_workbench_v1.md`: §4.7 gains the show-me entry and the sketch badge; §11.2's "AI-generated code, sandboxed" label becomes *AI-written simulation · sandboxed*; §4.10 gains the show-me box row.
- *(Rev 2.)* `ux_reader_workbench_v1.md` §4.7 also gains:
  - the rich badges (*AI-written animation · sandboxed*, *AI-made video*);
  - the `◌` progress and *a fuller animation is ready* lines;
  - the prebuilt figure's quiet line, counted in §4.4's cue budget.
- *(Rev 2.)* `spec_teacher_v1.md`: `write_plan` nodes may carry a planned `visual`, which P5 prebuilds quietly on the plan only (Q25). §17's transport list notes that prebuilds never use the lesson's grant.
- *(Rev 2.)* `spec_storage_sync_v1.md`: the snapshot's referenced-digest list (step 3) adds `interactive_figures.media_file_name`. "Rendered media" covers figure mp4s too.
- *(Rev 2.)* `spec_learned_parameters_v1.md`: the prefetch decision model is registered under LP §2's fields as a new learn family outside the learner model. Its `legacy` priors are listed as debt (§3.3).
- *(Rev 2.)* `content/authoring/concept_animation.py`: the module docstring's security posture is reworded at P2b to say that bubblewrap is the sandbox and the allowlist is hardening. The inspector's consent follows Q17.
- *(Rev 2.)* `spec_reader_workbench_v1.md` §17's "Generated-code figures" row: the `js_animation` tier is the generated-code figure it described, behind the isolation design it asked for (§9b.2, G-SM14).
