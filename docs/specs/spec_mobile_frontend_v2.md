# The phone as a second frontend (mobile frontend v2)

**Status:** revision 1, 2026-11-06. **Proposed. For owner review; nothing here is built.** Written against main `8b0738499d` (TE3a landed, migration head 249).

**The owner's request (2026-11-06, verbatim):**

> we need to remake the phone webapp/alternative frontend as well to include things like a phone reader, better UI/UX, etc. We basically want to share the main user journeys available on the desktop with the phone, while the phone acts as an alternative frontend while the desktop application does most of the work and runs

**What this spec does.**
- It keeps the phone host of `spec_mobile_tailnet_v1.md` (M1, PR-1..PR-7 and M2a, all built) and its security model unchanged.
- It replaces that spec's narrow phone *client* with a second frontend that covers the desktop's main journeys (§2).
- It folds in the Reader's queued phone stage, **CA7** (`ux_reader_compare_ask_v1.md` §5.7, §8.5, §13, Q11), as the phone Reader (§3).
- It sets the UI/UX rules (§4), the architecture (§5), the migration from today's PWA (§6), tests (§7), build stages (§8), and six decisions for the owner (§9).

**What it amends, once the owner accepts it.** This is listed so nothing is changed silently. Each amendment is made in the stage that needs it, with a dated note.
- `spec_mobile_tailnet_v1.md`:
  - §1 "out of scope: the reader" and §9 "Later: the reader (separate spec)" point here.
  - §4.5 gains the allowlist rows of §5.2.
  - The M2a ruling "Phone Today is the queue, never the plan" (§9.9) is replaced by §2.2 if the owner takes D1.
- `spec_reader_workbench_v1.md` D20 ("no new RPC is phone-allowed in v1") and `ux_reader_workbench_v1.md` §7.6 are superseded for the phone by §3.
- `ux_reader_compare_ask_v1.md` CA7 is absorbed into stages V4/V5. Its rule "nothing that costs money runs on the phone" is replaced by D2.
- `spec_followup_generate_serve_v1.md` §10 "Phone" and the §4.2 door table's Phone row change if the owner takes D3.

**Sources read for this spec.**
- **Phone host and app:** `spec_mobile_tailnet_v1.md` rev 4 with its as-built §9.1-§9.9, and `docs/reviews/mobile-m2a.md`; `src/learnloop_mobile/`; `apps/learnloop-mobile/`; `docs/mobile-shortcuts.md`; `integrations/ios/`.
- **Desktop:** `apps/learnloop-tauri/src` (screens and `api/`), and the sidecar registry (`src/learnloop_sidecar/registry.py`, `handlers/*.py`, 502 registrations).
- **UX:** `ux_learnloop_v1.md`, `ux_reader_workbench_v1.md`, `ux_reader_compare_ask_v1.md`.
- **Journeys and behaviour:** `spec_followup_generate_serve_v1.md`, `spec_router_objective_v1.md` (RO0-RO6 landed), `spec_teacher_v1.md` rev 5 (TE0-TE3a landed; TE3b not built), `spec_reader_show_me_figures_v1.md`, `spec_deliverable_curriculum_v1.md`, `spec_storage_sync_v1.md` §6.2 (the hub, PR-8).
- **Not useful here:** the architecture vault (`docs/learnloop-architecture-vault/`). Its journey Examples and Maps are at mvp-0.9 and include no Reader, lessons, follow-ups or router. §2's journey list therefore comes from the code and the specs above, not from the vault.

---

## 1. Principle: the desktop runs everything; the phone renders and sends intents

**The rule.** The desktop host does all of the following:
- runs the sidecar code, the models, storage, the router, grading, diagnosis, generation, page rendering and every durable write;
- runs as the mobile host process (`learnloop-mobile serve`), beside the desktop app or alone, on the same vault.

The phone does three things:
- renders what the host returns;
- sends the learner's intents (an answer, Next, a selection to ask about, a reading position);
- keeps them working on a small screen and a flaky link.

The phone never decides what to serve, never grades, never computes evidence, and never holds learner state of its own.

**What the phone may hold.** Two things, both disposable:
1. **A display cache.** This is the last copy of what the host showed: the plan step, the open question and its draft, reader sections already opened, a lesson's transcript. It is never authoritative. Every screen re-reads the host when it can and says when it is showing a stale copy.
2. **An outbox of intents.** These are intents that can wait for the host without changing their meaning (§5.4).

Revocation (a 401) deletes the token and the display cache, and keeps the outbox for the next token, as M2a does today.

**What M1 and M2a already do, and v2 keeps.**

| Concern | Built (M1/M2a) | v2 |
|---|---|---|
| Where state lives | One `state.sqlite` on the desktop. The host attaches as a secondary (`load_secondary`, PR-1) and never migrates (T7) | Unchanged |
| What the phone stores | Credential, capture outbox (IndexedDB, media as Blobs), `sessionCache.ts` (answer, key, draft help, the request as sent), cached session id | Same, plus a bounded display cache for reader sections, plan step and lesson (§5.4) |
| Long work | Durable `mobile_jobs` with `request_id`; 15 s wait, then `202` and a poll (§6.3) | Same contract for every new long method (lesson turns, asks, plan decisions that call a model) |
| One session, one owner | `start_session_exclusive`, `adopt_session`, `session_moved` (PR-4) | Extended to every session-keyed write v2 opens (§5.6) |
| Request origin | `phone_queue`, `phone_practice` from the token, never from params (PR-5) | Adds `phone_plan`, `phone_reader`, `phone_lesson` surfaces |
| What the phone can't render | `device_eligibility.py` (PR-6), "N items waiting for the desktop" | Kept, narrowed where the host can now render (§2.3) |
| Freshness | Host bumps `queue_revision`; the desktop's app-level poll (PR-7, R2) | Unchanged on the desktop; the phone polls the same token |
| Offline | Capture works offline; practice needs the desktop (D9) | Unchanged in substance: reading cached sections and queueing progress also work offline (§5.4) |

**Why not responsive desktop screens.** `spec_mobile_tailnet_v1.md` §3.4's finding still holds:
- the desktop screens import Tauri at module scope;
- they are large keyboard-first layouts (the Reader alone is about 3,750 lines plus about 50 hooks).

The phone gets its own screens. It shares the desktop's **types, query cache and pure render modules**, not its layouts (§5.3).

---

## 2. Journey parity

### 2.1 The table

Key to the "Phone v2" column:
- **Full:** the journey completes on the phone, with the same protections.
- **Reduced:** the core of it works, and named parts stay on the desktop.
- **Desktop-only:** not on the phone in v2, with the reason.

RPC names are the sidecar's. **Reused** means an existing method added to the host allowlist. **New** means a method or endpoint this spec adds. Stage letters refer to §8.

| # | Journey (desktop) | Phone v2 | Phone screens | RPCs: reused / new | Too heavy for the phone, and how it degrades | Protections that carry over |
|---|---|---|---|---|---|---|
| J1 | **Today and the plan with Next.** One sentence, minutes, Next (`TodayPlace`, `DailyPlanView`) | **Full** (if D1) | Today | Reused: `get_daily_plan`, `get_today_headline`, `next_plan_item`, `set_plan_minutes`, `plan_keep_going`, `plan_more_new`, `plan_learner_pick`, `plan_reading_ended`, `get_start_summary`; `get_today_queue` stays for plan-off vaults. New: none. The host adds the device filter at the plan step (§2.2) | A plan step the phone can't render is left for the desktop and counted, as the queue does now | Plan steps keep their offer receipts, with surface `phone_plan`. Session ownership (§5.6) |
| J2 | **Practice with feedback.** Answer, blind grade, feedback, clarification, Next | **Full** for typed answers. Photo answers are M2b, voice is M3 (mobile spec) | Question, Feedback | Reused (allowlisted now): session, item, draft, `submit_attempt`†, `submit_dont_know`†, `get_feedback`, clarification†, `diagnosis_status`, `submit_eliciting_response` (owner's uncommitted edit, §6.2). Added: `record_answer_display`, `record_diagnosis_feedback`, `trigger_regrade` (the contest, "I think I was right"), `rate_followup` | None heavy. Long grades are already jobs | Blind grading is unchanged: the phone sends text, the grader is the desktop's. No self-grade on the phone (M2a). Reveals are recorded by the same `record_answer_display` |
| J3 | **Follow-up probes after a miss** (FG1). Held feedback, *Preparing a question…*, *Continue without it*, *Show anyway*, hypothesis marks | **Full** (if D3); otherwise reduced to M2a's "continue it on the desktop" | Feedback, Question | Reused: `followup_status`, `followup_next`, `followup_continue_without`, `followup_show_anyway`, `record_hypothesis_exposure`, `record_hypothesis_mark`. Changed: the `probe_presentation_id` constraint on `submit_attempt`/`submit_dont_know` is lifted for phone-eligible probes (V3) | Polled at the desktop's 2 s interval; no push | Generated probes are single use, burned at first serve (FG1 §4.2), and answered cold with nothing held released early. *Show anyway* marks the answer not independent. Exam-reserved material never reaches the generator (FG1 §8) |
| J4 | **The router's visible decisions.** The plain router line, `why?`, `details ▸`, *how was this chosen?* | **Full** | Feedback, Today (one line each) | Reused: plan and feedback replies already carry `routerDecision` and per-block `why`/`whyDetails`; `router_objective_explain`. Read only | — | Display only; `ui.show_router_decisions` governs it, as on the desktop |
| J5 | **Stop offers** at block boundaries, *Keep going* / *Done*, the optional "predicted gain" line | **Full** | Today (a `done` step with `stopReason`) | Reused: `next_plan_item`, `plan_keep_going{stop}` | — | The stop coin's randomization is the engine's. The phone shows what it is given, in both directions |
| J6 | **The daily randomized check** (RO5). One a day, served as an ordinary plan item with no special label | **Full** when the item is phone-eligible; otherwise it waits for the desktop | Question | Reused: through `next_plan_item` | — | Cold: no hints, no help panel. Help would make it a non-success, and the phone offers none during it. A check left for the desktop is recorded `device_deferred` on its trace (§2.2) |
| J7 | **Reader with sections.** Guide plan, section progress, reading doses, saved place, end of section | **Reduced** (§3): text-first | Library → Reader | Reused: `reader.guide_plan`, `reader.get_progress`, `reader.mark_section_progress`, `reader.log_activity`, `reader.saved_place`, `reader.dose_offer`, `reader.dose_offer_event`, `reader.prompt_contract`, `plan_reading_ended`. New: `reader.render_view` gains an optional section or span range (§3.2); `GET /api/v1/reader/page/{extraction}/{page}` (a page image, §3.3) | No PDF.js on the phone. The original page is a server-rendered image on demand. Margin marks, side-by-side panes, the workbench and the intent box stay on the desktop | Reading is never evidence of mastery (`○ ◌ ●` only). Cold checks at a section's end follow J6's rules. A reading block ends exactly as on the desktop |
| J8 | **Ask** from a selection in the Reader; the standalone Ask | **Full** in the Reader; standalone Ask follows M3 | Reader (selection sheet), Ask | Reused: `reader.ask`† (synchronous on the desktop, a job on the phone), `reader.ask_history`, `reader.cancel_request`; M3's `ask_tutor_question`†, `get_tutor_transcript` | The answer streams on neither device; the phone shows *Thinking…* and polls | Ask during a cold check is refused as on the desktop (`coldActive`). Ask answers write reveal rows (`tutor_answer`) as on the desktop |
| J9 | **Compare** across books: ask your library, compare scope, kept comparisons by point, side by side | **Reduced** | Reader (sheet), Compare card | Reused: `reader.library_ask`†, `reader.library_compare`†, `reader.compare_scope`, `reader.library_job`, `reader.library_job_cancel`, `reader.kept_comparisons`, `reader.library_compare_keep` (with a take), `reader.library_compare_reopen` | Side by side (`reader.side_by_side_section`) is desktop-only, because two panes don't fit. A kept comparison shows as CA7's narrow cards by point (`ux_reader_compare_ask_v1.md` §5.6, X6) | Each row quotes its own book. The three voices (§ source, ◇ model, › you) are kept |
| J10 | **Show me figures** | **Reduced** | Reader, Feedback (inline figure) | Reused: `reader.figures`, `figure.open`, `figure.request`†, `reader.figure_job`, `figure.take_step`, `reader.figure_explain`. New: `GET /api/v1/figures/{id}/render` (a static render) and `GET /api/v1/media/{sha}` (Manim mp4) | The declarative tier (`InteractiveFigureSpecV1`, pure TypeScript) runs live. The sealed sketch tier (QuickJS-wasm in an iframe worker) is shown as a static render made by the host, because its sandbox needs a CSP the phone app shouldn't have. Manim's mp4 plays as a file. *Open on the desktop to explore* is the link | Figures are help, never certification (RW5d). A figure opened during a cold check counts as help, as on the desktop |
| J11 | **Lessons with the teacher.** Open, plan map, predict, teach, check, detour, close; probes inside a lesson; *Continue your lesson* | **Full** (V6) | Lesson (a document, with interjection cards) | Reused: `lesson.view`, `lesson.turn`† (open, reply, answer_prediction, answer_check, stop, resume), `lesson.open_lessons`, `lesson.suggestion`, `lesson.suggestion_respond`. `lesson.activity` is reused with the phone's minutes. Lesson probes need D3 | A turn is a model call: a job, with *Writing…* and the 15 s wait, then a poll | Probes inside a lesson are cold, single use and blind-graded (teacher §11.3). The "your thinking" field and the confidence tap never reach the grader. Exam material is never taught (§9.3 guards are server-side) |
| J12 | **Typed goals** in a lesson; **resume** | **Full** | Lesson, Today card | Reused: `lesson.goal`, `lesson.turn{resume}`; the close card's *Add to my goals* | — | As J11 |
| J13 | **Goals and deliverables.** Goal cards, a deliverable from a sentence, scope, exams | **Reduced** | Progress | Reused: `goals_list`, `get_goal_report`, `curriculum.deliverables`, `curriculum.scope`, `curriculum.create_deliverable`† (writes the goal at a server-chosen path, a named exception as in mobile §4.5). Desktop-only: scope editing (`curriculum.set_scope`, `scope_decide`, `set_depth`), exam sittings (`start_exam`…) | Scope review is a dense table; it stays on the desktop. A deliverable typed on the phone is resolved by the host, and its scope can be reviewed on the desktop | Exam sittings stay desktop-only: reserved material and a timed sitting on a flaky link don't mix. Nothing about scoping reads protected material (deliverable spec §9) |
| J14 | **Capture of photos and text** | **Full** (built) | Capture (the `+` tab) and the Shortcuts | Reused: `POST /api/v1/capture`, `GET /api/v1/capture/{id}`. M3's background processor and *Practice this* stay in the mobile spec | — | Sanitization and the outbox as built (§4.4, §7 of the mobile spec) |
| J15 | **Library.** Books, continue reading, add a source | **Reduced** | Library | Reused: `get_source_library` (read only). *Add a link* is a URL capture (J14). Desktop-only: file import, re-extract, delete, ingest administration | Adding a PDF from the phone is not in v2 (books exceed the 20 MB upload cap, and ingest is desktop work) | Ingest administration stays never-allowed (mobile §4.5) |
| J16 | **Help and reveals in practice, and their review.** Hints ladder, *show answer*, the review feed of what was answered with help | **Reduced** | Question (help sheet), Progress → Review | Reused: `practice.request_hint`†, `practice.hint_job`, `practice.cancel_hint`, `practice.record_hint_reveal`, `record_answer_display`, `get_review_log` (read only) | The review feed is a list. The knowledge well (`KnowledgeMapScreen`) stays on the desktop | Help states what it changes before it happens (◌ "with help"). No help is offered during a cold check, a randomized check or a probe; the server also refuses it (`coldActive`, `help_assists`). PR-5 left hint surfaces on desktop values; V2 gives them `phone_practice` |
| — | **Desktop-only in v2** | — | — | Never allowed (mobile §4.5) plus: workbench (`workbench.*`), teach-back, error hunt, calibration, probe dialogues, exams, the graph and knowledge map, ingest and settings, proposals, under the hood | Multi-pane, keyboard-heavy or administrative work. Each keeps its PR-6 ineligibility or simply has no phone screen | — |

† Long: a durable job under mobile §6.3 (`request_id`, 15 s wait, then `202` and a poll).

### 2.2 The plan on the phone (J1, J5, J6)

**Why M2a chose the queue.** M2a kept the phone on the queue for two reasons:
- the plan's stored record is shared between devices;
- filtering at the plan's *build* would hide items from the desktop (`mobile-m2a.md` §1 item 2; `daily_plan.py` docstring).

PR-6 already named the way out: "M2 filters at the step" (mobile §9.7).

**v2 serves the same plan to both devices and filters at the step** (if D1):
- **No device filter at build.** `get_daily_plan` and the plan's composition stay exactly what the desktop gets.
- **The step skips what the phone can't render.**
  - When `next_plan_item` runs under a phone origin and the step it would serve is phone-ineligible (`ineligibility_reason`, PR-6), the step goes to the next eligible block in plan order.
  - It leaves the ineligible one assigned and counts it in `device_deferred_count`, as the queue does. The phone shows *2 questions are waiting for the desktop.*
  - A held-back step stays in the plan for the desktop's next Next. A reading block is never ineligible, because the phone has a Reader (§3).
- **Router decisions.** Decisions taken at a boundary under a phone origin record the surface `phone_plan`. They record `device_policy: device_eligibility_v1` (or `off`) in their inputs, as M2a's queue offers do. The support the router chooses from is unchanged. Only the serving door skips.
- **The randomized check.** The day's check is drawn before any device is known (RO5 §9 item 2).
  - If it is phone-ineligible, it waits for the desktop. Its trace records `device_deferred`, so the completion-rate term in `r` (RO §8.7) and the report can see it.
  - Nothing re-draws it for the phone. Re-drawing would make the check's inclusion depend on the device.
- **Stop offers** arrive as a `done` step with `stopReason`, and the phone answers with `plan_keep_going{stop}`, as the desktop does. The randomized stop coin is the engine's; the phone only displays it.
- **A plan decision can call a model.** RO4's LLM policy runs at a boundary (`objective_chooser.py`). So `next_plan_item{serve: true}` is **long-capable** on the phone: the adapter waits 15 s, and beyond that returns `202` with a job, and the phone shows *Choosing what's next…*.
- **Kill switch.** `mobile.phone_plan` (default true once V2 lands). Off, the phone falls back to M2a's queue.
- **Successor.** None expected, by M2a's reasoning: no vault has a phone-plan predecessor state, and desktop replies stay byte-identical at a None origin. The V2 build confirms this against `docs/algorithm-change-playbook.md` and records the ruling.

### 2.3 What becomes phone-eligible

PR-6's reasons stay, with two narrowed once the host can serve the bytes:
- **A prompt that embeds an image or references an item asset** becomes eligible (V4). The host serves the asset by content hash (`GET /api/v1/assets/{sha256}`, read-only, from the originals store).
- **A prompt that links `llpdf://`** becomes eligible (V4). The phone renders the link as the page image of §3.3.

Error hunt, laddered stems, multi-turn teach-back, `diagnostic_microprobe` and a lesson's own check (`lesson_check`) stay desktop-only. The lesson check stays inside its lesson, which the phone can open (V6).

---

## 3. The phone Reader (CA7 folded in)

**What CA7 was.** CA7 proposed kept comparisons by point, read-only plus *your take*, and *as printed* after feedback. It was gated on the owner's trigger "when the phone page is used most days" (Q11). The owner's request now asks for a phone reader outright. So CA7's two allowlist entries become part of a full Reader (V4, V5), and its trigger is met by this request.

### 3.1 Reading on a phone: text first

**What the phone shows.**
- **The text.** It renders the desktop's **extracted** document: `reader.render_view`'s blocks, sanitized Markdown with `$…$`/`$$…$$` math, rendered with KaTeX through the desktop's `render/MarkdownMath.tsx`.
- **Layout.** One column at a readable measure, in a serif face for the book's voice (§4.6), reflowed to the screen.
- **Equations.** Wide display math scrolls sideways inside its own box; the page never scrolls sideways.
- **Tables.** Tables wider than the screen get the same horizontal box, plus *view as image* (§3.3).

**Navigation.**
- A section list comes from `reader.guide_plan` (`sections[]`). It shows titles, `○ ◌ ●` where the desktop shows them, and the reading mark where the learner is.
- Within a section: scroll, then *Next section* at the foot, in the thumb zone.
- *Continue reading* opens the section and span from `reader.saved_place`, so a place saved on the desktop opens on the phone, and the reverse.

**Poor extraction.** A block whose `health.recommended_view` is not the text (scanned, garbled, figure-heavy) shows the page image of §3.3 instead of its text, with a quiet *as printed* label. The phone never shows garbled text silently.

### 3.2 Loading by section

**The problem.** `reader.render_view` returns the whole extraction. That is fine over stdio and too much for a phone on cellular.

**The fix.** It gains an optional `sectionId` (or `fromSpanId`/`toSpanId`) parameter that returns only that range's blocks, with the same block shape.
- Absent, the reply is byte-identical to today's, which a test pins.
- This is the one sidecar change the Reader needs. It belongs in the shared handler, not in the host, so the two can't drift.

**Prefetch.** The phone fetches the open section and prefetches the next one. Both go into the display cache (§5.4), so a section can be read on the train with no signal.

### 3.3 The original page, on demand

**The endpoint.** `GET /api/v1/reader/page/{extractionId}/{page}?w={px}` returns a WebP or PNG of one page.
- It is rendered by the host with pypdfium2, which the sidecar already uses for `reader.block_original_region` (`span_view.py`).
- Widths are snapped to a small set (for example 720 and 1080 px), so the cache stays bounded.
- Its auth is a `Token(app)`.

**Caching.**
- The host caches renders on disk by `(file sha256, page, width)`, under the host's cache directory, never in the vault.
- Responses are immutable and content-addressed (`Cache-Control: private, max-age=31536000, immutable`). This is a stated exception to §4.6's `no-store`, made safe because the URL names the content. The service worker may cache these responses, and only these, beside the app shell.

**Uses.**
- *View the page* on any block.
- *As printed* after feedback, through `reader.block_original_region` with `spanIds` (CA1, already built), as CA7 asked.
- The `llpdf://` links of §2.3.

**Why not PDF.js on the phone.**
- PDF.js would mean shipping the PDF (often tens of MB) over the tailnet, holding it in iOS Safari's memory, and duplicating the desktop's text-layer selection logic.
- The phone needs none of that. The extracted text already carries the spans that selection, progress and Ask use. A page image covers fidelity.
- Reconsider only if page images prove unusable for some book (§9, D4).

### 3.4 Progress, doses and the end of a section

The phone records reading exactly as the desktop does, through the same methods, so the evidence is one stream:
- **Progress.** `reader.mark_section_progress{spansSeen, spanCount, revealed, completed}` is sent as spans scroll into view, debounced. The first `completed` enqueues the section's practice generation, which is idempotent per section. That generation runs where the desktop's runs (D6).
- **Monotonic progress.** Progress must be monotonic across devices: a phone's lower `spansSeen` must never lower the desktop's. The V4 build checks the upsert and makes `spansSeen` and the timestamps take the max if it doesn't.
- **Activity.** `reader.log_activity{events}` is sent with the desktop's ids, kinds and timings, never learner text. Each event carries its client `occurred_at`, so RO0's `occurred_at`/`received_at` gap survives the outbox (RO §4 row 5).
- **Doses.** At a section boundary the phone calls `reader.dose_offer`. The randomized `reading_dose_v1` draw is the server's, made before anything is shown. The phone renders the offer (an extra worked example, or an extra in-passage question served as a question) and reports `reader.dose_offer_event` (`delivered`, `not_delivered`, `taken` or `dismissed`).
  - Offline, no dose is drawn, because the draw needs the host. The section's progress waits in the outbox.
- **Plan reading blocks** end with `plan_reading_ended{outcome}`, as on the desktop.
- **Surface.** Every reader call under a phone origin records the surface `phone_reader`.

### 3.5 Ask from a selection

**Selecting.** Selection works on the rendered text, not the page image.
- A long press selects a word. The iOS handles extend it. On release, a bottom sheet offers **Ask**, **Save** (`reader.capture`) and **Copy**.
- The sheet never covers the selection. It sits at the bottom, and the text scrolls above it.

**Asking.** Ask sends what the desktop's `reader.ask` takes: `extractionId`, `spanId`, `selectionSpanIds`, `selectionQuote`, the question, and `retrievalIntent` (explain, alternative or remediate, as three plain chips).
- The span ids come from the blocks' `span_id`, so the server's check that the passages belong to this reading holds unchanged.
- The answer opens in the same sheet, in the three voices.
- Follow-ups in the thread use `parentExchangeId`. The history is `reader.ask_history`, shared with the desktop.

**Asking across books.** *Ask your library* and Compare (J9) start from the same sheet as jobs.

**Out of v2 on the phone.** Highlights and margin notes as editable objects (`reader.create_annotation` and its siblings) stay on the desktop; *Save* covers the phone's need. Translation and video watch plans also stay on the desktop.

---

## 4. UI and UX

### 4.1 Rules carried from the desktop

The phone follows `ux_learnloop_v1.md` without exception. The rules that matter most on a small screen:
- **One primary action per screen, zero required decisions** (§4.2 layer 1). Next, Submit and *Next section* are a full-width button in the thumb zone.
- **Plain words.** The desktop's jargon deny-list test (`src/copy/denyList.test.tsx`, §9 glossary) runs over the phone's components too (§7.1).
- **The glass box on demand.** `why?` and `details ▸` sit on the object, collapsed. On the phone they open as a bottom sheet, not inline, so the primary button doesn't move.
- **The stated exception:** the router line (J4) is on the surface by default (`ui.show_router_decisions`), as FG1 §6.4 decided.
- **No counts of waiting things.** The only count is *N waiting for the desktop*. It is kept because it explains an absence, as M2a decided.
- **No raw numbers about the learner.** Only `○ ◌ ●` and *assumed known*.
- **Errors: one sentence, one action.**
- **Three voices:** § the book, ◇ the model, › you.
- **No toasts or modals while reading; never wait.** A job shows one line on its object (*Writing…*, *Preparing a question on this…*), with its cancel or *continue without it* beside it.

These follow the owner's direction recorded as "frictionless UX over transparency": default to frictionless, keep the glass box one tap away, use no jargon.

### 4.2 Places and navigation

**A bottom tab bar with four places**, matching the desktop's four (Today · Library · Reader · Progress) and adapted to one hand:

| Tab | Holds |
|---|---|
| **Today** | The plan sentence and Next, lesson cards (*Continue your lesson on X*, TE3b offers when built), *waiting for the desktop* |
| **Read** | The library list, then the book (Library and Reader in one stack, since a phone can't show both) |
| **+** | Capture: text, photo or link. The tab is centred, because capture is the phone's most-used verb |
| **Progress** | Goal cards, deliverables, the review feed |

**Within a tab:**
- Screens push onto a stack, and Back is the edge swipe and a top-left chevron.
- Question, Feedback, Lesson and the Reader cover the tab bar while open, so the primary action owns the bottom. One swipe or chevron returns.
- The current view is mirrored in the URL fragment (`#/read/<extraction>/<section>`). A reload or a cold app start returns to the same place.
- No router library is needed. The PWA keeps its own small view stack (§5.3).

### 4.3 One-hand use

- Primary actions sit in the bottom third. Nothing that commits work sits in the top corners.
- Targets are at least 44 × 44 pt, with 8 pt between adjacent targets.
- Sheets open from the bottom, are dismissed with a downward swipe, and are always also closable by a button.
- No gesture is the only way to do anything, and no gesture commits (no swipe-to-submit).
- The answer editor keeps M2a's symbol bar above the keyboard. The primary button stays visible above the keyboard (`visualViewport`), so Submit never hides behind it.

### 4.4 Connection states

There are four states. Each is one quiet line under the title, never a modal:

| State | Detected by | Line | What still works |
|---|---|---|---|
| **Connected** | A recent successful call | (nothing) | Everything |
| **Desktop unreachable** | A network error, or 502/504 from Serve (`http.ts` `OFFLINE`) | *Desktop offline. Reading and capture still work.* | Cached sections, the open question's draft, capture and queued progress (§5.4) |
| **Desktop busy** | `503 host_busy` or `database_busy`, retried per policy | *Desktop is busy — trying again.* | As connected, with waits |
| **Grading unavailable** | `grading_fallback_required` | *Grading isn't available right now. Your answer is saved.* | Everything except a new grade |

**Reconnect.** On `online`, on `visibilitychange` to visible, and on a successful call, the phone does the following in this order:
1. flush the outbox;
2. re-read the session (`session_moved`);
3. read `queue_revision`;
4. refresh the screen in view.

It never refreshes a screen under an answer being typed (the desktop's R2 rule).

### 4.5 Latency: what a round trip costs, and how to hide it

**The path.** Phone → WireGuard (direct, or relayed through Tailscale's DERP) → Serve on carson → loopback → the host's RPC worker → the shared handler → SQLite. *Estimates for the owner's single-user tailnet, to be measured in V1 (below); none of these are measured yet:*

| Leg | Estimate |
|---|---|
| Same Wi-Fi, direct path | 5-20 ms round trip |
| Cellular, direct path | 40-120 ms |
| Relayed (DERP) | 80-250 ms |
| New connection (TCP + TLS 1.3) | +2 round trips; the PWA keeps one connection warm while open |
| Host: a short read (`get_session`, `get_feedback`, a cached section) | tens of ms |
| Host: a queue or plan build | hundreds of ms to seconds |
| Host: a plan decision with RO4's LLM policy, an Ask, a lesson turn | seconds to tens of seconds (model calls) |
| Host: a grade | 5-180 s (mobile §6.3) |

**Measuring it.** The host adds a `Server-Timing` header (queue wait and handler ms) to every `/rpc` reply. The PWA records client round-trip time beside it in `mobile_request_log`'s existing duration field, through the report. `learnloop-mobile report` then shows p50 and p95 per method and the network share. V1 lands this first, so later stages are measured, not guessed.

**Budgets (`keep` bounds, checked in the report, not gates):**
- A tap shows its response at once (≤ 100 ms, locally): pressed state, the draft saved, the sheet opened.
- Switching to a screen with cached data: ≤ 300 ms, showing the cache and then refreshing.
- A fresh short read: p50 ≤ 1 s on cellular.

**How the phone hides the wait.**
- **Optimistic, but only for intents that can't be wrong:** drafts, reading progress, hypothesis marks, a capture, a kept comparison's take. These show as done at once and reconcile on the reply.
- **Never optimistic for a decision or a grade:** Next, Submit, an Ask or a lesson turn shows its waiting line until the host answers.
- **Prefetch:**
  - the next reader section and its page images;
  - the feedback bundle the moment a submit completes;
  - while feedback is being read, the next plan step as a **non-serving peek** (`next_plan_item{serve: false}`), *if* the V2 build confirms the peek writes nothing that depends on being shown. If it writes decision rows, there is no peek, and Next shows *Choosing what's next…*. It does, so there is no peek. `plan_prefetch` (`spec_instruct_handoff_v1.md` §3a) starts the decision's model calls instead: it writes nothing and returns no step.
  - The router's decision depends on the outcome just graded, so it is never made before the grade.
- **One warm connection.** A cheap `GET /healthz` on resume reopens the TLS connection while the screen renders from the cache.

### 4.6 Visual direction

**Paper and ink, quiet by default.** The phone's job is mostly reading and answering, so the text is the design. It uses the existing CSS variables in `apps/learnloop-mobile/src/styles.css`, extended, with no new design system or component library.

- **Two themes, following the system** (`prefers-color-scheme`), with a manual override in a small *Display* sheet:
  - **Dark:** today's palette (`--bg #14161a`, `--panel #1c1f25`, `--text #e8e6e1`, amber `--accent #e0a458`).
  - **Light:** warm paper (about `#f7f4ee` background, `#1f1d1a` text, a deeper amber for contrast). KaTeX inherits `currentColor` in both.
- **Type.**
  - The UI uses the system face (`-apple-system`), at 17 px base and scaled with iOS Dynamic Type (`font: -apple-system-body` on the root, rem everywhere).
  - Book text uses `ui-serif` (New York on iOS) at a measure of 60-70 characters, line-height 1.55.
  - The learner's and the model's text stay in the UI face. With the § ◇ › markers, that keeps the three voices visually distinct.
- **Evidence glyphs** `○ ◌ ●` and the voice markers are the only ornaments. There are no badges, streak flames or progress rings, which the UX spec refuses.
- **Motion.** Only sheet and stack transitions, 200 ms, and none under `prefers-reduced-motion`.
- **Desktop palette.** If the desktop's design tokens are already exported as CSS variables, the phone imports the colour values rather than copying them. Otherwise the phone keeps its own small set; no shared token pipeline is built for this.

### 4.7 Accessibility

- VoiceOver: every control has a label; sheets trap focus and return it; the stack announces the new screen title.
- Math: KaTeX renders with `output: "htmlAndMathml"`, so VoiceOver reads the MathML. Page images carry the block's extracted text as `alt` when its health is good, and *page N, as printed* otherwise.
- Contrast is WCAG AA in both themes, checked by a vitest over the theme tokens.
- Dynamic Type up to the accessibility sizes, with no clipped buttons (the layout wraps).
- Nothing is conveyed by colour alone: verdicts are words, and `○ ◌ ●` are shapes.

---

## 5. Architecture

### 5.1 One host, one proxy, no duplicated logic

**The host stays `learnloop-mobile serve`.** It keeps its edge (Host, identity, token, limits), its two workers in secondary attach, and its jobs (mobile §3.1, §6). **Every journey in §2 goes through `POST /rpc` to the shared sidecar handlers.** The host adds no domain logic of its own. The only new host code is:
- **The reader page, asset and figure-render endpoints** (§3.3, §2.3, J10). They are read-only.
  - They run on a third worker, the **media lane**: a small pool that needs no `SidecarContext`. It uses `Repository.attach(read_only=True)`, the originals store, and the renderer functions `learnloop.reader` already has.
  - A slow page render therefore never queues behind a short RPC, and the reverse.
  - It has its own admission bound (8, `keep`) and returns 503 `host_busy` beyond it.
- **`Server-Timing`** and the client-timing field (§4.5).
- **The allowlist's v2 rows** (§5.2) and their parameter constraints.

**The desktop sidecar changes only where a shared handler must:**
- `reader.render_view`'s optional range (§3.2);
- the step-level device filter in the plan (§2.2);
- monotonic reading progress if it isn't already (§3.4);
- origin surfaces for the new phone doors (`phone_plan`, `phone_reader`, `phone_lesson`, and hint surfaces);
- ownership checks on the session-keyed writes v2 opens (§5.6);
- lifting the probe constraint for eligible probes (V3, if D3).

**No embedded server in the desktop app.** D2 of the mobile spec stands: the phone must work with the desktop app closed, and the sidecar is a single-threaded stdio loop.

**Relation to the hub (storage spec S5, PR-8).** When the hub lands, the hub holds the primary role and the mobile host stays a secondary. Nothing in this spec depends on the hub. D6 says what the host runs until then.

### 5.2 The allowlist, versioning and auth

**The allowlist grows by stage, default-deny as now (T3).** Each new entry is a `MobileMethod(name, milestone, kind, retry_safe, param_constraints)`, with `milestone` = the v2 stage (`V2`…`V7`). The G3 test that enumerates the registry keeps every other method at 403.

**Constraints added with v2 (enforced in the adapter, before dispatch):**
- **Any vault path or file parameter** is still rejected for every method.
- **`reader.*`:** `extractionId` must resolve. `coldActive` comes from the server's own state, never trusted from the phone.
- **`lesson.turn`:** actions are limited to those §2.1 J11 lists.
- **`next_plan_item`:** `serve: true` requires the session the phone owns.
- **`figure.request`:** origin `ask` or `reader` only.
- **`curriculum.create_deliverable`:** `sentence` ≤ 1 KB, and no path.
- **Paid methods** (the long ones, plus job starters such as `reader.library_ask`) carry `request_id`, so a retry can't pay twice (§6.3's coalescing).

**The retry policy is generated, not copied.**
- Today `apps/learnloop-mobile/src/api/retryPolicy.json` is a hand-kept copy that `test_mobile_allowlist.py` checks.
- v2 has the test **write** it: `ALLOWLIST` → `retryPolicy.json` plus a `phoneMethods.ts` const list.
- A pytest fails if the committed files differ from what the allowlist produces. The PWA's typed client can then only name allowlisted methods (§7.2).

**Versioning.**
- `GET /api/v1/meta` (Token(app)) returns `{host_version, api_version, allowlist_digest, schema_version}`.
- The PWA build embeds the `allowlist_digest` it was built against.
- The host serves the PWA itself (`/app/`), so the two normally move together. The risk is a stale shell cached by the service worker.
- On open and on resume, the PWA compares digests. On a mismatch it shows *LearnLoop was updated. Reload* (one tap; the service worker's cache is keyed by build hash). Until reloaded, a `method_not_allowed` is shown as that same line, never as a raw error.
- `api_version` is `1` and stays `1`. v2 adds methods and endpoints and changes no existing contract. A breaking change would add `/api/v2/`.

**Auth is M2a's, unchanged:**
- the Host check, `Tailscale-User-Login == owner_login`, and a per-device `app` bearer token held in IndexedDB;
- pairing by the manual code, because a home-screen app keeps storage apart from Safari's;
- no cookies, no CORS, the same CSP.

v2 adds no auth surface. The new endpoints are `Token(app)`, and the page and media endpoints are `GET`s under the same checks.

**CSP.**
- The sketch tier's sandboxed iframe would need `frame-src` and `wasm-unsafe-eval`. v2 doesn't ship it (J10), so the CSP is unchanged.
- `img-src 'self' blob: data:` already admits host page images.
- `media-src 'self' blob:` is added for J10's mp4.

### 5.3 The PWA's structure

**Kept stack:** React 18, Vite 5 and TypeScript, the `@desktop` alias to `apps/learnloop-tauri/src`, and vitest with jsdom and fake-indexeddb. No new framework.

**Shared with the desktop (imported through `@desktop`, never copied):**
- `api/dto.ts` (the hand-written DTOs), `api/queryCache.ts`, `useCachedQuery.ts`, `queryTags.ts`;
- `render/MarkdownMath.tsx`, `render/markdownPipeline.ts`, `render/MathLiveEditor.tsx`;
- `figures/figureSpec.ts` and its pure evaluator (J10's live tier), **if** it has no Tauri or DOM-worker import. The V5 build checks this; otherwise the phone shows the static render for that tier too.
- A test fails if anything the phone imports from `@desktop` reaches `@tauri-apps/*` (a module-graph walk in vitest, §7.1). This keeps the share honest as the desktop changes.

**The phone's own modules:**

```
apps/learnloop-mobile/src/
  api/        http.ts (kept), phone.ts → generated method list + typed wrappers, jobs.ts (202 + polling, generalized)
  store/      credential, outbox (generalized to intents, §5.4), sessionCache (kept), displayCache (new: sections, plan, lesson)
  shell/      TabBar, Stack, Sheet, ConnectionLine, theme
  today/      TodayScreen, PlanStep, StopOffer, LessonCard, WaitingForDesktop
  practice/   QuestionScreen (kept, restyled), FeedbackScreen (kept core + follow-up panel, marks, router line), HelpSheet
  read/       LibraryList, ReaderScreen, SectionList, SelectionSheet, AskThread, PageImage, DoseOffer, KeptComparison
  learn/      LessonScreen (document + interjections), PlanMap, CheckCard
  progress/   GoalCards, DeliverableNew, ReviewFeed
  capture/    CaptureScreen (kept)
```

### 5.4 Caching and the outbox

**Display cache** (IndexedDB, new store):
- **What it holds:** reader sections (blocks plus `guide_plan`), keyed by extraction, revision and section; the last plan step and headline; open lessons' views.
- **Bounds:** an LRU of 50 MB for sections (`keep`). Page images are cached by the service worker under the same budget. The plan and lessons keep their last copy only.
- **On a 401** it is deleted, with the session cache. On a revision change of an extraction, its sections are dropped.
- **Not bulk export.** Mobile §4.4's "no bulk export to the phone" holds: the phone caches what was opened plus one section ahead, never a whole book.

**The outbox, generalized from captures to intents.** An intent may wait in the outbox only if all three hold:
1. replaying it later means the same as sending it now;
2. it is idempotent by a client id;
3. nothing waits on its reply.

| Intent | Outboxed? | Idempotency |
|---|---|---|
| Capture (text, photo, link) | Yes (built) | `client_capture_id` |
| `reader.mark_section_progress` | Yes | Monotonic upsert (§3.4); the latest per section wins locally, so only one is queued |
| `reader.log_activity` | Yes | Each event carries a client ULID and `occurred_at`; the build checks the store dedupes on it, or adds that |
| `reader.dose_offer_event` | Yes | `drawId` plus event |
| A kept comparison's *your take* | Yes | Client id |
| `record_hypothesis_mark` | Yes | (attempt, hypothesis) is last-write-wins on the server; the build confirms |
| Drafts | No: `sessionCache` holds them, and `save_practice_draft` is sent when connected (built) | — |
| Submit, Next, Ask, a lesson turn, a figure request, Skip | **No.** Each decides, grades, generates or spends; it needs the desktop now | Jobs (§6.3) once connected |

**Flushing.** The outbox flushes in insertion order:
- on open, on `online`, on visibility, and every 60 s while open (iOS has no Background Sync);
- before any other call on reconnect (§4.4).

The capture outbox's response classes (mobile §7) apply to every intent.

### 5.5 Follow-ups and lesson resumes: polling, not push

**v2 polls** (D5), with the existing `useVisibleInterval`, which stops while the app is hidden:

| What | Interval | While |
|---|---|---|
| Job status (`/api/v1/jobs/{id}`) | 2 s | A job is open (built) |
| `followup_status` | 2 s, the desktop's interval | A follow-up is pending or held on Feedback |
| `diagnosis_status` | 3 s (built) | A diagnosis is pending |
| `queue_revision` | 3 s (built) | Today is on screen |
| `reader.library_job`, `reader.figure_job`, `practice.hint_job` | 2 s | That job's line is on screen |
| `lesson.open_lessons` | on open and on visibility only | — |

On return to the app, each of these is read once at once.

**What the learner misses.** A follow-up or a lesson that became ready while the app was closed is seen on the next open: Today's *Continue your lesson on X* card, and Feedback's follow-up line. That is the same as the desktop, which also has no notifications.

**Why not Web Push.** Web Push on iOS requires the home-screen app and Apple's push service, which is a path off the tailnet. It is deferred (D5).

### 5.6 Phone and desktop open together

| Shared thing | Rule |
|---|---|
| **The session** | One owner (PR-4). The non-owner's session-keyed writes return `session_moved`; the desktop shows *This session continued on your phone* (built). v2 **closes PR-4's open list for every write it opens**: plan steps (`next_plan_item{serve}`, `plan_keep_going`, `plan_learner_pick`, `plan_reading_ended`), tutor and Ask writes bound to a session, lesson turns bound to a session, and reading-progress writes that carry a session. Each checks `require_owned_session`. This is a prerequisite of V2 (mobile-m2a §3 item 9) |
| **The plan** | One stored record, read by both. Steps commit atomically, and a phone step bumps `queue_revision` (PR-7's `host_mutation`), so the desktop's Today refreshes under R2 |
| **Reader progress and place** | Server-side, monotonic (§3.4). Each device keeps its own scroll position locally; *Continue reading* uses the server's saved place, so the device that read last wins the place and neither lowers progress |
| **A lesson** | A lesson's turns are a sequence. `lesson.turn` from the phone carries the lesson's last turn index (`expectedTurn`). A stale one is refused with `lesson_moved`, and the phone re-reads `lesson.view`. The V6 build adds this parameter to the shared handler if it has no equivalent. The desktop's LessonScreen re-reads on `queue_revision` change and on focus, so a lesson continued on the phone shows its new turns on return |
| **Asks, comparisons, figures** | Append-only histories, shared. No conflict |
| **Drafts** | Owned by the session (built) |

**Desktop changes.** Only the ownership refusals above, and the lesson screen's re-read. The desktop gets no phone-specific UI beyond M2a's banner and prompt.

---

## 6. Migration from today's PWA

### 6.1 Kept, rewritten, dropped

| Path (apps/learnloop-mobile/src) | Fate | Why |
|---|---|---|
| `api/http.ts` (transport, 202, retry, the 401 rule, `OFFLINE`) | **Kept**, with `Server-Timing` read and the digest check added | Correct and tested against §6.2/§6.3 |
| `api/retryPolicy.json` | **Generated** (§5.2) | A copy can drift |
| `api/phone.ts` | **Rewritten** as typed wrappers over the generated method list | One wrapper per allowlisted method, grouped by journey |
| `store/credential.ts`, `store/db.ts`, `store/sessionCache.ts` | **Kept** | M2a's correctness work (F1-F11) lives here |
| `store/outbox.ts` | **Generalized** to intents (§5.4); the capture path is unchanged | — |
| `screens/QuestionScreen.tsx` | **Kept in logic, restyled.** Moves to `practice/`; gains the help sheet (J16) and, with D3, probe presentation | Its skip and submit outcome handling is M2a's hardest-won code |
| `screens/FeedbackScreen.tsx` | **Kept in core, extended**: follow-up panel, hypothesis marks, router line, reveal recording, contest. The owner's uncommitted diagnosis card and eliciting questions (§6.2) are the base | — |
| `screens/TodayScreen.tsx` | **Rewritten** around the plan step (J1), with the queue kept as the plan-off path | The queue list becomes the fallback |
| `screens/CaptureScreen.tsx`, `PairScreen.tsx` | **Kept**, restyled | — |
| `App.tsx` (545 lines, one view union) | **Rewritten** as `shell/` (tabs, stack, sheets) | Four places and stacks don't fit one union |
| `styles.css` | **Rewritten** as theme tokens plus components, light and dark | — |
| `App.test.tsx` (1,337 lines) | **Split** by journey; existing cases kept | — |
| `components/RemoteImageAsLink.tsx` | **Kept**, and narrowed: host asset URLs (§2.3) render as images; remote ones stay links (CSP) | — |
| `public/sw.js`, `manifest.webmanifest`, icons | **Kept**; `sw.js` gains the immutable page-image cache and the build-hash key | — |

**Nothing is dropped** except `App.tsx`'s single view union and the old stylesheet. The host's Python is extended, not rewritten.

### 6.2 The owner's uncommitted phone edits (main checkout, 2026-11-03)

This spec was written from a worktree at `8b0738499d`. The main checkout's working tree holds the owner's uncommitted edits. They were read there and compared file by file with the committed copies; nothing was copied or changed. **What they change:**

1. **Diagnosis follow-up questions on the phone's Feedback.** The diff adds:
   - `submit_eliciting_response` to the M2 allowlist, as short and not retry-safe ("Each call writes a new report, so it is not retried");
   - its pins in `tests/test_mobile_allowlist.py` and `tests/test_mobile_rpc.py`, where it joins the never-retried set;
   - a dated note in `spec_mobile_tailnet_v1.md` §4.5 ("Added at the owner's report, 2026-11-03 … a recorded answer, never a grade").
2. **The diagnosis on the phone's Feedback.** The changes are:
   - `phone.ts`: `diagnosisStatus` now returns the desktop's `DiagnosisCardDto`, and `submitElicitingResponse` is added.
   - `FeedbackScreen.tsx` shows *What happened here* (the card's `summaryMd`) once the diagnosis is done, and *The look into this answer didn't finish. Your grade stands.* when it failed.
   - It asks the diagnosis's eliciting questions one at a time, never showing the expected answer, and says *Answer recorded. It isn't graded.* It adds *…won't count as independent evidence because the answer was already on screen* when the server says so.
   - `styles.css` adds `h2`, and `App.test.tsx` has the tests.
3. **The iOS Shortcuts' capture id.**
   - `generate_shortcuts.py` replaces the base32 ULID encoder, which failed on the real iPhone with "You asked for item 0", with a 26-character id: 17 digits of local time (`yyyyMMddHHmmssSSS`) and 9 zeros, with no randomness.
   - The two `.shortcut` files are regenerated, and `docs/mobile-shortcuts.md` and `tests/test_mobile_shortcuts.py` follow.
   - Two devices capturing in the same millisecond would get a 409 and keep their files.

**v2 keeps all three.** (1) and (2) are part of J2's feedback parity and are V2's starting point. (3) is independent of the PWA.

**What the owner must do first.** V1 and V2 rewrite or extend exactly these paths: `FeedbackScreen.tsx`, `phone.ts`, `styles.css`, `App.test.tsx`, `allowlist.py` and its two tests. Agents never commit the owner's files, and a stage worktree branched from main without them would either drop them silently or conflict at landing. So before V1 starts:
1. **Commit the edits on main** (or discard any you don't want), so main carries them. A one-line check that the edited tests pass is enough: `uv run pytest tests/test_mobile_allowlist.py tests/test_mobile_rpc.py tests/test_mobile_shortcuts.py`, and `npm test` in `apps/learnloop-mobile`.
2. **Run A4 if possible** (`docs/reviews/mobile-m2a.md` §7). M2a's screens have never been rendered in a real browser (its known limit 3). Learning now whether the editor, the symbol bar and the canvas re-encode work on the iPhone changes what V1 rebuilds. Not a gate: V1 can start without it.

---

## 7. Testing

### 7.1 Unit and component (vitest, `apps/learnloop-mobile`)

- **Kept:** every existing case (transport, 202, retry policy, outbox, fragment token, service worker, each screen through the fake host).
- **New, per stage:** each screen's journey through the fake host (§7.3); theme contrast; the jargon deny-list over phone components (imported from the desktop's list); the `@desktop` import walk that refuses any path to `@tauri-apps/*`; the display cache's LRU and its 401 wipe; the generalized outbox (ordering, idempotency, the response classes); connection states and reconnect order (§4.4).

### 7.2 Contract tests between the PWA and the host's allowlist

- **Method names.** pytest writes `retryPolicy.json` and `phoneMethods.ts` from `ALLOWLIST` and fails on a diff (§5.2). A vitest fails if `phone.ts` names a method not in `phoneMethods.ts`. The type system enforces the same, and the test keeps it visible.
- **Parameter shapes.**
  - Each wrapper in `phone.ts` has a recorded example request under `apps/learnloop-mobile/contract/<method>.json`, generated by a vitest from the wrapper itself.
  - A pytest loads every file and validates it through the adapter: envelope, allowlist and constraints. It then validates it through the method's own `ParamsModel` (`extra="forbid"`).
  - A renamed or added field on either side fails the build, not the phone. This is the phone's equivalent of `tests/test_desktop_rpc_contract.py`.
- **Result shapes.** For each method, a pytest on a fresh fixture vault (helpers' builders) calls the handler through the host's adapter, and asserts the reply carries the fields the phone's DTO reads (a per-method key list beside the request example). Model-calling handlers run with `StructuredClientFake`.

### 7.3 Journey tests with fakes, no model calls

- **Host side (pytest):** for each journey in §2.1, a test drives the host's Starlette app (TestClient), on a fresh vault, with the fake identity header and fake AI clients (`StructuredClientFake`, `openai_fakes.py`):
  - J1/J5/J6: plan steps under a phone origin, the step filter, a stop offer, the randomized check deferred and its trace;
  - J2/J3: a miss, the held feedback, a probe served, burned and answered (V3);
  - J7/J8: a section loaded by range, progress monotonic across a phone and a desktop write, a dose draw and event, Ask by span;
  - J11: a lesson opened, a turn as a job, a stale `expectedTurn`, resume.
- **Two processes (durability lane):** `test_mobile_two_process.py` extends to a plan step on the phone interleaved with the desktop's, and reading progress from both.
- **PWA side (vitest):** the same journeys through the fake host, asserting what the learner sees: words, the one primary action, the waiting lines.
- **No test makes a model call or a network call outside the TestClient.** Every ad-hoc script runs under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, and with routes off.

### 7.4 How tests are run

- Every pytest run goes in a `systemd-run --user --scope -p MemoryMax=5G` scope, with `-n 6` at most. vitest runs with 4 workers at most.
- Stages run targeted tests while iterating. The full suite, the durability lane and vitest run once, in each stage's landing gate.

### 7.5 Phone acceptance (the owner runs these on the iPhone)

A1-A4 of the mobile spec stay as they are. v2 adds a set per stage, each recorded in that stage's review file:

| Id | Stage | Check |
|---|---|---|
| P1 | V1 | Reinstall from the home screen: the new shell opens. Light and dark follow the system. Text follows the iOS text-size setting at its largest accessibility size without clipped buttons. VoiceOver reads the tab bar and a KaTeX formula |
| P2 | V1 | With carson suspended, the app opens from the cache, says *Desktop offline*, and Capture works. On wake, the line clears and the outbox flushes |
| P3 | V2 | Today shows the plan's sentence. Next serves the same next block the desktop would show. With the desktop app open, the desktop's Today moves within about 3 s after a phone answer |
| P4 | V2 | Miss a question on purpose. Feedback holds the worked answer and shows *Preparing a question on this…*, then the router line. Check that *Continue without it* and *Show anyway* behave as on the desktop. Take a hint: it is labelled *with help* |
| P5 | V2 | Keep going past the plan's minutes until a stop offer appears; take *Keep going*, then *Done* |
| P6 | V3 | A generated follow-up probe is served on the phone, answered, and the held feedback then appears. Reopening it from history does not serve it again |
| P7 | V4 | Open a book: the section list, then a section. Math renders. *View the page* shows the original. Selection → Ask returns an answer that quotes the passage. Airplane mode: the opened section and the next stay readable; progress made offline appears on the desktop after reconnecting |
| P8 | V4 | Finish a section on the phone: the desktop's Reader shows it completed, and its questions arrive as on the desktop |
| P9 | V5 | From a selection, ask the library and compare. A kept comparison opens as cards by point. A figure shows (live or static). An mp4 figure plays |
| P10 | V6 | Start a lesson on the phone, answer a prediction and a check, leave the app, and continue it from the desktop's *Continue your lesson*. Then the reverse |
| P11 | V7 | Create a goal from a sentence on the phone; it appears on the desktop. The review feed lists today's answers with their help labels |

---

## 8. Stages

**Shape.** Each stage is one orchestrator stage on its own worktree from main, landed before the next starts unless marked parallel. Sizes: **S** is a day or less of agent work, **M** a few days, **L** about a week. Migration numbers and successor tags are claimed at landing.

**Spend.** No stage adds a paid call of its own. Every model call the phone causes is one the same journey makes on the desktop, under the same routes, envelopes and budgets (D2). Tests use fakes, and smokes run on fresh fixture vaults with routes off.

**Order.** It gives the owner a usable new phone early: the new shell and today's practice (V1, V2), then the Reader (V4), then lessons (V6), then the rest.

| Stage | What | Touches | Migration / successor | Paid calls | Tests | Size |
|---|---|---|---|---|---|---|
| **V0 (owner)** | Commit or discard the uncommitted phone edits on main (§6.2). Optionally run A4 | Owner's files | — | — | The three test files + `npm test` | — |
| **V1: shell and plumbing** | New PWA shell (tabs, stack, sheets, URL fragment), light and dark themes, Dynamic Type, accessibility basics, connection states, `GET /api/v1/meta` and the digest check, `Server-Timing` and client timing in the report, generated `retryPolicy.json`/`phoneMethods.ts` and the request-example contract tests, the `@desktop` import walk, the generalized outbox (captures only at first), the display cache store. Today, Question, Feedback and Capture are restyled onto the shell with **today's behaviour unchanged**. **As built (2026-11-06, `docs/reviews/phone-v2-v1-shell.md`):** all of it, with these narrowings, each recorded there with the smallest way to finish: the fragment restores the place, never a question or a feedback (opening either writes; they come back from the checkpoint as before); Feedback and the grading wait get no back chevron (M2a had none); Capture stays one tap away in the top bar of the covering screens; Read and Progress say plainly that they come later; the phone keeps its own colour set (the desktop's palette variables differ from §4.6's dark values); the round trip rides on the next `/rpc` as `client:`/`network:` rows of the request log; the generated files are rewritten only under `LEARNLOOP_UPDATE_PHONE_CONTRACT=1`; `App.test.tsx` is kept whole (its 149 cases are the proof of unchanged behaviour) and split in V2. Also touched: `runtime.py` (the worker's timing), `capture/maintenance.py` (the log's endpoint labels), `cli.py`, the new `client_contract.py` | `apps/learnloop-mobile/**`, `learnloop_mobile/host.py`, `adapter.py`, `capture/report.py`, `tests/test_mobile_*` | None / none | None | vitest per component; contract tests; host `meta` and `Server-Timing` tests; P1, P2 | M |
| **V2: Today is the plan; practice and feedback parity** | Plan RPCs allowlisted (J1); the step-level device filter and `phone_plan` surface (§2.2); `next_plan_item` long-capable; the stop offer (J5); the randomized check deferral (J6); the router line, `why`, `details`, `router_objective_explain` (J4); the follow-up panel without probes (held feedback, *Continue without it*, *Show anyway*, marks), diagnosis card and eliciting questions (owner's edits), reveal recording, the contest, hints with their surfaces (J2, J3 partial, J16 partial); PR-4's remaining ownership checks for plan, Ask, tutor and lesson writes (§5.6); kill switch `mobile.phone_plan`. **As built (2026-11-06, `docs/reviews/phone-v2-v2-today-plan.md`):** all of it, with these narrowings, each recorded there with the smallest way to finish: blocks are decided one at a time, so "the next eligible block" is the first open block the phone can show, and otherwise the phone's Next crosses one boundary (a read never does); a boundary with nothing feasible waits for the desktop, and while the day's randomized check waits the phone crosses none (its *Skip it* is the desktop's skip link); readings wait for the desktop until V4; AD's slot draw is not asked under a device; no peek (§4.5's fallback line); a hint reveal keeps `help_assists.surface = practice` (a CHECK constraint; the device is the attempt's `entry_surface`) and the adaptive hint jobs stay off the phone (in-memory jobs); no session-keyed reading-progress or lesson-turn write exists to check; the kill switch is `phone_plan` in `mobile.toml`; the phone keeps its own plan wording (the desktop's imports its Tauri client); the desktop's answer-exposure gate became a pure module (`answerExposureGate.ts`) the phone shares. No successor (the playbook ruling is in the review) | `learnloop_mobile/allowlist.py`, `handlers/daily_plan.py`, `daily_plan/engine.py` (the step filter), `scheduling/device_eligibility.py`, `learnloop_sidecar/request_origin.py`, the PR-4 ownership sites, PWA `today/`, `practice/` | None expected (no table); **no successor expected**, with the playbook ruling recorded at the build (§2.2) | None | Host journey tests J1-J6; two-process plan steps; desktop byte-identical at a None origin; vitest journeys; P3-P5 | L |
| **V3: probes and cold checks on the phone** (if D3) | Lift the `probe_presentation_id` rejection for phone-eligible probes; render an active probe contract on the phone (cold banner, no help, no Ask); FG1 serving on the phone (burn at first serve, held feedback released on answer); FG1 §4.2's Phone door and §10 amended. **As built (2026-11-07, `docs/reviews/phone-v2-v3-probes.md`):** all of it, behind the phone host's `phone_probes` (mobile.toml, default true) at the successor **mvp-0.54** (built as mvp-0.53, renumbered after TE3b's mvp-0.53 landed) (the playbook's 2026-10-17 rule: which items are served as measurements changes for a phone origin), with these narrowings, each recorded there with the smallest way to finish: eligibility is PR-6's structural rules unchanged (image, page or asset links; microprobe dialogues, teach-back, error hunt, laddered stems, lesson checks), so an eligible probe is any other probe; the switch rides on the request origin, which the host sets; the phone's admission is one `BEGIN IMMEDIATE` transaction with its cap count (G10); single use across devices is FG1's claim keyed by surface, the phone's plan holding a desktop-served probe and the desktop's serving Next abandoning a phone-served one unless the phone's answer to it is still being graded; a phone door burns one only for the session's owner (checked in the claim's transaction), and only for an app that says it answers probes (`LearnLoop-Capabilities: phone_probes` on every `/rpc`; a cached V2 app keeps V2's doors) (Codex review, `docs/reviews/phone-v3-codex-review.md`); lesson probes wait for V6 (lessons aren't on the phone); *Teach me instead* stays on the desktop (the phone's way out is Skip). Also built here: V2's carried items, migration **250** (`help_assists.surface` gains `phone_practice`; head `migration_head_250`) and the F9 class on a finished plan (Keep going and `more_new{confirm}` commit their override receipt with the new plan) | `allowlist.py`, `practice.py` constraints, `device_eligibility.py`, PWA `practice/` | No table; **a successor is likely**, because a phone origin then serves and answers probes it used to defer. Kill switch `mobile.phone_probes`. The build decides with the playbook | None (generation is FG1's, already paid on the desktop path) | Burn and single use across both devices; cap boundary (G10) with phone probe answers; P6 | M |
| **V4: the phone Reader** (CA7 folded in) | `reader.render_view` optional range; the media lane, the page endpoint and its cache; item assets and `llpdf://` as page images (§2.3); guide plan, section list, reading view, progress (monotonic), activity with `occurred_at`, saved place, doses, `plan_reading_ended`; selection sheet with Ask and Save; *as printed* after feedback (`reader.block_original_region`); display-cache prefetch; outbox intents for progress, activity and dose events. **As built (2026-11-07, `docs/reviews/phone-v2-v4-reader.md`):** all of it, behind the phone host's `phone_reader` (mobile.toml, default true; the app says `LearnLoop-Capabilities: phone_reader`, so a cached V3 app keeps V3's plan), with no migration and no successor (the playbook ruling is in the review: reading recorded from the phone is the same evidence as on the desktop), and with these narrowings, each recorded there with the smallest way to finish: the phone is never sent what exam material covers (no text, page image or cached copy of a held-out passage, an exam-pool source or a reading held back; a reading covered whole is refused), which is stricter than the desktop's display; the page endpoint serves only pages some reading covers, by reading or by file (`sha256-…`, as an `llpdf://` link names it), cached by vault, file, page and width outside the vault; *as printed* after feedback is `practice.as_printed` (the desktop Feedback's own path, with its solution and cold guards), not `reader.block_original_region`; there is no server-side saved place, so *Continue reading* is the shared reading history (the desktop's fallback); progress was already monotonic (no change); the outbox's three intents are host jobs keyed by the intent's id, so a replay is coalesced; activity records `device_surface: phone_reader`; a section finished on the phone host leaves its generation to the desktop (D6: `deferred_to_primary`, taken at the desktop's start and when its Reader reads the book's progress); §2.3's lift covers content-addressed targets only and names `device_eligibility_v2`; the guide's section checks, cues, annotations and translation stay on the desktop; the Read tab's list is `get_source_library` at a phone origin (V7 adds the rest) | `handlers/reader.py` (range param), `learnloop/reader/*` (if progress needs max), `learnloop_mobile/host.py` (media lane, endpoints), `allowlist.py`, PWA `read/`, `sw.js` | No migration expected (the render cache is on disk outside the vault); a progress upsert change, if needed, is checked for replay equivalence. No successor expected | None new (Ask as on the desktop) | Range reply byte-identical when absent; progress across devices; page endpoint auth and immutability; P7, P8 | L |
| **V5: Ask your library, Compare, figures** (can run parallel to V6) | Library ask and compare as jobs; kept comparisons by point (CA7's X6), *your take* outboxed; figures: declarative tier live, sketch tier as a host static render, Manim mp4 through `GET /api/v1/media/{sha}`; `media-src` in the CSP | `allowlist.py`, `learnloop_mobile/host.py` (figure render and media endpoints), PWA `read/` | None / none | None new | Jobs and cancel; figure render endpoint; CSP test; P9 | M |
| **V6: lessons on the phone** | `lesson.*` allowlisted; `lesson.turn` as a long job; `expectedTurn` / `lesson_moved`; lesson document view with interjection cards, plan map, prediction and check cards, confidence tap, "your thinking"; typed goals; resume and *Continue your lesson* on Today; lesson probes (needs V3); `lesson.activity` from the phone; TE3b offers render as plan steps when TE3b lands | `handlers/lesson.py` (expected turn), `allowlist.py`, PWA `learn/`, desktop `LessonScreen.tsx` (re-read on revision) | None expected / none | None new | Lesson journey with fakes; stale turn; desktop re-read; P10 | M-L |
| **V7: goals, deliverables, library, review** | Goal cards, deliverable from a sentence (long), library list read-only with *Add a link* through capture, review feed; the remaining J13-J16 reads | `allowlist.py`, PWA `progress/`, `read/LibraryList` | None / none | None new | Host and vitest journeys; P11 | S-M |
| **Later (not v2)** | Photo answers (mobile M2b), voice and the standalone tutor (M3), Web Push (D5), the sketch tier live, highlights as objects, side by side on a tablet width, exam sittings | — | — | — | — | — |

**The first usable phone** is V1 plus V2, about two weeks of stages. The owner can use the plan, practice, follow-ups without probes, stop offers and the router line on the phone after that, and the Reader one stage later.

---

## 9. Decisions for the owner

**D1. Phone Today serves the shared plan, filtered at the step.**
- **Recommendation: yes.** This reverses M2a's ruling of 2026-11-03 (§2.2).
- **Trade-off:** it brings J1, J5 and J6 to the phone and makes the phone a real second frontend. In exchange, the plan's steps gain a device filter and phone-origin offer rows, and PR-4's ownership checks must close first (in V2). The alternative keeps the phone on the queue, with no stop offers and no plan sentence.

**D2. Journeys that spend model calls run from the phone** (Ask, library ask and compare, figure requests, lesson turns, plan decisions, generated probes).
- **Recommendation: yes, under the desktop's routes, envelopes and budgets.** This retires CA7's "nothing that costs money runs on the phone".
- **Trade-off:** parity needs it, and the spend is what the same journey costs on the desktop. In exchange, the host process spends from `mobile.env`, so a phone session can spend while the desktop app is closed.

**D3. Diagnostic probes, including FG1 follow-ups and lesson probes, are answered on the phone** (V3).
- **Recommendation: yes, for phone-eligible probes, behind `mobile.phone_probes`, with the successor the playbook asks for.**
- **Trade-off:** without it, every miss on the phone ends in *continue on the desktop*, which is the exact confusion FG1 was built to remove. With it, a probe answered on a phone in a distracting place carries the same evidential weight. The surface is recorded, so reports can split it.

**D4. The phone Reader is text-first with server-rendered page images, and no PDF.js.**
- **Recommendation: yes** (§3.3).
- **Trade-off:** it is light on memory and data, and selection uses the extracted spans that Ask already needs. In exchange, a scanned or badly extracted section reads as page images, with no selection on them.

**D5. Polling, not Web Push, in v2.**
- **Recommendation: polling**, with every status read once on return to the app.
- **Trade-off:** it adds no path off the tailnet and no Apple push dependency. In exchange, a ready follow-up or a lesson's next turn is not announced while the app is closed; it is seen on the next open, as on the desktop.

**D6. Until the hub (storage S5) lands, the host runs only the phone's own work.** That means its jobs, and the post-attempt diagnosis M2a already drains. Section-completion generation, ingest and other primary duties wait for the desktop app.
- **Recommendation: yes.** This keeps M2a's line (mobile-m2a §8 Q1) and adds no new background spender to the host.
- **Trade-off:** with the desktop app closed, reading on the phone records progress at once, but the section's new questions arrive only once the desktop app (or later the hub) runs. The alternative binds the generation runner in the host now, which duplicates PR-8's job before PR-8.

---

*Related: `spec_mobile_tailnet_v1.md` · `docs/reviews/mobile-m2a.md` · `ux_learnloop_v1.md` · `ux_reader_compare_ask_v1.md` (CA7) · `ux_reader_workbench_v1.md` §7.6 · `spec_followup_generate_serve_v1.md` · `spec_router_objective_v1.md` · `spec_teacher_v1.md` · `spec_reader_show_me_figures_v1.md` · `spec_deliverable_curriculum_v1.md` · `spec_storage_sync_v1.md` §6.2*
