# LearnLoop UX: frictionless by default, the glass box on demand (v1)

**Status:** draft for owner review, 2026-10-13. Branch `docs/learnloop-ux`, written against `main` at `57d31c63`.

**Scope.** The whole app except the inside of the Reader:
- the shell and navigation;
- first run and ingest;
- Today and the daily plan;
- practice and feedback;
- the knowledge views;
- settings, and everything else.

**Companion.** `docs/specs/ux_reader_workbench_v1.md` (branch `docs/reader-workbench-spec`, read at `8deb75be`) owns the inside of the Reader. §12 lists where the two documents agree and what is still to settle.

**What this document changes.** No data contract changes, except the additions §10 names (`add_source`, a preparing state for `reader_pdf_view`, a status line on library cards, auto-apply on the automatic build path, routing on ChatGPT sign-in, one consent record).

**Inputs**
- **The request.** The owner asked to recall Scott Jenson's Ubuntu Summit talk and Andy Matuschak's *How might we learn?* and his OS-level spaced-repetition note, and to use them on the whole app. Their own diagnosis of the problem: *"When running learnloop by a tester user, they said that the UX was very confusing to them, especially how to ingest canonical sources. I think we were overly focused on making everything transparent/observable/controllable instead of frictionless and easy to use when making a lot of aspects in the UI."*
- **Research,** read for this document. §2 and §3 summarise it; `docs/ux/research_notes.md` has the full quotes and links.
- **An audit of every screen.** I read the code at `57d31c63`, and rendered most screens headlessly against copies of a fresh library and a fixture library (Appendix A). This was not a usability session. `docs/ux/audit_current_screens.md` holds the findings with file and line references.
- **Owner decisions this design builds on:**
  - `docs/specs/daily_loop_frictionless_defaults.md` (cited as **DL** plus the decision id, e.g. DL C2);
  - `docs/brainstorming/LearnLoop_User_Intentions_v2.md`;
  - `spec_source_ingestion_v2.md`;
  - `spec_new_improvements.md`.

**Conventions**
- *Italic phrases in wireframes and tables* are proposed learner-facing copy.
- `Code-formatted phrases` are today's strings or identifiers.
- "Audit A.4" points to `docs/ux/audit_current_screens.md`, part A, section 4.

---

## 0. The design on one page

A new learner should be able to **drop in a book and be reading within seconds**. Structuring, study-map building and question writing happen in the background with good defaults, and nothing in that path asks a question. Everything LearnLoop now shows (receipts, ladders, probabilities, queues, switches) still exists, but **one click away on the thing it concerns, or under the hood**. It is no longer on the learner's path.

Ten moves:

1. **One verb to start: Add.** Drop a file anywhere, paste a link, or choose a file. The Reader opens on it at once, and LearnLoop prepares the rest while the learner reads (§6). The first run has no vault wizard, no subject, no level, no page range, no token budget, no role, no consent checklist and no proposals review.
2. **Four places, not nine tabs.** Today · Library · Reader · Progress, plus *+ Add*, the palette and a `⋯` menu (§5). Ingest, Proposals, Registry and Maintain stop being destinations.
3. **Three layers, and each thing belongs to one.** The surface shows what to do next. *details ▸* and *why?* sit on the object they explain. *Under the hood* is one place for the machine. Ten placement rules decide which layer a thing goes in (§4).
4. **Automatic with undo, instead of asking first.** Study maps that pass the checks apply themselves and can be undone. Consent is asked once, per provider. Cost is shown only when it is unusual (§6.5, §6.6, after Matuschak's "not right now", N6).
5. **Today is one sentence and Enter.** *25 minutes today: finish §5.4, then 6 short questions from last week.* There are no counts of anything waiting, sessions start without being asked for, and the streak sits quietly in the footer (§7.1, after "program attention", N2).
6. **Learning starts in the book.** The first question arrives at the end of the first section the learner reads. Highlights, questions and tries become practice without anyone writing cards. Practice and feedback go back to the passage they came from (§6.8, §7.5, M1, M2, N1).
7. **Feedback shows what matters.** It gives the verdict in words, the learner's answer next to a full answer, one sentence on what went wrong, one next step and a Next button. The diagnosis machinery is behind *why?* (§7.5).
8. **The well answers three questions at a glance.** *What can I do on my own? What's fading? What's next?* Titles replace IDs, *next* is drawn on the map, and the map holds still (§7.6). The owner's contract for the well is kept.
9. **One vocabulary for evidence, shared with the Reader.** `○` not tried yet, `◌` with help, `●` on your own, and *assumed known — not tested yet*. No percentages appear on the learner's surface (§4.2 rule 9).
10. **Plain words, enforced by tests.** A glossary maps every internal term to learner words or hides it (§9). A deny-list test fails the build when a learner-facing component renders jargon. A short checklist (§4.4) is run before a screen ships.

**Ingest, before and after** (§6.8). Adding a textbook and reading it takes about 20 actions today, with 4 required decisions and about 25 internal terms. The first page comes after tens of minutes of extraction, building and review. After the redesign it takes **1 action, 0 decisions and 0 internal terms**, and the first page is visible **under 10 seconds** after the drop. The first question arrives at the end of the first section.

---

## 1. What a newcomer meets today

This is the tester's path, reconstructed from the code. §11 sets out how to measure it properly.

1. **They launch the app** (dev build) and land on someone else's study map. With no remembered library, the shell opens the tracked `fixtures/linear_algebra` vault, which is the owner's working vault, or the repository root (`src-tauri/src/sidecar.rs:696-719`).
2. **The first screen is Start.** It shows an animated backdrop with a `backdrop:` debug chip, then *ready to practice?*, minute chips and a plan line in internal lanes (`maintain 13 · repair 4 · new 4 · push 4`). On older vaults it shows `scheduler mode short_session — probe_eig suppressed (≤20 min)` and tiles for `due now · probe queue · later today · follow-ups`.
3. **The top bar has nine tabs:** `[1]Start [2]Today [3]Graph [4]Ingest [5]Proposals [6]Registry [7]Library [9]Reader [0]Maintain`. The digits are Alt chords, and on Today plain digits open questions instead.
4. **To begin, the learner has to find `+ create a new vault ▸`.**
   - The wizard defines a vault as *"a folder LearnLoop owns: your concepts, evidence, practice items, and the SQLite state behind them."*
   - It then opens a second dialog, `NEW VAULT SETUP · GUIDED INGEST · 01 source + pages → 02 inventory budget → 03 review + build`.
   - That dialog has token budgets per unit, a source role, an "enrichment adjunct" switch, a brief and an external-AI consent checklist.
   - If the learner skipped the *optional* subject, the dialog's *Analyze →* button stays disabled and nothing says why.
5. **The build runs in the background for many minutes.** It ends as a proposal on another tab, which the learner must accept item by item while reading raw IDs and `auto_apply / review_required`.
6. **Nothing on the Ingest screen says "read".** The Reader is the ninth tab. Its picker hides every source that isn't ready behind *"{n} sources are still getting ready."* On first open it can flash an instruction to edit `learnloop.toml` (audit C.2).
7. **Practice needs a session that is started separately.** Feedback has no Next button. It never shows the question, the learner's answer or the correct answer. Instead it shows a Kalman-update chart, FSRS parameters, `bayesian 1.42 nats > τ 0.90`, and four separate ways to rate the diagnosis (audit A.4).

None of these screens is careless. **Every one of them answers a question that LearnLoop's owner and builder needed answered**: Did the gate pass? Why was this item chosen? How much did that answer move the estimate? The app is the instrument panel of a research system, and the instrument panel is the front door. The fix is not to remove the instruments. It is to give the learner a different door.

---

## 2. What the talks and notes teach, and what each changes in LearnLoop

**How to read this section.** Quotes are verbatim from what was read (§2.4 lists the sources and how far to trust them). The Jenson quotes come from YouTube's auto-generated captions of the talk, so they may carry transcription slips; the time code is the start of the caption chunk. Anything about LearnLoop is this document's inference, and each row names the change it drives.

### 2.1 Scott Jenson, "Are we stuck with the same Desktop UX forever?" (Ubuntu Summit 25.10, London, October 2025)

The talk is mostly about how open-source teams do design, not about learning apps. Four of its ideas, and his own write-ups that it points to, bear directly on LearnLoop.

| # | What Jenson says | What it means here | The LearnLoop change |
|---|---|---|---|
| **J1** | **Start here first.** Apps "show you EVERYTHING at the very beginning hoping you'll get it all in this one shot. Of course, we all know what happens: skip, skip, skip…." Apps "offer users a large toolbox and let them figure out how to get started"; games "have a clear understanding of the journey and say 'Start here first'" ([How Video Games Inspire Great UX](https://jenson.org/games/)). | The first thing a new learner sees today is nine tabs (`Start · Today · Graph · Ingest · Proposals · Registry · Library · Reader · Maintain`), a "scheduler mode" box and a "+ create a new vault ▸" link. Nothing says *start here*. | First run has one action: **Add a book, paper or video**. Everything else appears when it has something to show (§6). |
| **J2** | **Hints that teach, not dialogs that stop you.** "for App UX, hints are exactly the opposite, usually dialog box prompts in your face that stop you dead in your tracks!" Games "use hints constantly and patiently to move users to the next level" ([games](https://jenson.org/games/)). | Onboarding today is a modal wizard, a second modal (`Quick add → study map`) and a banner (`SETUP 03/03`) that explains inventories and synthesis. | No wizard and no setup banners. Each place teaches its next step in its own empty state, in one sentence, the first few times (§7 empty states). |
| **J3** | **Learning loops.** "The user has a mental model and they have an intent. So then they look on the screen and they find an affordance to do their action and they get a result which gives them feedback. And then … you go back the loop and you learn." ([talk, 21:56](https://www.youtube.com/watch?v=1fZTOjd_bOQ&t=1316s)) | Adding a source breaks the loop. Its result (a study map) lands minutes later on a different tab (`Proposals`) as something to review, so the learner never sees the effect of their action. | The result of *Add* is the book, open, within seconds. Background work reports on the book itself ("questions for Chapter 1 ready"), where the learner is already looking (§6). |
| **J4** | **Don't rush; keep a boring, consistent base.** "the most common product mistake is rushing. People just go, go, go. They just cram things in, put in put in more menu items, put in more icons." ([24:13](https://www.youtube.com/watch?v=1fZTOjd_bOQ&t=1453s)) "this boring base is powerfully consistent … we always underestimate how important consistency is." ([25:54](https://www.youtube.com/watch?v=1fZTOjd_bOQ&t=1554s)) | Every spec since July added its own surface: a tab, an overlay, a banner or a panel. The app has 9 top tabs, 13 shell-level overlays and dialogs, 328 sidecar methods and 123 top-level CLI commands. Each "why" panel, receipt and switch has its own layout. | Four places, one verb for each (§5). One disclosure pattern everywhere (`why?` and `details ▸`, §4.3). New features extend the loop (read → answer → feedback → plan) instead of adding a tab. |
| **J5** | **Designers think statistically.** "programmers think mathematically and designers think statistically … Programmers tend to be in the might category … They find every possible problem." ([18:36](https://www.youtube.com/watch?v=1fZTOjd_bOQ&t=1116s)) He never says "design for the 80%"; that framing is ours. | The add-a-source dialog asks about every case that *might* matter: page ranges, the PDF engine, token ceilings per unit, the source's role, "enrichment", the brief, whether the Reader is on, and a consent checkbox per stage. | Handle the common case with defaults, and handle the "might" cases when they actually happen: a scanned PDF gets OCR, an expensive build asks once, a failed build shows one fix. All the choices stay available under *More options* and *details* (§6.4). |
| **J6** | **Settings are a cost, and so is their absence.** "UX designers in general don't like … settings that much. I realize that's not a popular opinion here." ([5:44](https://www.youtube.com/watch?v=1fZTOjd_bOQ&t=344s)) On Hacker News, seba_dos1: "rarely is not never, and when I do really need an option, it better be there … both ends of it make the user miserable" ([46261836](https://news.ycombinator.com/item?id=46261836)). rcxdude: "think about how these options interact and compose at the start" ([46262843](https://news.ycombinator.com/item?id=46262843)). | Fewer settings on the surface, not zero. The owner is a power user and must keep every switch. | Settings opens on the five choices a learner makes. Everything else stays, under *Advanced*, searchable (§7.8). Kill switches stay where they are and stay working. |
| **J7** | **Mature technology looks like infrastructure.** "The user has no idea an LLM is even involved; they just get better results." "a mature technology doesn't look like magic; it looks like infrastructure." ([Boring is good](https://jenson.org/boring/)) | Pipeline stages are on screen as vocabulary: *extraction*, *inventory*, *synthesis*, *proposal*, *external AI consent · synthesis*. | Show AI authorship where it matters to trust: model text looks different from the book's text and from the learner's (the Reader doc's three voices). Pipeline stages never appear on the surface. |
| **J8** | **Change gently.** "Users always don't like change … How do you roll it out in a way that is sensitive and doesn't like freak them out and can be done slowly." ([9:36](https://www.youtube.com/watch?v=1fZTOjd_bOQ&t=576s)) HN, rustcleaner: "AVOID BREAKING MUSCLE MEMORY AT ALMOST ANY COST!" ([46269308](https://news.ycombinator.com/item?id=46269308)) | The owner has months of muscle memory: `alt+1..0`, `^p`, the terminal look. | Ship the new shell behind a kill switch (`ui.shell = "simple" \| "classic"`). Every demoted screen stays one palette command away under its old name. Keep the look and the palette (§10). |

### 2.2 Andy Matuschak, "How might we learn?" (UCSD Design@Large, May 2024)

| # | What Matuschak says | The LearnLoop change |
|---|---|---|
| **M1** | **Guidance woven into the real activity.** "we bring guided learning to authentic contexts, rather than thinking of it as a separate activity" ([§design principles](https://andymatuschak.org/hmwl/#design-principles)). "This AI system isn't trapped in its own chatbox, or in the sidebar of one application." ([§guidance in action](https://andymatuschak.org/hmwl/#guidance-in-action)) | The Reader is where learning starts. Questions arise at the end of the section being read, and Today continues what the Reader started (*Continue §5.4 · 12 min*). Ingest, Proposals and Registry stop being places the learner has to visit. |
| **M2** | **Your reading feeds your practice.** "those annotations won't end up trapped in this PDF: they'll feed into future discussion and practice" ([§contextualized study](https://andymatuschak.org/hmwl/#contextualized-study)). | What the learner highlights, asks and tries in the Reader becomes candidate practice in the background, and Today draws on it. The learner never writes a card or files a capture. This is already the direction of `daily_loop_frictionless_defaults.md` (C1–C3); this document gives it its place in the shell. |
| **M3** | **A personal path through a big book.** "the AI reassures Sam that they don't necessarily need to read this entire thousand-page book right now … It's made a personal map in the book's table of contents." ([§contextualized study](https://andymatuschak.org/hmwl/#contextualized-study)) | Adding a whole textbook is fine. LearnLoop builds questions for the chapter being read and the next one, not all 24 chapters at once. The Reader's Guide (Reader doc §4.11) shows the path. |
| **M4** | **The system schedules; the learner gets a nudge.** "one week later, you'll get an email that says: 'Hey, you've probably started to forget some of what you read. Do you want to take five minutes to quickly review that material again?'" ([§practice and memory](https://andymatuschak.org/hmwl/#practice-and-memory)) | Today offers one sentence and one key: *25 minutes today: finish §5.4, then 6 short checks from last week.* There are no queue counts, no "scheduler mode", no "probe queue". |
| **M5** | **Practice is varied, ambient and steerable.** "They install a home screen widget, which ambiently exposes them to practice prompts drawn from highlights, questions asked, and other activity"; "it's important that Sam can steer them with feedback" ([§dynamic practice](https://andymatuschak.org/hmwl/#dynamic-practice)). | Every question carries in-place steering: *too easy*, *not for me*, *this question is wrong*, *write what you can*. There is no queue to manage. Phone capture and phone answers (`spec_mobile_tailnet_v1.md`) are the ambient channel. |
| **M6** | **No deficit framing.** Chatbot tutors "view me as defective until I say the right things" ([§chatbot tutors](https://andymatuschak.org/hmwl/#chatbot-tutors)). "The famous 'bicycle for the mind' metaphor is better because it has no agenda other than the one you bring." ([§ethics](https://andymatuschak.org/hmwl/#ethics)) | Feedback names the mix-up and the next step, never a trait or a "misconception id". Today speaks of *threads to pick up*, never of debt or *overdue*. This matches the Reader doc's U6 and U12. |
| **M7** | **Workings on request.** On the AI-built figure: "At any time, Sam can just 'view source' to tinker" ([§synthesized dynamic media](https://andymatuschak.org/hmwl/#synthesized-dynamic-media)). | The glass box stays, but behind *why?* / *details ▸* on the object and in **Under the hood** (§4). |

### 2.3 Matuschak's notes on memory systems

| # | Note and quote | The LearnLoop change |
|---|---|---|
| **N1** | [OS-level spaced repetition system](https://notes.andymatuschak.org/zNLoqjEVe5dheMKmTTyB9E3): "What if, rather than living 'inside an app's shoebox', as in Anki and other existing tools, prompts were framed more like files in folders—readable and writable throughout the system?" "You'd import these prompts as you read, just as your browser forms a history as you read." "the system may create tentative SRS prompts based on links you've bookmarked or phrases you've searched for repeatedly." | **Tentative by default.** A highlight, an Ask, a phone photo or a pasted link can become practice *tentatively*, created by LearnLoop with undo and adopted with one tap, never through a review queue. Practice reaches the learner wherever they are: at the end of a section in the Reader, in Today, or on the phone. The vault's plain files (Markdown and YAML) are already "files in folders", which keeps that promise for the owner. |
| **N2** | [Spaced repetition systems can be used to program attention](https://notes.andymatuschak.org/zB92WZZ5baBHKZPPbWMbYEv): "you can make a coarser decision—to devote your attention to SRS practice for 10 minutes—and then let your attention be directed by the machine within that block." | **One decision a day:** the minutes, remembered and changed with one tap (DL P4). Begin is Enter. The machine does the bookkeeping. |
| **N3** | [Regular spaced repetition memory practice is an onerous habit to adopt](https://notes.andymatuschak.org/z3DiwZKDuLxMV17mt2nWH7y): "a successful Spaced repetition memory system must deliver significant personal value immediately … Most systems don't: they're an empty box meant for the user to fill." [Onboarding depends on a critical mass of content](https://notes.andymatuschak.org/zPUXHmQEkd33qkuTCnvKVL6): "the prompts presented in the first few weeks of practice play an outsized role." | **Day one is never empty.** One added book gives a readable book at once and questions on its first section within minutes. Today's first plan is *read*, not *Nothing due today*. |
| **N4** | [The mnemonic medium's design relies on light-weight prompts](https://notes.andymatuschak.org/zCfJ4TfWWa24aKoRS7dpNc5): "Quantum Country's median prompt review time is 6 seconds." "If prompts were weighty like a textbook exercise, many readers would pick and choose … That extra decision makes each prompt even heavier!" | **Honest gap.** LearnLoop's questions are written answers graded by a model. They are heavier than one-tap cards, and a model call adds a wait. In-reading checks stay short ("one or two lines"). Heavy problems are planned as timed blocks with *about N min*, so the learner chooses the block, not each prompt (§3, row F6). |
| **N5** | [The critical thing to optimize … is emotional connection to the review session](https://notes.andymatuschak.org/zPiRwRHQxGfF9Zej765PB8M): "ruthlessly minimize elements which provoke a sigh." | A **sigh audit** of every learner screen (§4.4): counts of waiting things, "system debt", red, internal words, waits without a known end, setup banners. |
| **N6** | [Software interfaces often harmfully frame destructive operations as final decisions](https://notes.andymatuschak.org/z4xE8FBHhDo5pTvJuCBPRYC) and [Spaced repetition can lower the stakes around destructive … operations](https://notes.andymatuschak.org/zJ5Yzvba2729XKXivBBZ91J): "If you recast the destructive operations as 'not right now,' they feel completely different." | **Accept and reject become undo.** Study maps that pass the checks apply themselves, with *undo*. Proposals become review-by-exception (§6.5). Retiring a question means *not now* or *not for me*, with an optional reason. |
| **N7** | [Inboxes only work if you trust how they're drained](https://notes.andymatuschak.org/zGKqPvetpYbvbXmPmuuvfx8) and [Beware automatic import into the reading inbox](https://notes.andymatuschak.org/zL2SPWGitsD4TruNYBzSZ7s): "the reading inbox may intermittently become intimidatingly long. That discourages you from opening it." | Auto-generated questions **never show as a count**. Today drains them inside the minute budget. Generation follows reading progress, so one textbook can't drop 400 questions on the learner. |
| **N8** | [The mnemonic medium should give readers control over the prompts they collect](https://notes.andymatuschak.org/z8kPkXQZ3wVR5DfJ79uhnuz): "readers should be able to disable or skip prompts that don't resonate; readers should be able to make simple edits to authors' wording." | Control lives **on the question**: edit, *not for me*, *this is wrong*. It is not a Proposals screen or the Registry. |
| **N9** | [Peripheral vision](https://notes.andymatuschak.org/z4geAr5cERWdJPrdhU5gy3N): "Software systems, by contrast, often lack this kind of peripheral vision." "Unchanging peripheral vision desensitizes." | The Library shelf (each book's place and what's ready) and the well on Progress give peripheral vision. Both change visibly when something changes (*since last time*). Static banners that never change go (`SETUP 03/03`, the scheduler-mode box). |
| **N10** | [Self-graded systems outperform machine-graded systems in most respects](https://notes.andymatuschak.org/zScaVuH9r2pwo24iD3f39bU), though machine grading "can perform more advanced knowledge modeling." | **A real tension, kept.** LearnLoop grades with a model because diagnosis needs it (ADR-016). The cost is trust. So contesting a grade is one tap and visible on every feedback screen (*I think I was right*). That is acceptance criterion 8 (contestability) in `LearnLoop_User_Intentions_v2.md`. |

### 2.4 Sources and how far to trust them

- **Jenson talk:** "Are we stuck with the same Desktop UX forever? | Ubuntu Summit 25.10", <https://www.youtube.com/watch?v=1fZTOjd_bOQ> (uploaded 2025-12-11; 43:30). The schedule abstract is at <https://discourse.ubuntu.com/t/are-we-stuck-with-the-same-desktop-ux-forever/67253>. The quotes are YouTube's auto-generated captions, read in full; there is no human transcript. The slides aren't online.
- **Jenson's posts:** [games](https://jenson.org/games/), [boring](https://jenson.org/boring/) and [paradox](https://jenson.org/paradox/), read in full.
- **Hacker News:** item 46256834, read in full via the Algolia API (205 comments). Neither the talk nor the thread uses the phrases "design for the 80%" or "progressive disclosure"; those framings are this document's.
- **Matuschak:** *How might we learn?* (<https://andymatuschak.org/hmwl/>) and the linked notes, read from the server-rendered pages. The owner's copies of several notes are in `docs/specs/spec_andymatusnotes.md`, and the quotes above match them where they overlap.
- **Supporting file:** `docs/ux/research_notes.md` has the longer quote set, with HN usernames and comment links.

---

## 3. The pain points of textbooks, videos and flashcards, and what LearnLoop does about each

How to read the table:
- **Evidence** cites what was read (`docs/ux/research_notes.md` has the full list). Forum and HN quotes are anecdotes chosen for clarity; they are not data on how common a problem is.
- **Today** describes the app at `57d31c63`.
- **Status:**
  - **✓** LearnLoop addresses it.
  - **◐** It addresses it partly, or only once this redesign ships.
  - **✗** It doesn't yet.

### 3.1 Studying from a textbook

| # | Pain point | Evidence | LearnLoop today | With this redesign | Status |
|---|---|---|---|---|---|
| **T1** | **Rereading and highlighting feel productive but do little** | Dunlosky et al. 2013 rate rereading and highlighting "low utility"; practice testing and distributed practice "high utility". Karpicke, Butler & Roediger 2009: "many students experience illusions of competence while studying". Kuhbandner & Emmerdinger 2019 counter that rereading is mostly "rereading not understood parts". | The Reader has section-boundary quick checks, "write my own question" and Ask. But the checks need *read closely* mode, and they disappear silently if writing one times out (audit C.3). | The first question arrives at the end of the first section the learner reads (§6.8), and the section-end check is a reliable part of reading rather than a hidden mode. Highlights remain, but a highlight is never shown as progress (Reader doc §8). | ◐ |
| **T2** | **"It makes sense when I read it, but I can't do the problems"** (the fluency illusion) | Bjork & Bjork 2011: rereading gives "a sense of familiarity or perceptual fluency that we interpret as understanding". r/math: "I feel like I understand things, but I can't solve problems." | Practice is written answers graded by a model, with cold checks and an evidence model that never counts reading as mastery (P3 invariant 6). | Unchanged in substance. The surface now says it plainly with `◌ with help` vs `● on your own`, the same marks the Reader uses. | ✓ |
| **T3** | **No feedback on exercises; no solutions** | r/learnmath: "I have no way to know whether this answer I feel good about is completely wrong or not, so I feel it's a waste of time to do these problems." Matuschak: "Readers must run their own feedback loops." | "add exercise to practice" imports a book's exercise verbatim, and the model writes the key, rubric and hints. The Reader doc's workbench (RW2) checks steps. | The import becomes *work through this* (Reader doc §5). The shell's part is that practice opens at once and feedback returns to the exercise (§7.5). | ◐ (RW2 is not built) |
| **T4** | **Not knowing what matters in a 600-page book** | Shepherd, Selden & Selden 2012: strong readers "were not effective readers of their mathematics textbooks". Matuschak (HMWL): "they don't necessarily need to read this entire thousand-page book right now". | The Reader Guide marks some passages *worth a second look*. Quick add picks "the most relevant units" by keyword, which a newcomer never sees. | The Reader doc's reading paths (§4.11). Questions are built in reading order (§6.4), so what LearnLoop asks about follows what the learner reads. | ◐ |
| **T5** | **Prerequisite gaps turn helpful difficulty into blocking difficulty** | Bjork & Bjork 2011: without the background, difficulties "become undesirable difficulties". Hailikari et al. 2008: prior procedural knowledge predicts achievement. | Learner-text gap naming (prerequisites are created on first sighting) and the concept graph. The diagnoser names a missing prerequisite. | On feedback, a named gap becomes one next step: *This needs conditional probability first · 5 min*. It is not a misconception id or a graph edit (§7.5). | ◐ |
| **T6** | **Notation** | HN: "the pages full of bizarre elongated Greek letters… just induces a bit of panic." The evidence for adults is weak. | Ask about a selection, and "explain differently". | Unchanged. Reader doc territory. | ◐ |
| **T7** | **Losing your place and momentum across weeks** | Anecdotal. Nielsen on returning after months; Matuschak, Peripheral vision. | Reading position is restored per source. The Reader picker's "Pick up where you left off" shows no position (audit C.2). | Book cards show where you are (*§5.4 · 2 days ago*). Today offers *Continue §5.4 · 12 min*. The Reader doc's *Last time here* card. | ✓ after Phases 1 and 3 |

### 3.2 Learning from videos

| # | Pain point | Evidence | LearnLoop today | With this redesign | Status |
|---|---|---|---|---|---|
| **V1** | **Fluent explanations inflate the feeling of learning** | Carpenter et al. 2013: "Perceived learning was significantly higher for the fluent instructor… lecture fluency did not significantly affect the amount of information learned." Deslauriers et al. 2019: active learners "learned more… but their perception of learning… was lower". | Watch mode with tutor pause points (`reader.watch_plan`). | Each pause point is a question about the last few minutes, offered the way a section-end check is. The shell treats a video like a book. | ◐ |
| **V2** | **Watching is not doing** | Kardas & O'Brien 2018: "repeatedly watching others can foster an illusion of skill acquisition… experiencing a 'taste' of performing attenuates the illusion." r/learnmath: "I can't do a single integration problem." | The same practice loop as books. | Unchanged. The plan mixes *watch* blocks with *practise* blocks. | ✓ |
| **V3** | **Mind-wandering with no retrieval** | Szpunar, Khan & Schacter 2013: interpolated tests "discourage task-irrelevant mind wandering" (40% mind-wandering without them). Guo, Kim & Rubin 2014: median engagement "at most 6 minutes". | Pause points exist, but how often they come is model-chosen and isn't visible. | The default is a short pause question about every 6–8 minutes, which sits with Guo's 6-minute finding. *Skim* turns them off (Reader doc). | ◐ |
| **V4** | **Hard to search inside a video and hard to tie it to notes** | NoteVideo (CHI 2013); Visual Transcripts (2015). Kim et al. 2014: transcript tools were preferred, but "no significant differences were found in task performance". | Synchronized transcript with find. Highlights anchor to transcript cues. | Unchanged. Adding a YouTube link is now one paste (§6). | ✓ |

### 3.3 Flashcards and spaced repetition (Anki and friends)

| # | Pain point | Evidence | LearnLoop today | With this redesign | Status |
|---|---|---|---|---|---|
| **F1** | **Writing cards is a skill and a time cost** | Matuschak: "writing 40 prompts will add 30-60 minutes of effortful work"; "it's not obvious when the prompts you've written are bad". Matuschak & Nielsen: "making good cards is a difficult skill to master". HN: "manually making cards was too tedious." | The model writes questions from the source (study-map synthesis, quick checks, rung variants). The learner *can* write their own. | The learner never has to write one. Their highlights, asks and tries become tentative practice automatically (N1, M2). | ✓ |
| **F2** | **Cards cut off from their source ("orphans")** | Nielsen: "avoid lonely orphans: single questions that are largely disconnected from everything else." r/Anki: flashcards "**dis**connect them from the big picture". | Every generated item cites the passage it came from (span provenance). | Feedback always offers *see it in the book* (opens the Reader at the passage, Reader doc RW6b), not "view in Library", which today opens a raw file (audit C.1). | ✓ after Phase 4 |
| **F3** | **Memorizing the card, not the idea** | Matuschak, prompts guide: "you might eventually memorize the shape of that question… through a mechanical pattern association". | Rung variants (easier/harder), practice families and transfer questions vary the surface. | Unchanged. *Ask me differently* stays on every question. | ✓ |
| **F4** | **Review piles, "review debt" and quitting after a break** | Nielsen: "It's intimidating to come back to find you have 500 cards to review." Anki manual: "has become overwhelmed by the reviews required." HN: "the huge backlog is too much that I give up." r/Anki: "declare bankruptcy, delete the deck". | The finite daily plan (DL1) and re-entry plans (DL P6). But Start still shows tiles reading *due now · probe queue · later today · follow-ups* (`StartScreen.tsx:1795-1800`), and Today shows queue counts. | **No count of waiting things anywhere** (§4.2 rule 10). The plan is minutes. Re-entry after a break is a short plan with no debt screen. New material slows automatically when reviews run long (the plan's split already does this; DL P3). | ✓ after Phase 3 |
| **F5** | **Dread: "my memory feels worse than it is"** | Matuschak: SRS "make you feel like your memory is worse than it really is". r/Anki: "All my material is super mega difficult". | No counter-signal. Feedback lists errors and misconceptions. | Feedback and the session summary lead with what you showed (`●`) and what came back (*since last time*), as the Reader doc's S10 does (§7.5). | ◐ |
| **F6** | **Heavy prompts invite picking and choosing** | Matuschak: QC's "median prompt review time is 6 seconds"; weighty prompts mean readers "pick and choose". | Written answers graded by a model (seconds of waiting each), plus worked problems. | **Honest gap.** In-reading checks stay short. Heavy problems go into plan blocks with *about N min*. A lighter one-line answer type for recall checks is worth exploring; it is open question Q19 for the owner, out of scope here. | ✗ / ◐ |
| **F7** | **Rigid due dates** | HN: "I just want to practice when I feel like it… and not feel like there's a backlog building up." | The plan picks by value within minutes. It is not a due list. | Unchanged. *Keep going* after the plan, and no *overdue* anywhere. | ✓ |
| **F8** | **"Ease hell" (SM-2)** | Anki FAQ: cards "stuck in 'low interval hell'". FSRS FAQ: "solved by mean reversion of difficulty". | Scheduling uses FSRS-style state (`practice_item_state`: stability, retrievability) with an evidence model on top. No ease factor. | Unchanged, and invisible. | ✓ |
| **F9** | **Settings overload and setup friction** | Anki manual: "Make sure you understand the options before changing them." HN: "Anki feels like Microsoft Word." r/Anki: "An app that has a 200 pages manual has lost the popularity race". | 9 settings sections, about 28 controls and N modality checkboxes (audit B.11), plus a vault wizard and a build dialog with token budgets. | Five settings on the surface. Everything else is in Advanced. No setup step before reading (§6, §7.8). | ✓ after Phases 1 and 6 |

### 3.4 Learning apps in general, and the self-directed adult

| # | Pain point | Evidence | LearnLoop today | With this redesign | Status |
|---|---|---|---|---|---|
| **G1** | **Onboarding drop-off** | Reich & Ruipérez-Valiente 2019: "52% never enter the courseware". Education-app 30-day retention is about 2–4% (one industry figure, verified only from a search snippet). | No first run (audit C.5). | §6. | ✓ after Phase 1 |
| **G2** | **Feature fatigue** | Thompson, Hamilton & Rust 2005: "too many features can make a product overwhelming… and difficult to use". Choice overload is real but inconsistent (Scheibehenne et al. 2010 found a mean effect "of virtually zero"). | 9 tabs, 31 palette commands, 12 selection actions. | Four places, one Add and the glass box on demand (§4–§5). The aim is not "fewer options as a law" but one obvious path. | ✓ after Phase 2 |
| **G3** | **Streak anxiety vs. streaks that help** | Duolingo: losing a streak "can… feel quite *de*motivating", but 7-day streaks correlate with completion. Silverman & Barasch 2023: broken-streak drop-off is "attenuated when consumers can 'repair' a broken streak". Lally et al. 2010: "Missing one opportunity… did not materially affect the habit formation process." | A day streak on Start (owner decision P5). | Kept, and kept quiet. It is a forgiving count (*4 days · best 9*), never red, and absent from the Reader. Q20 proposes one repair day per week, the owner's call. | ◐ |
| **G4** | **Opaque algorithms lose trust** | Dietvorst et al. 2015: confidence is lost faster in algorithms after a mistake. Dietvorst et al. 2018: people use an imperfect algorithm more "when they could modify its forecasts", even slightly. | Total transparency on the surface (scheduler weights, EIG, Brier). | **Small overrides beat big dashboards.** *too easy*, *not for me*, *I know this*, *I think I was right* and *undo* on every automatic decision. *why?* is one click away. | ✓ |
| **G5** | **Dashboards that don't help** | Matcha et al. 2019: learning-analytics dashboards "rarely grounded in learning theory… do not offer any information about effective learning tactics". | Maintain (about 40 metric blocks), Strata, Terrain and the Well with ids. | Progress answers three questions in words (§7.6). The analytics move under the hood. | ✓ after Phase 5 |
| **G6** | **No structure, and deciding what's next** | Bjork, Dunlosky & Kornell 2013: people "are prone to both misassessing and mismanaging their own learning". Kizilcec et al. 2020: self-regulation nudges "raised student engagement in the first few weeks but not final completion rates." | The finite plan decides (DL1). | Today's one sentence plus Enter (N2). The plan's *why?* explains each choice when asked. | ✓ |
| **G7** | **Effortful learning feels worse** | Deslauriers et al. 2019: learners "take that effort to signify poorer learning". Kornell & Bjork 2008: learners rated massing above spacing "even after their own test performance had demonstrated the opposite". | Not addressed in copy. | Feedback names effort as normal ("This one's meant to be hard to recall. That's what makes it stick."), at most once a session, in details for the curious. Satisfaction ratings are not used to tune practice (the Reader doc does the same, §9.3 point 4). | ◐ |

---

## 4. The core diagnosis, and where the glass box belongs

### 4.1 Where the app over-exposes

The audit found eight patterns. Each row is one pattern, with examples (all from the audit) and how many places it shows up.

| Pattern | Examples | How widespread |
|---|---|---|
| **The pipeline is the navigation** | Ingest, Proposals, Registry and Maintain are top-level tabs. *Import source*, *＋ create study map*, *outline & select →* and collections' *synthesize →* all start the same journey. Help text explains `source revision + extraction`, inventories and synthesis. | 4 of 9 tabs. Ingest's four help paragraphs (`IngestScreen.tsx:1530-1572`). |
| **Model internals shown as content** | `priority = Σ wᵢ · componentᵢ` with hard-coded weights. `Ready variance 0.0123`. `stress 0.12`. `logit-space Kalman update`. `bayesian 1.42 nats > τ 0.90`. `pooled Brier 0.183`. `FSRS interval factor 0.85`. `entropy 1.23 nats`. | Today, Feedback, Progress, Calibration, Exam, Inspector |
| **Identifiers used as labels** | The item ULID on every practice card, which opens the inspector and **shows the expected answer**. Raw facet IDs on the well's rim. LO IDs in Strata and Calibration buttons. `selected · {spanId}`. `bbox [x, y, x, y]`. | Most screens. `EntityLink` renders the raw ID by default. |
| **Controls at every level of detail** | Token budget per unit and *no LearnLoop token ceiling*. PDF engine. Five roles. The brief. *Reader on/off*. About 28 settings plus N modality checkboxes. 12 actions per Reader selection plus a 5-item right-click menu. 11 retire reasons. | Ingest, Settings, Reader, Practice |
| **Approval and labelling work handed to the learner** | Accept each proposal. *Was this queue choice useful?* (7 buttons on every focused row). Diagnosis rated up to 4 times per feedback. *Adjudicate diagnoses · N owed*. `window.prompt("Reviewer name?")`. | Proposals, Today, Feedback, Maintain, Registry |
| **Bookkeeping for valid measurement, addressed to the learner** | *"using a hint (or opening it primed) voids the measurement and the attempt will be rejected"*. *"only that converts to Demonstrated credit"*. *"Feedback withheld during the block, released now"*. *"reading is recorded as exposure, not proof"*. | Today, Practice, Feedback, Repair |
| **Engineering states shown as UI** | *"Set `tutor_qa.reader_enabled = true` in learnloop.toml"*. *"the sidecar is unreachable"*. *"restart the app (npm run dev)"*. *"available for mvp-0.7 vaults"*. *"Verifying diagnostic safeguards..."*. | Reader, errors, Inspector |
| **Every message is a red toast** | Errors, notices and successes share one red, persistent toast. About 108 of 197 error sites pass backend text through raw. No toast has a Retry button. | App-wide (`styles/app.css:795`) |

**What is missing, in contrast,** is the simple path:
- There is no first run.
- After adding a source there is no *read* button.
- Practice has no *practise this now*, and Feedback has no Next button.
- Feedback doesn't show the question, the learner's answer or the expected answer.
- The practice exam is hidden in the full list.
- The quick check is reachable only from the palette or the inspector.
- The well is three clicks deep and resets every visit.

**Why it happened.** Every spec since July added receipts, labels, switches, review queues or inspectable state to the UI. Each addition was right for the person debugging the algorithm, and that person was also the only learner. Together they turned the learner's path into the debugger. The owner's own rule (*honest labels, generous defaults*, DL) already points the other way. What was missing is a rule for **where** honesty lives. §4.2 supplies it.

### 4.2 The principle: frictionless by default, the glass box on demand

LearnLoop keeps every receipt, label, switch and log it has. What changes is **where** each one lives. There are three layers, and every element belongs to exactly one of them.

| Layer | What it holds | How the learner reaches it | Examples |
|---|---|---|---|
| **1. The surface** | What to do next, in the learner's words. At most one primary action per screen. **Zero required decisions.** Short, quiet honesty labels. | It is the screen. | *Continue §5.4 · 12 min* · *with help* `◌` · *assumed known — not tested yet* · *AI-written* · *graded by AI · I think I was right* |
| **2. Details** | The answer to "why?" and "where did this come from?" for **the object in front of the learner**: one question, one grade, one book, one plan step. | `why?` or `details ▸` on that object. One click, in place, collapsed again on leaving. | Why this question now · what the grade looked at (rubric) · the passage it came from · what was assumed · the diagnosis behind a repair · which model wrote it and when |
| **3. Under the hood** | Everything about the **system** rather than the object: queues, ladders, token bars, proposals, the registry, calibration, maintenance, raw data, the inspector, spend, health. Plus reports and the CLI. | One place, from the `⋯` menu or the palette (`under the hood`). Never in the top navigation. | Imports & builds · Study-map changes · Subjects & topics · Mistake history · Calibration · Maintenance · Data (SQLite) · Files · Health (`doctor`) · Spend |

**Placement rules.** These are tests a reviewer can apply to any screen or spec.

1. **Next action → surface.** If a fact changes what the learner should do next, it goes on the surface, in words. If it doesn't, it doesn't.
2. **Explains a decision → details, on the object.** If the learner might reasonably ask "why did it do that?", the answer sits one click away on the thing it decided about. It never sits in a separate screen, and never on the surface by default.
3. **About the machine → under the hood.** Health, cost, internals, audit trails, algorithm versions and identifiers live under the hood, in reports or in the CLI.
4. **A decision → a default plus undo.** Before adding a choice to the main path, ask whether a good default with undo would do. If yes, ship the default; the choice moves to *More options* or *details*. A choice stays on the surface only if no default is right for most learners **and** a wrong guess is expensive to undo.
5. **One signal per background job, on its object.** A job reports in one line on the thing it concerns (the book card, the question, the plan step), never on a separate activity page in the main path. The full ladder is under the hood.
6. **Errors: one sentence, one action.** "Couldn't read pages 40–52 — they look scanned. *Try text recognition.*" Codes, stages and diagnostics go in *details*.
7. **Consent once per data flow, not once per action.** Consent is asked when a provider is connected, and again only when what leaves the machine changes (§6.6).
8. **Money only when it's unusual.** Cost appears on the surface only above a threshold or near a cap (the Reader doc's Q7 makes the same rule). Otherwise it is in *Spend*, under the hood.
9. **No raw numbers about the learner on the surface.** No probabilities, Brier scores, posteriors, counts of facets, token counts, IDs or algorithm versions. Evidence uses the well's vocabulary everywhere: `○` untested, `◌` with help, `●` on your own, and *assumed known (not tested)*. It is the same vocabulary as the Reader doc §3.4.
10. **No count of waiting things.** No due counts, *probe queue*, *to review*, *pending proposals* or *system debt* on learner screens. A plan is stated in minutes. Threads are listed as things to pick up, never as totals (Reader doc U12).

**Honest labels stay, but get quiet.** The owner's rule, *honest labels, generous defaults*, holds. Labels shrink to a few plain words in a dim style. The full statement moves into details. For example:

| Today | Becomes |
|---|---|
| `short_session — probe_eig suppressed (≤20 min)` | *(nothing; the plan's minutes say it)* |
| `reader-first: this build creates the study map (concepts, facets, learning objects) with no upfront practice items — questions appear in the reader per section, and practice items build themselves as you complete sections.` | *Questions arrive as you read.* |
| `Nothing a model writes enters your vault directly. Every concept, facet, and practice item arrives as a proposal — you accept, edit, or reject it on the Proposals screen.` | *AI-written · undo* (on the book card, after a build) |
| `no practice items yet — system debt` | *Questions for this chapter are being written.* (or nothing) |

### 4.3 One disclosure pattern

The same two controls work everywhere:
- **`why?`** is a dim link after a sentence that LearnLoop decided: a plan step, a question's arrival, a grade, a repair. It opens a short paragraph, in plain words, with a `details ▸` inside for anyone who wants the evidence.
- **`details ▸`** is a disclosure at the foot of an object: a question, a grade, a book card, a mistake. It holds the receipts: rubric, sources, model, timings, IDs, and the *open in inspector* link for the owner.

Both are collapsed by default, keyboard reachable (`?` opens the focused object's *why?*, `.` toggles *details*) and remembered for the visit only. One owner setting, *Always show details* (Settings → Advanced → For builders), expands every `details ▸` for anyone who wants the instrument panel back.

### 4.4 The sigh audit

Matuschak's rule, "ruthlessly minimize elements which provoke a sigh" (N5), becomes a checklist run on every learner screen before it ships:

- [ ] A count of things waiting (due, queued, to review, pending, debt, overdue)
- [ ] A word from the jargon glossary (§9) on the surface
- [ ] A wait without a known end, or a wait that blocks reading or typing
- [ ] A modal the learner didn't ask for
- [ ] Red, or a trait word about the learner ("weak", "struggle", "misconception")
- [ ] A banner or box that looks the same on every visit
- [ ] A choice the learner must make before they can continue
- [ ] Two ways to do the same thing on one screen (*import source* vs *＋ create study map*)

Each tick is a defect to fix or an exception to justify in the spec that adds it.

---

## 5. Information architecture and navigation

### 5.1 The places a learner goes

A learner does four things: **add** something to learn from, **read** it, **practise** what matters today, and now and then **look at how they're doing**. The shell has one place for each, plus one corner for the machine.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LearnLoop   Today   Library   Reader   Progress              [+ Add]  ^K  ⋯   │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Place | The learner's job | Replaces |
|---|---|---|
| **Today** (home; `Alt+1`) | "What should I do now?" Shows one plan in minutes, Begin with ↵, the thread to pick up, and the streak, quietly. | Start + Today + the session finish HUD |
| **Library** (`Alt+2`) | "My books, papers and videos." Each is a card with its place, readiness and *continue*. My notes live here too. | Ingest (its learner part) + Library (notes) + the Reader's source picker |
| **Reader** (`Alt+3`) | "The book I'm in." Owned by the Reader doc. When no book is open, it shows the Library shelf. | Reader |
| **Progress** (`Alt+4`) | "What can I do now, and what's next?" The well first, then connections, goals and a practice exam when a goal exists. | Graph + Knowledge field + Maintain's exam readiness |
| **+ Add** (button, drop anywhere, `Ctrl+O`, paste a link) | "Learn from this." A file, a link, an arXiv id or a YouTube URL. | QuickAdd, NewVaultWizard's source step, Ingest's input |
| **⋯ menu** | Settings · Under the hood · Switch library · Keyboard & help | the vault chip, the settings chip, the palette-only screens |

**Practice and feedback are not places.** Practice starts from Today's plan, from the Reader (a section check, *work through this*) or from Progress (*practise this*). Feedback is the second half of practice. Both return to where the learner came from (Reader doc S6 for Reader-started attempts; Today otherwise).

**Ctrl+K / Ctrl+P (the palette) stays**, and gets plain-language commands first: *add a book*, *continue reading*, *start today's plan*, *check what I already know*, *open settings*, *under the hood*. The CLI pass-through moves to a `>` prefix (`> doctor`) so plain words never run a CLI command by accident (audit B.0).

### 5.2 Under the hood

One screen, from `⋯ → Under the hood` or the palette. It has a left list of tools and keeps every demoted screen working as it does today, under a plain title, with the old name in small type for the owner's muscle memory:

| Under the hood → | Was | Notes |
|---|---|---|
| **Imports & builds** | Ingest's Activity stack, staging, outline & select, collections, PDF engine, exam seeding | The full durable-batch view: ladders, token bars, cancel, resume, repair, revalidate. Book cards in the Library link here from *details ▸*. |
| **Study-map changes** | Proposals | Review-by-exception inbox. Only items that failed a check, or that the policy routes to review, wait here (§6.5). There is no top-nav badge. |
| **Subjects & topics** | Registry | Unchanged, apart from the title. |
| **Concept graph editor** | Graph's edit mode | Edits apply with undo and an optional reason (§7.6). The geometry preview stays here. |
| **Analyst views** | Terrain, Strata, FacetInspector | Unchanged. |
| **Mistake history** | Review / `diff` ledger | The learner's surface gets the next repair step instead (§7.5). |
| **Calibration** | Calibration sessions (blocks, episodes, entropy) | The learner's *Check what I already know* stays on the surface (§7.6). |
| **System health** | Maintain's measurement and causal health, the feed, conflicts, D3 backfill, probe review, adjudication | Unbadged. Notices that concern a book appear on its card instead. |
| **Data** | SqliteBrowser | Read-only by default, with *allow edits* as a switch. `state.sqlite` disappears from the Library tree. |
| **Files** | Library's vault tree and the proposal payload editor | Unchanged. |
| **Inspector** | InspectorOverlay (`show <id>`) | Reached from any `details ▸ → open in inspector`, and from the palette. |
| **Golden path** | Golden Path (hidden) | Stays hidden behind `SHOW_GOLDEN_PATH`. |
| **Spend & AI routes** | parts of Settings, `learnloop ai status` | Spend by route, caps, latency. |

### 5.3 What happens to every current screen

| Current | Fate | Where it goes |
|---|---|---|
| `StartScreen` | **Merge** | Into Today. The minutes chips, Begin and the streak stay. The backdrop cycler moves to Settings → Appearance. *Scheduler mode*, the queue preview and the fake `11 concepts in scope…` line go. |
| `TodayScreen` + `today/` | **Keep, simplify** | Today (§7.1). |
| `IngestScreen` | **Split** | The learner part becomes *+ Add* and Library cards. The rest goes to Under the hood → Imports & builds. |
| `LibraryScreen` | **Split** | Notes go to Library → Notes. The vault tree, payload editor and SQLite go under the hood. |
| `ReaderScreen` + `reader/` | **Keep** | The Reader doc owns the inside. This doc owns how it is entered and left, and its processing state (§6.3). |
| `PracticeScreen` | **Keep, simplify** | §7.4. |
| `FeedbackScreen` | **Keep, simplify** | §7.5. |
| `DiagnosticReviewScreen` | **Fold** | Becomes a feedback variant: one verdict line and the next step on ↵ (§7.5). |
| `RepairScreen` | **Fold** | A step launched from feedback or from the plan (*Fix this mix-up · about 4 min*), not a destination. |
| `ReviewScreen` | **Demote** | Under the hood → Mistake history. |
| `CalibrationScreen` | **Split** | The quick check becomes a learner verb (§7.6). Full calibration goes under the hood. |
| `ExamScreen` | **Keep** | Entered from a goal on Progress or Today (*Practice exam · 40 min*). |
| `KnowledgeMapScreen` + Well | **Keep, promote** | Progress opens on the well (§7.6). |
| Terrain, Strata | **Demote** | Under the hood → Analyst views. |
| `GraphScreen` | **Split** | A read-only *Connections* view on Progress. The editor goes under the hood. |
| `ProposalsScreen` | **Demote** | Under the hood → Study-map changes (review by exception). |
| `RegistryReviewScreen` | **Demote** | Under the hood → Subjects & topics. |
| `MaintenanceScreen` | **Dissolve** | Exam readiness goes to a goal on Progress. *Update study map* goes to the book card. Conflicts go to the book card when they occur. The rest goes to Under the hood → System health. |
| `SettingsScreen` | **Split** | Five learner settings, plus *Advanced* (§7.8). |
| `SqliteBrowser` | **Demote** | Under the hood → Data. |
| `GoldenPathScreen` | **Stays hidden** | Under the hood. |
| `NewVaultWizard` | **Remove from first run** | `⋯ → Switch library → New library…` becomes a two-field dialog (name, folder). |
| `QuickAddDialog` | **Replace** | *+ Add* (§6). Its options move to *Add → More options*. |
| `InspectorOverlay` | **Demote** | From *details ▸* and the palette only. Bead clicks open the learner card instead (§7.6). |
| `ClaimSurface` on Today rows | **Remove** | One optional *this seems off* link stays on feedback (§7.5). |
| `AdjudicationOverlay` | **Demote** | Under the hood → System health. |
| `CommandPalette` | **Keep** | Plain commands first; CLI behind `>`. |

### 5.4 Keys

| Key | Does |
|---|---|
| `Alt+1` … `Alt+4` | Today · Library · Reader · Progress |
| `Ctrl+O` | Add a file |
| `Ctrl+V` (no text field focused) | Add the link on the clipboard |
| `Ctrl+K` or `Ctrl+P` | Palette |
| `Ctrl+,` | Settings |
| `↵` on Today | Begin or continue the plan |
| `Esc` | Back one layer (Reader doc §3.2 rules hold inside the Reader) |
| `?` / `.` | *why?* / *details ▸* on the focused object |

The old `Alt+5…0` keep working while `ui.shell = "classic"` is selectable (the transition period, §10), and open the matching Under-the-hood tool in the new shell. Muscle memory survives the move (J8).

---

## 6. Ingest and first run, redesigned

**The goal, as a test:** a new user launches LearnLoop, drops in a textbook PDF and is **reading page 1 within 10 seconds**. When they finish the first section, a question on it is waiting. Graded questions on the chapter follow in about 5 minutes. They do nothing to make any of this happen (an AI connection is assumed). They make **no required decision** on the way. Today's specs already set this target: "the first hour must produce learning, not library curation" (`spec_source_ingestion_v2.md` §1); "The user answers their first meaningful question within ten minutes of installation" and "'Create vault' can happen invisibly" (`spec_new_improvements.md`, north-star moment). The UI never delivered them.

### 6.1 First launch

**Today (dev build).** `default_vault_path()` (`src-tauri/src/sidecar.rs:696-719`) opens the last-used vault. Failing that, it opens the first folder in `fixtures-local/`, then the **tracked `fixtures/linear_algebra` fixture**, and failing that the repository root. So a tester either lands in someone else's linear-algebra vault, with its history and a streak, or in a broken one. Rendered with no usable vault, the first screen is a red box: *"LearnLoop could not confirm whether this action completed. Check the current state before trying it again."*, with a `retry vault load` button (screenshot `docs/ux/screenshots/01-first-launch-no-vault.png`). They then have to notice `+ create a new vault ▸` on the Start screen. That link is amber only when the vault has no learning objects (`StartScreen.tsx:1621-1648`).

**Redesign:**
1. **A library exists before the first click.** With no remembered library and no `LEARNLOOP_VAULT`, LearnLoop creates one silently at `~/LearnLoop` (open question Q1) through the existing `create_vault` (`handlers/vault.py:28`). It has no subject and the default starting level, and it is remembered as the last library. The owner's dev order (env var → last-used → `fixtures-local/`) is unchanged. Only the final fallback changes: from the tracked fixture to a fresh library. The tracked fixture still opens with `LEARNLOOP_VAULT=fixtures/linear_algebra`.
2. **The window opens on an empty Library**, and it is welcoming. Wireframe W1:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LearnLoop   Today   Library   Reader   Progress              [+ Add]  ^K  ⋯   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                                                                              │
│            ┌──────────────────────────────────────────────────────┐          │
│            │                                                      │          │
│            │        Drop a book, paper or lecture here            │          │
│            │                                                      │          │
│            │   PDF · web page · arXiv · YouTube · Markdown · text │          │
│            │                                                      │          │
│            │   [ Choose a file… ]     or paste a link: [_______]  │          │
│            │                                                      │          │
│            └──────────────────────────────────────────────────────┘          │
│                                                                              │
│      LearnLoop opens it right away. While you read, it builds questions      │
│      on what you've just read and brings them back when they'll help.        │
│                                                                              │
│      ○ Connect an AI to get questions — Continue with ChatGPT · other…       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

   - The AI line appears only when no route can author questions. It disappears once one can. It never blocks adding or reading.
   - There is no tour, no wizard, no goal step and no "the loop" explainer. Each place teaches itself in its own empty state (J2).
3. **Today, Reader and Progress each have a one-line empty state** that points back to *Add* (§7). None of them is hidden. A visible tab that explains itself costs less than a tab that appears later and surprises.

### 6.2 Adding: one gesture

Every way in leads to the same flow:
- **Drop** anywhere in the window. A full-window drop target appears: *Drop to add to your library*.
- **Choose a file…** (`Ctrl+O`).
- **Paste a link** in the Add box, or `Ctrl+V` with no text field focused.
- *+ Add* in the bar, which opens a small popover with the same three ways.

There is nothing to fill in. The flow:
1. The **kind is detected** from the path or URL, as `detectKind` does today (`IngestScreen.tsx:29-40`). An unrecognised input gets one line: *LearnLoop can't open this yet — it reads PDFs, web pages, arXiv, YouTube, Markdown, text and subtitles.*
2. The **original is registered and stored at once.** This is the fast, local part of today's import job: register plus the originals store (`learnloop/ingest/originals.py`).
3. **The Reader opens on it.** Each kind opens as follows:

| Kind | What opens, and how soon (target) | What is still happening |
|---|---|---|
| PDF (book or paper) | The **original PDF** in the PDF surface, page 1 or the first chapter page. Under 3 s. | Text extraction (Marker, or pypdf as fallback). Chapter detection. Then question building. |
| arXiv id or URL | The paper's PDF or ar5iv HTML. Under 5 s, network permitting. | The same. |
| Web page | The article text (trafilatura). Under 5 s. | Question building. |
| YouTube | Watch mode with the transcript (`youtube_transcript_api`). Under 5 s. | Question building and pause points. |
| Markdown / text / `.vtt` / `.srt` | The text. Under 1 s. | Question building. |
| Audio | A *Transcribing — about N min* card in the Library. It opens when the transcript is ready. | Transcription. This is the one kind that can't be read at once. |

4. **Several files at once** become several books. The first one opens; the rest show on the shelf with their status.
5. **Already in the library?** It opens where the learner left off, with a quiet line: *Already in your library — opened where you left off.* Nothing is duplicated (today's `existingSourceId` preview already knows).

### 6.3 Reading while LearnLoop gets the book ready

The Reader doc owns the inside of the Reader. This doc owns the **preparation state**, because it is where ingest hands off to reading. (Coordination item C3, §12.)

The header carries one quiet status line, which goes away when there is nothing left to say. Wireframe W2:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Library   Probability — Blitzstein & Hwang        p. 1 / 636      skim ▾   │
│ ◐ Getting this book ready · chapters found · questions for Ch. 1 in ~4 min   │
├────────────────────────────────────────────────┬─────────────────────────────┤
│                                                │ Guide                       │
│    [ the original PDF, page 1 ]                │                             │
│                                                │  Chapters                   │
│                                                │   1 Probability and counting│
│                                                │   2 Conditional probability │
│                                                │   …                         │
│                                                │                             │
│                                                │  Start where you like —     │
│                                                │  LearnLoop builds questions │
│                                                │  for the chapter you're in. │
│                                                │                             │
└────────────────────────────────────────────────┴─────────────────────────────┘
```

**What works at once.** Scrolling, page search on the PDF text layer, highlights, notes and Ask about a selection. Until extraction lands, Ask is grounded in the selected text and the page number. Its answers say *from this page*.

**What waits for extraction, and says so in place.** Anchored highlights that survive re-extraction, section checks, *work through this* on an exercise, and the margin cues. Each one shows *available in a minute or two* on its own control. Nothing greys out without a reason (Reader doc U9).

**The status line goes through these states:**

| State | Line |
|---|---|
| started | *Getting this book ready* |
| extracted | *Chapters found* |
| building | *Questions for Ch. 1 in about 4 min* |
| done | *Questions ready for Ch. 1* |
| quiet | the line hides |

**The line never shows** stage names (*extraction*, *inventory*, *synthesis*), token bars or percentages. *details ▸* on the line opens the book's card, which links to Under the hood → Imports & builds.

**The first question comes from the section the learner is reading.** It needs only the extracted text, not the study map. Today's quick-check producer (`spec_reader_quick_check_producer.md`) already writes a span-grounded question per section from the extraction alone when the reader nears a section's end. So the first question can arrive about a minute after extraction finishes. It comes through the Reader's existing section-boundary offer, which the Reader doc §4.12 allows, with no toast and no modal.

That question is a self-check: the learner writes, then compares with the intended answer. *Add to practice* turns it into a graded, spaced question. Graded questions for the chapter arrive with the background build (§6.4), and Today's plan starts drawing on them the next time it plans.

### 6.4 What LearnLoop decides, so the learner doesn't

Every choice that today's Add flow asks for, with the redesigned default and where the choice now lives:

| Asked today (where) | Default now | If the learner wants to choose |
|---|---|---|
| Vault directory (NewVaultWizard) | `~/LearnLoop`, created silently | ⋯ → Switch library · Settings → Library location |
| Subject name (wizard; **required** by QuickAdd, which has no way to create one) | **Automatic.** A provisional subject named from the book's title or topic. An LLM files it with existing subjects in the background, correctable with one tap (DL decision C2) | Book card → *details ▸ → Subject* |
| Starting level (wizard, brief, Ingest chip) | Not asked. Placement comes from the first answers and from Reader questions (DL S1, S5). *Too easy* and *I know this* act at once on any question (DL S3) | Reader Guide → *I know this chapter* (assumed known, not tested) · Settings → Learning → Starting level |
| Page range (wizard, QuickAdd, Ingest) | The whole book is readable. Questions are built progressively (below) | *Add → More options → Only some pages* |
| PDF engine (Ingest) | `auto`: Marker if installed, else pypdf, with the existing runtime fallback | *Add → More options* · Settings → Advanced → Import |
| Source use / "Enrichment · interesting adjunct" (QuickAdd) | Inferred: the first book in a subject is the main text; a later short source on the same topic becomes enrichment | Book card → *details ▸ → Use as…* |
| Role (`primary_textbook`, `lecture`, …; *role ambiguous — flagged*) | By kind, as today (`quick_add.py` `_ROLE_BY_CATEGORY`). Never shown | Book card → *details ▸ → Use as…* |
| Inventory output budget per unit; *no LearnLoop token ceiling* | The recommended budget (12,000). Spend caps bound the total | Settings → Advanced → Token budgets |
| Brief (outcome, depth, practice timing, topics, notation) | The default brief; practice *as you read* | Book card → *details ▸ → Focus and depth* |
| Reader on/off (QuickAdd, staging) | On | *Add → More options → This is a past exam or problem set* (turns it off) |
| External-AI consent checkbox per stage (QuickAdd confirm) | **Asked once, when an AI is connected** (§6.6) | Settings → AI → *What leaves this computer* |
| Confirm & build, after reviewing scope, role and token estimate (QuickAdd) | Builds automatically once extraction finishes. Asks only when the build is unusually costly (§6.6) | Book card → *details ▸ → Build questions for the whole book* |
| Accept each proposal (Proposals screen) | Study maps that pass the checks **apply themselves**, with undo (§6.5) | Under the hood → Study-map changes |
| Import vs. "＋ create study map" vs. outline & select vs. collections (Ingest) | One verb: **Add** | Under the hood → Imports & builds keeps the deliberate path |
| Exam seeding mode (Ingest) | Not on the main path | *Add → More options → This is a past exam* |

**Progressive building replaces up-front scope selection.** Today, Quick add picks a "small relevant scope" by keyword match against the subject title (`quick_add.py` `select_relevant_units`). A learner who reads Chapter 1 may find questions built for Chapter 7. The redesign builds in **reading order**:
1. The chapter the learner opens first, and the next one.
2. Then each chapter as the learner reaches it, one chapter ahead.
3. Also, any chapter the learner jumps to.

Under the hood this is today's machinery: the first build is a bootstrap of the selected units, and later chapters are `append` builds. The spec already allows this: "late units … route through append". The difference is that the trigger is the learner's reading position rather than a keyword score. *Build questions for the whole book* stays available as an explicit choice.

### 6.5 Study maps apply themselves (review by exception)

Today a quick-add build ends at "Study-map proposal ready for review" (`content/pipeline/jobs.py:1647`, `apply` defaults to `False`). The learner then has to find Proposals, read raw entity IDs and accept items one by one; bulk accept is a hidden `Shift+A` (audit B.6).

**The redesign:**
- The automatic builds of §6.4 run with `apply=True` when every gate passes. They go through the same gates, receipts and proposal records as today.
- The proposal still exists, marked *applied automatically*. It can be undone from the book card (*details ▸ → Undo this book's questions*) or from Under the hood → Study-map changes, which already supports *Reject (revert)*.
- Items the policy routes to `review_required`, and anything that fails a gate, wait in Under the hood → Study-map changes. The book card gets **one quiet line**: *2 changes need a look ▸*. The top navigation shows no badge or count.
- This extends the owner's decision R1 ("No review queues as a default workflow … auto-accepted when confident, with undo", `daily_loop_frictionless_defaults.md`) from practice families to study maps. It is also what `spec_source_ingestion_v2.md` calls "review-by-exception".

### 6.6 AI: connect once, consent once, money only when unusual

**No AI connected.** Reading, notes, highlights and the shelf all work. Each book card says *Questions need an AI connection · Connect*.
- Connect opens one small sheet. **Continue with ChatGPT** is first, then *Use an OpenRouter key*, then *Other (advanced)*.
- Signing in **routes every use case** to that provider by default. Today it routes nothing, and the hint tells the learner to edit `learnloop.toml` (audit B.11).

**Consent happens once, at connection.** The sheet says in one sentence what leaves the machine: *LearnLoop sends passages of the books you add, and your answers, to ChatGPT to write questions and give feedback.* Then one button: **OK**.
- This replaces the per-build checkbox list (`QuickAddDialog.tsx:502`).
- It is recorded in vault config with the provider and date, so the audit trail survives.
- If a later action would send something new (audio to a transcription service, a whole PDF to a native-PDF model), that action asks once, in place.
- **No per-book opt-out** (owner, 2026-10-13: it is fine to send books to an AI, and a per-book opt-out was not asked for). This draft's *Keep this book on this computer* (shipped in Phase 1 as *Never send this book to an AI*) is retired: no control in Add or book details, no refusal at any boundary. The `source_artifacts.keep_local` column it used stays and nothing reads it; `learnloop doctor` names a book that still has it set (`source:retired_keep_local`). See `docs/reviews/reading-hardening.md`, part 3.

**Money.** Spend caps (the existing `SpendBudget`) bound everything.
- A build whose estimate is above a threshold (open question Q5: default $1 per build, or more than 25% of the remaining daily cap) pauses before it runs. The book card shows one line: *Building questions for all 24 chapters would cost about $3.10 · Build as I read (recommended) · Build all now*.
- Below the threshold, cost appears only in Under the hood → Spend.

### 6.7 When things go wrong

| Situation | On the book card or Reader line | In *details ▸* |
|---|---|---|
| Scanned PDF, no text layer | *Some pages look scanned · Read them with text recognition* (re-runs Marker with OCR) | The health flags and the engine used |
| Marker missing or failed; fell back to pypdf | *Maths may look rough in the text view · Fix it* (opens Settings → Advanced → Import, with the install hint) | `marker_failed_pypdf_fallback` |
| Network fetch failed (web, arXiv, YouTube) | *Couldn't reach the page · Try again* | The HTTP error |
| YouTube has no captions | *This video has no captions · Transcribe the audio (uses AI, about $0.05)* | — |
| Question build failed a gate | *Questions for Ch. 3 need another try · Retry* (the existing zero-model *auto-repair & revalidate* runs first) | The gate diagnostics, linking to Under the hood → Imports & builds |
| Spend cap reached | *Paused — today's AI budget is used · Raise it or wait until tomorrow* | Caps by route |
| No AI | *Questions need an AI connection · Connect* | — |

**Every failure leaves the book readable.** Only the thing that failed stops.

### 6.8 Before and after, step by step

**Scenario.** A first-time user with an AI already connected. They add a 600-page textbook PDF, read the start of Chapter 1, and answer their first question. "Before" is the guided path the app offers today, read from the code at `57d31c63`. Run against the real app, it may differ in small ways (§11 measures it).

**Before**

| # | The user… | Kind |
|---|---|---|
| 1 | Notices `+ create a new vault ▸` on Start | find |
| 2 | Reads "A **vault** is a folder LearnLoop owns: your concepts, evidence, practice items, and the SQLite state behind them" | jargon |
| 3 | Types a directory or uses *browse…* (2–3 clicks in the native dialog) | **decision** |
| 4 | Types a first subject. It says *optional*, but QuickAdd's *Analyze →* is disabled without one, and QuickAdd can't create one | **decision** (a trap if skipped) |
| 5 | Picks "where are you starting from" (4 chips) | decision |
| 6 | Clicks *create vault ↵*. The app switches vault | wait (seconds) |
| 7 | QuickAdd opens over Ingest: *NEW VAULT SETUP · GUIDED INGEST · 01 source + pages → 02 inventory budget → 03 review + build* | jargon |
| 8 | Chooses the PDF (*browse…*, 2–3 clicks) | **decision** |
| 9 | Optionally types a page range (`3-27, 29-33, 36`) | decision |
| 10 | Passes *source use · Enrichment · interesting adjunct*, *inventory output budget · per unit* (12,000 tokens), *no LearnLoop token ceiling*, *customize brief* and *▣ reader on* | 5 decisions offered |
| 11 | Clicks *Analyze →* | click |
| 12 | Reads *This source has not been imported yet. Import + extract first, then quick-add continues.* and clicks *Import first* | click, jargon |
| 13 | Waits in the dialog while *Extraction worker is processing the source* (Marker on 600 pages: many minutes on a CPU) | **blocking wait** |
| 14 | Reads the confirmation: scope (*N of the most relevant units*), role (`primary_textbook`), estimate (tokens), *reader-first* note | jargon |
| 15 | Ticks each *external AI consent* checkbox (at least one, `synthesis`) | **required decision** |
| 16 | Clicks *Confirm & build* | click |
| 17 | Lands on Ingest with toast *Study map building — track it in Ingest* and banner *SETUP 03/03 … Inventory runs once per selected unit, then study-map synthesis starts…* | jargon |
| 18 | Waits for inventory and synthesis (many minutes). The card shows a checkpoint ladder and token bars | wait |
| 19 | Notices the build finished. There is no signal outside the Ingest tab and the Proposals badge | find |
| 20 | Opens Proposals (`Alt+5`). Reads `proposals · AI inbox`, raw IDs and `auto_apply / review_required` | jargon |
| 21 | Accepts the items (one at a time, or the hidden `Shift+A`) | **required decisions** |
| 22 | Opens Reader (`Alt+9`) and picks the book | 2 clicks |
| 23 | Reads | — |
| 24 | First question: under *practice as you read* there are no practice items until a section is completed in the Reader, so either answers the section-boundary check or goes back to Start → *begin session* → Today → opens an item | 1–4 clicks |

**Before, counted.** Reading starts at step 23. The first question comes at step 24 or later.
- About **20 actions** to reading.
- **4 required decisions** (folder, subject, consent, accepting proposals) and **about 10 offered decisions**.
- **2 long waits.** The first blocks a modal dialog. The second is only visible on a tab the learner has to find.
- **About 25 internal terms** on the path: vault, SQLite, canonical source, subject, extraction, extraction worker, import, inventory, inventory output budget, unit, token, token ceiling, brief, enrichment adjunct, role, `primary_textbook`, reader-first, facets, learning objects, external AI consent, synthesis, study map, proposal, AI inbox, `auto_apply` / `review_required`, Activity / checkpoint ladder.
- **Time to first reading:** the extraction time plus the build time plus the review time. For a textbook on a CPU that is **tens of minutes**.
- **A trap:** skip the "optional" subject and the guided path dead-ends with a disabled *Analyze →* and no message.
- **The other entry points** are no better. The Ingest screen offers a *▶ import source* (reading only) on the right and *＋ create study map* on the left, explained by four paragraphs of help text (`IngestScreen.tsx:1530-1572`).

**After**

| # | The user… | Kind |
|---|---|---|
| 1 | Launches. The Library says *Drop a book, paper or lecture here* | — |
| 2 | Drops the PDF (or *Choose a file…*, 2 clicks) | action |
| 3 | Reads page 1 of the original PDF. The header says *Getting this book ready* | wait ≤ 3 s |
| 4 | Keeps reading. The line becomes *Questions for Ch. 1 in about 4 min*, then hides | background |
| 5 | Reaches the end of §1.1. The section-boundary offer reads *A quick question on what you just read · about 1 min*. Presses ↵ | action |
| 6 | Answers the first question in their own words | — |

**After, counted.**
- **1 action** to reading (2 with the file dialog). **2 actions** to the first question.
- **0 required decisions.** **0 blocking waits.**
- **0 internal terms.**
- **Time to first reading:** under 10 seconds.
- **Time to the first question:** the time it takes to read the first section. The section check is written about a minute after extraction finishes.
- **Graded questions** for the chapter are built in the background in about 5 minutes (an estimate for one chapter, to be measured in §11). From then on they are offered at the next section break and in Today's plan.
- **The caveat is extraction speed.** Marker on a 600-page book, on a machine with only a CPU, takes a long time. To keep the promise, extraction runs in reading order:
  1. first the chapter the learner opened, as a page-range import, which today's machinery already supports;
  2. then the rest of the book in the background.

  If that chapter's text isn't ready when the learner reaches the end of §1.1, the offer appears as soon as it is. Nothing is lost, and nothing blocks reading.

**The same, for other kinds** (actions to reading / actions to the first question):

| Source | Before | After |
|---|---|---|
| Textbook PDF | ~20 / ~22+ | 1 / 2 |
| Paper (arXiv id) | ~17 / ~19+ (no page range; role `paper`) | 1 (paste) / 2 |
| Web article URL | ~17 / ~19+ (role ambiguous, flagged) | 1 / 2 |
| YouTube lecture | ~17 / ~19+ (role `lecture`) | 1 / 2 (pause-point question) |
| A second book, later | Ingest → *＋ create study map* → the same QuickAdd: ~12 / ~14+ | 1 / 2 |

### 6.9 What changes in code for this slice

The detailed sizing is in §10. In outline:
- **Rust** (`src-tauri/src/sidecar.rs`): `default_vault_path()` falls back to a created `~/LearnLoop` instead of the tracked fixture.
- **Sidecar.** A new `add_source` method composes existing parts:
  1. register the source and store the original;
  2. return `source_id`, `revision_id`, `kind`, `title` and a `reader_target`;
  3. enqueue extraction;
  4. on extraction complete, auto-create or auto-file the subject and enqueue the progressive build with `apply=True`.
- `reader_pdf_view` accepts a revision with no extraction yet (`available: true`, `blocks: []`). `get_source_library` gains a learner-facing `status_line`.
- **Frontend.** New `components/AddSource.tsx` and `components/BookCard.tsx`, a window-level drop target, and `components/ConnectAI.tsx`. `IngestScreen`, `QuickAddDialog` and `NewVaultWizard` leave the default path but stay reachable from Under the hood and the palette.
- **What stays:** the durable job runner, gates, receipts, proposal records, kill switches, spend caps, and every CLI command.

---

## 7. Screen by screen

Each place below has the same five parts:
- the learner's **job** there;
- what it shows **by default**;
- what moves behind **details** or under the hood;
- its **states**: empty, first run, loading and error.

The detailed findings behind each screen, with file and line references, are in `docs/ux/audit_current_screens.md`.

### 7.1 Today

**Job.** "What should I do now?" One decision, the minutes, which is remembered. Then Enter (N2, M4).

**Default view.** This is today's `DailyPlanView`, which the audit found to be the cleanest learner surface in the app (audit A.2). It is promoted to home, merged with Start, and stripped of what remains.

Wireframe W4:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LearnLoop   Today   Library   Reader   Progress              [+ Add]  ^K  ⋯   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Tuesday evening                                    10m  15m [25m] 40m  60m   │
│                                                                              │
│  25 minutes today: finish §5.4 Mixtures, then 6 short questions from         │
│  last week, and one problem you worked with help.                 why? ▸     │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ ▸ Continue §5.4 Mixtures · Probability                     about 12 min │  │
│  │   6 short questions · conditional probability, counting   about 8 min  │  │
│  │   Exercise 5.14 on your own (you did it with help Sat)    about 5 min  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                             [ Begin ↵ ]                      │
│                                                                              │
│  Pick up a thread                                                            │
│   ? "why is the density of a sum a convolution?" · §5.4      open in book ▸  │
│   ✎ Exercise 5.9 — 3 steps written                                 resume ▸  │
│   ◇ Reading wrap-up ready — under a minute                            ▸     │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  4 days · best 9                                    all of today's list (l)  │
└──────────────────────────────────────────────────────────────────────────────┘
```

**What the learner sees:**
- **The plan as one sentence**, plus the blocks as a short list, each in *about N min*.
  - The lanes (*maintain / repair / new / push*) are not named on the surface. Their effect is described in words: *questions from last week*, *a problem you worked with help*, *a fix for a mix-up*, *new: §5.5*.
  - The lane split is in `why? ▸`, along with the plan's reasons.
- **Begin ↵** opens the first block. A reading block opens the Reader with the plan banner. A practice block opens Practice.
- **Sessions are implicit.** Begin, or any practice started anywhere, opens a session with the remembered minutes. The sidecar's `start_session` is called lazily. The "start a session first" toasts go (audit A.0).
- **Threads** come from the Reader doc: open questions (they open in the Reader, at the passage), unfinished workbench problems, and a wrap-up when there is one. None of them has a count. At most three are shown, then *more ▸*.
- **Re-entry after a break** replaces the plan sentence: *Welcome back. A short catch-up today: 12 minutes of the most useful questions. Nothing else is waiting on you.* (DL P6). No list of slipped items appears on the surface. It goes in `why?`.
- **The streak** is a footer line: *4 days · best 9*. It is never red, and it never says what you'll lose.
- **Inbox.** Captures (phone, clipboard) show a single line, *2 new captures ▸*, only when there are some. The always-visible `InboxStrip` goes.

**Moves to details (`why? ▸`):**
- the lane split and its reasons;
- why each block is there (from the plan's existing reasons);
- the re-entry list of what slipped.

**Moves under the hood, or is removed:**
- *Scheduler mode* and its probe-suppression rule;
- the *due now / probe queue / later / follow-ups* tiles;
- the `goalMeta` counts and the fake fallback line;
- the backdrop cycler (to Settings);
- the full list's hero status line (`vault ● healthy · ai:codex ● ready · queue ● ready`), the DUE/PROBE/LATER/BUDGET grid and per-row mastery numbers;
- *Why this position* bars, *priority 0.412*, the hard-coded ranking formula and the algorithm version;
- ClaimSurface *Scheduler choice* (Q16);
- *Evidence facets* chips and the Beta-parameter drawer;
- the SurpriseInsertionBanner wording;
- `e` (end session) without confirmation;
- the fake-telemetry session HUD.

**The full list (`l`) stays,** as a plain list: titles, *about N min*, and why each is there in five words. Raw item IDs, mode slugs and mastery bars go to the inspector.

**Goals.** A goal shows as a single card under the plan: *Probability midterm · 14 Nov · on track*, with *Practise for this goal* and *Practice exam (40 min)*. GoalBanner's numbers, the track record and the Brier score go behind *details*. The practice exam becomes reachable from the plan view, where today it is hidden in the full list (audit A.5).

**Questions that need no special banner.** A check-on-your-own question (held-out cold probe or validity check) is shown in the list as *on your own · no hints*. *why?* explains: *to see whether last week's fix held.* The "voids the measurement… attempt will be rejected" wording goes, and the Reader doc's cold banner wording is used instead (*A check on your own. Help is still here — using it makes this practice with help.*).

**States:**

| State | What shows |
|---|---|
| **First run (no books)** | *Nothing to plan yet. Add a book, paper or lecture and LearnLoop will plan your days around it.* with [+ Add]. Not *Nothing due today*, and not a Begin that leads to *No new material is ready to add* (audit A.1). |
| **One book, no answers yet** | *15 minutes today: start Probability, Chapter 1.* followed by Begin, which opens the Reader. Day one is never empty (N3). |
| **Plan done** | *Done for today · 26 minutes.* followed by *Keep going* (more of the same) or *Something new* (the next section). The session summary is the two calm lines of §7.5's session end. |
| **Loading** | The plan frame with the last plan dimmed. No "Loading today's queue". |
| **Error** | *Couldn't plan today · Try again.* The plan is never replaced by a raw error. |

### 7.2 Library

**Job.** "My books, papers and videos: where I am in each, and what's ready." It is also where the learner's own notes live.

**Default view.**
- The shelf: one card per source, most recently read first.
- A *Notes* tab beside *Books* holds the learner's Markdown notes (today's Library note editor).

Wireframe W3:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LearnLoop   Today   Library   Reader   Progress              [+ Add]  ^K  ⋯   │
├──────────────────────────────────────────────────────────────────────────────┤
│  Books   Notes                                            search your books ⌕ │
│                                                                              │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐          │
│  │ Probability                  │  │ Attention Is All You Need    │          │
│  │ Blitzstein & Hwang · book    │  │ arXiv 1706.03762 · paper     │          │
│  │ §5.4 Mixtures · 2 days ago   │  │ p. 3 · yesterday             │          │
│  │ ●●●◌◌○○○  Ch. 1–5            │  │ ◐ questions for §3 in ~2 min │          │
│  │ Continue ↵        details ▸  │  │ Continue          details ▸  │          │
│  └──────────────────────────────┘  └──────────────────────────────┘          │
│  ┌──────────────────────────────┐  ┌──────────────────────────────┐          │
│  │ 3Blue1Brown — Eigenvectors   │  │ Linear Algebra Done Right    │          │
│  │ YouTube · 17 min · lecture   │  │ Axler · book                 │          │
│  │ 9:40 · last week             │  │ Some pages look scanned      │          │
│  │ Continue          details ▸  │  │ Read them with text recog. ▸ │          │
│  └──────────────────────────────┘  └──────────────────────────────┘          │
│                                                                              │
│              Drop more books here, or [+ Add]                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

**A book card shows:**
- title, author and kind;
- where the learner is and when they were last there;
- one row of evidence marks over the chapters built so far (`●` on your own, `◌` with help, `○` not tried yet; no percentages);
- **one** status line, only when it says something (§6.3, §6.7);
- *Continue* (↵), which opens the Reader at the learner's place.

**The card's `details ▸` holds the receipts and controls:**
- *Use as…* (role) and *Subject*;
- *Focus and depth* (the brief) and *Build questions for the whole book*;
- *Undo this book's questions*;
- *Only some pages…* and *Re-read with text recognition*;
- *Update to the new edition* (from Maintain's *update study map*) and *Source conflicts* (only when they exist);
- *Remove from library*;
- *Open in Under the hood*, which goes to that book's batches and proposals.

**States.**

| State | What the learner sees |
|---|---|
| **Empty / first run** | W1 (§6.1). |
| **Loading** | The shelf frame with card outlines. No spinner title. |
| **A book being prepared** | The card with its status line. The card is never hidden and is always openable, except audio while it is transcribing. |
| **Error loading the library** | *LearnLoop couldn't read your library · Try again*, with `details ▸` holding the raw message. |

**Moves out of the Library:**
- The vault file tree, the proposal payload editor and the SQLite browser go to Under the hood → Files and Data.
- `state.sqlite` no longer appears in any learner tree.

### 7.3 Reader (the shell's part)

**Job.** Read and think. The inside is the Reader doc's.

**Entering:**
- *Continue* on a book card, the plan's reading step on Today, a thread on Today (it opens at the passage, K6), *see it in the book* on feedback, `Alt+3` (the last book), or *Add* (the new book).
- **With no book open**, the Reader shows the shelf (the same `BookShelf` component) with the line *Open a book to read*.

**The header:**
- *← Library*;
- the title, taken from the book's metadata and never a `file://` URI (today the header shows the raw path, Appendix A `36`);
- position;
- the reading depth control (Reader doc);
- when preparing, the status line (§6.3).

The plan banner (`PlanReadingBanner`) stays while the plan step is active, **even across a detour to another place**; today it disappears on any tab switch (audit C.1). *Back to today's plan* returns to Today's next step.

**Leaving.** Practice and feedback started in the Reader come back to the Reader at the passage (Reader doc S6).

**States the shell owns:**

| State | What the learner sees |
|---|---|
| **Loading a book** | The page frame with *Opening…* in the header; the previous book's position is not shown. |
| **Preparing** | §6.3. |
| **Source missing** (the file moved, or it was deleted) | *This book's file isn't where it was · Find it…*, which re-links via the originals store. |
| **Offline backend** | *LearnLoop's background service isn't responding · Try again*. The demo chapter is no longer offered on the main path; it moves to Under the hood. |

**Shell bugs that must be fixed as part of this work:**
- The `readerEnabled ?? false` flash on every first open (`ReaderScreen.tsx:620`), which tells the learner to edit `learnloop.toml`.
- A bare `Alt` clearing the selection (K7).
- Red toasts on every open about saved requests that never started (audit C.3). These become one quiet line in the rail.

### 7.4 Practice

**Job.** Answer one question in your own words, get help if you want it, and move on.

**Default view.** Wireframe W5:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Today's plan · 2 of 6                    conditional probability   ⋯       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  A fair die is rolled twice. Given that the sum is 8, what is the            │
│  probability that the first roll was a 3?                                    │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │ Write what you can — $math$ works.                                     │  │
│  │                                                                        │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│   [ Submit  Ctrl+↵ ]    Hint   ·   I'm stuck   ·   Ask   ·   Skip          │
│                                                                              │
│                                          see it in the book (§2.2) ▸         │
└──────────────────────────────────────────────────────────────────────────────┘
```

**What the learner sees:**
- **The header**: where they came from and how far through (*Today's plan · 2 of 6*, or *← §5.4* from the Reader), the topic title, and `⋯`.
- **Hint, I'm stuck, Ask and Skip are buttons.** They keep their keyboard shortcuts. Today all four are keyboard-only (audit A.3).
  - *Skip* goes to the next question, not back to Today.
  - *I'm stuck* keeps the owner's rule: write what you can, then submit.
- **`⋯` holds the card controls**: *easier · harder · ask me differently · explain it (teach-back) · I know this · this question is wrong · not for me*. *Not for me* replaces *retire*, with an optional reason. The 11 retire reasons go to details.
- **A check on your own** shows the quiet line *On your own · no hints on this one · why?*. Hint and Ask stay visible. Using one says first: *This becomes practice with help.* This is the Reader doc's U11.
- **A diagnostic question** looks like any other question. Its *why?* says *to see which of two things to help with next*. Its feedback waits until the short set ends, and the screen says so in one line: *Feedback after the next 2 questions.*
- **The grading wait.** *Reading your answer — usually about N s*, where N comes from the grading route's measured latency (`learnloop ai latency`). Everything except Submit stays usable. The learner can reread the question or copy their text. The 180 s timeout is never shown. If it is reached, the screen says *The grader is slow right now · Keep waiting · Grade it yourself*.
- **Self-grading** (no AI, or the AI is unavailable): the **expected answer is shown** beside the learner's, with three choices: *Got it · Partly · Missed*. Per-criterion numeric inputs, fatal-error lists and attribution chips go to *details*. Today the self-grade panel asks for a score per criterion with no reference answer shown (audit A.3).

**Moves to details or under the hood:**
- the item ULID, which today opens the inspector and **shows the expected answer mid-question**;
- the mode slug;
- *codex grading*;
- *MASTERY ESTIMATE 0.62 ±0.18*;
- the character and word count;
- "Verifying diagnostic safeguards…";
- measurement-integrity copy (*void*, *rejected*, *Demonstrated credit*, *surface authored*).

The inspector never shows the expected answer or rubric for an item the learner hasn't answered (§10, 4.1).

**States:**

| State | What shows |
|---|---|
| **Loading** | The question frame. |
| **Unavailable** (retired, missing) | *This question isn't available any more · Next question* |
| **Submission needs recovery** | *Your answer is saved. LearnLoop is finishing the grading · Try again.* The raw attempt ID goes in details. |
| **Exam mode** | The header says *Practice exam · 3 of 20 · no hints*. Esc asks *Leave the exam? Your answers are saved.* |

### 7.5 Feedback

**Job.** Was I right? What does the right answer look like next to mine? What is the one thing to do now? Then Next.

**Default view.** Wireframe W5b:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ← Today's plan · 2 of 6                    conditional probability   ⋯       │
├──────────────────────────────────────────────────────────────────────────────┤
│  Partly right                                          ◇ graded by AI ·      │
│                                                     I think I was right ▸    │
│  ┌───────────────────────────────┐  ┌───────────────────────────────────┐   │
│  │ › You wrote                   │  │ ◇ A full answer                   │   │
│  │ P(first=3 | sum=8) = 1/6      │  │ Outcomes with sum 8: (2,6),(3,5), │   │
│  │ because each roll is fair     │  │ (4,4),(5,3),(6,2) — 5 equally     │   │
│  │                               │  │ likely. One has first = 3: 1/5.   │   │
│  └───────────────────────────────┘  └───────────────────────────────────┘   │
│                                                                              │
│  ✓ Set up the conditional probability                                        │
│  ✗ Restricted the sample space to the condition                              │
│                                                                              │
│  You used the unconditional probability. Conditioning on "sum = 8" shrinks   │
│  the outcomes to five.                                         why? ▸        │
│                                                                              │
│  [ Next ↵ ]     Try a similar one (t)  ·  see it in the book (§2.2) ▸        │
│                                                                   details ▸  │
└──────────────────────────────────────────────────────────────────────────────┘
```

**What the learner sees:**
- **A verdict in words**: *Right*, *Partly right*, *Not yet*. The score in numbers (*3 / 4*) goes in details.
- **Their answer beside a full answer**, in the three voices (`›` you, `◇` model, `§` the book where the answer quotes it). Today Feedback shows neither the question, nor the learner's answer, nor the expected answer (audit A.4).
- **The criteria as ✓ / ✗ lines** in plain words. *Downstream of an earlier error — not judged* stays as a quiet `·` line.
- **One sentence on what went wrong.** It merges what today is spread over DiagnosisCard, CausalFeedbackPanel, the misconception card and the tutor note. It uses the diagnoser's result when ready. Until then it uses the grader's feedback, and the sentence updates in place without moving the layout. No "analyzing your pattern…" banner. A named mix-up reads *You may be mixing up conditional and unconditional probability*, with titles and no facet slugs. A missing prerequisite reads *This needs conditional probability first · 5 min ▸*.
- **One next action** besides Next. Pick the one the system recommends:
  - *Fix this mix-up · about 4 min*, the repair inline, replacing the 4-click Repair flow;
  - *Try a similar one*;
  - *Redo the part you missed*, the guided redo;
  - *Explain it*, a teach-back.
  The others sit under `⋯`.
- **A Next button.** Today Next is keyboard-only.
- **Next returns to where the attempt started.** That is the plan's next step, the Reader passage (Reader doc S6), or Progress.
- **Contesting is one link**: *I think I was right ▸*. It opens a one-line box for the reason, and the regrade happens in place. It replaces the four diagnosis verdict widgets with a single *this doesn't sound right* link under `why?`.

**Moves to `why? ▸`, on the explanation:**
- the possible causes and what is still unverified;
- *what you already showed*;
- the mix-up's mechanism;
- *You've made this mistake before* with the dated quotes, one of the clean patterns worth keeping;
- *this doesn't sound right* (the single diagnosis verdict).

**Moves to `details ▸`, on the attempt:**
- the numeric score;
- the rubric with weights;
- *what the grader looked for*;
- grader confidence and tier;
- the regrade history;
- *one question, unaided*, offered when the grader asks;
- the clarification card, shown when the grade is provisional with a short line *This grade may change after one question ▸*;
- tutor hints counted;
- *open in inspector*.

**Moves under the hood, or is removed:**
- the attempt ULID breadcrumb;
- FSRS rating, interval factor and retrievability target;
- the belief-update chart (*logit-space Kalman update*);
- surprise *nats > τ*;
- the diagnostic follow-up gate card and need IDs;
- error-attribution severity and scope;
- the duplicated criterion trace;
- *decision · … · causal_p2_v1*;
- ClaimSurface;
- `⇧D force follow-up` and `a add error` (palette only).

**Diagnostic set results** (today's DiagnosticReviewScreen) become this same screen, with one line on top: *That's the short check done. Here's what it showed.* It then shows the per-question verdicts and one next step on ↵. Raw status, *converted_to_tutoring*, *Feedback withheld… released now* and *observation N* all go.

**Session end.** Two calm lines on Today (or a dismissible card), never a full-screen HUD:
- *26 minutes · 9 questions. Since last time: ● conditional probability (on your own) · ◌ mixtures (with help).*
- *Next time: finish §5.4.*

**States:**

| State | What shows |
|---|---|
| **Loading** | The verdict area outline. The learner's answer shows at once, since it is already known. |
| **Grade provisional** | *This grade may change after one question ▸* |
| **Diagnosis failed** | Nothing extra. The grader's sentence stands. |
| **Error loading** | *Couldn't load the feedback · Try again · Next question* |

### 7.6 Progress

**Job.** Answer three questions at a glance: *What can I do on my own now? What's fading? What's next?* Then let the learner act on the answer with one click.

**Default view: the well,** made readable. Wireframe W6:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LearnLoop   Today   Library   Reader   Progress              [+ Add]  ^K  ⋯   │
├──────────────────────────────────────────────────────────────────────────────┤
│  Probability ▾      Well · Connections · Goals                               │
│                                                                              │
│  You can do 9 things on your own. 3 are fading. Next: conditional            │
│  independence.                                                 why? ▸        │
│                                                                              │
│              counting ●                     ● Bayes' rule                    │
│                     ╲      ·  ·  ·  ·      ╱                                 │
│      inclusion–   ●  ╲  ·            ·   ╱  ◌ total probability              │
│      exclusion        ·    ╭──────╮    ·        (with help)                  │
│                      ·    ╱  ░░░░  ╲    ·                                    │
│    sample spaces ●  ·    │  ░░▓▓░░  │    ·  ▸ conditional independence       │
│                      ·    ╲  ░░░░  ╱    ·      next                          │
│     random vars ○     ·    ╰──────╯    ·                                     │
│     (not tried)        ·  ·  ·  ·  ·  ·    ◌⌁ geometric series (fading)      │
│                                                                              │
│  deep = you'll likely recall · ● shown on your own · ◌ with help · flat =    │
│  not started                                                     more ▸     │
├──────────────────────────────────────────────────────────────────────────────┤
│  conditional independence    ○ not tried yet                                 │
│  Practise this (5 min)   ·   Check what I already know   ·   I know this     │
└──────────────────────────────────────────────────────────────────────────────┘
```

**What changes in the well.** The owner's design contract stays: depth comes from *ready × evidence* only, demonstrated is shown only as beads, and the two are never blended.
1. **Titles, not ids, on the rim.** They are short, wrapped and truncated with the full title on hover. Today the labels are raw snake_case facet ids (`KnowledgeWellView.tsx:690`).
2. **One headline sentence** above the canvas, built from the counts the view already computes (`:334-355`): *You can do N things on your own. M are fading. Next: X.* Its *why?* explains how *next* was chosen.
3. **Next is drawn.** `nextGap`, which today is drawn only in Terrain, gets a `▸` marker and a label on its spoke.
4. **Fading is visible.** A skill whose predicted recall will cross the target within 7 days gets an amber `⌁` tick and the word *fading*. Today this lives only in a tooltip.
5. **It holds still.** Auto-rotation is off by default and the view starts top-down, so labels stay put. Drag still orbits, and *Settings → Appearance → Animate the map* brings rotation back.
6. **Plain-language legend** with three items, plus *more ▸* for held-flat, absent, locked, assumed and decay rings.
7. **One colour, one meaning.** Amber marks *fading / with help*. Contours, selection and locks move to neutral tones.
8. **A click opens a learner card, not the inspector.** The card shows the title, one status line in the ○◌● vocabulary, and *Practise this · Check what I already know · I know this* (today's `PlacementControls`). The card's *details ▸* holds Ready %, evidence mass, capabilities and *open in inspector*.

**The other views:**
- **Connections** is a read-only concept map with titles, prerequisites first. Editing moves under the hood, where edits apply with undo and an optional reason.
- **Goals** holds goal cards in plain words (*On track for the exam on 14 Nov · 2 topics need attention*), *Practice exam · 40 min*, and *Set a goal (optional)*.
- **Terrain and Strata** move under the hood.

**States.**

| State | What the learner sees |
|---|---|
| **First run (no books)** | *Your map grows as you read and practise. Add a book to start.* [+ Add] |
| **Books but no answers yet** | A faint, flat well with the chapter skills as `○` and the line *Answer a few questions to shape your map · Check what I already know (about 5 min)*. Never a disc of "untested" ids. |
| **Loading** | The canvas outline. |
| **Error** | *Couldn't draw your map · Try again*. |

### 7.7 Under the hood

**Job.** The owner's instrument panel: everything §5.2 lists, unchanged inside, under plain titles.

**Default view.** A left list of tools, and on the right the last tool used. Each tool's page keeps today's screen as it is, including its terminal voice.

**What changes:**
- Badges move here, unbadged in the nav. Each tool shows its own count beside its name.
- *Always show details* (an owner setting) lives here too.

**Empty states** keep today's copy. Under the hood is for the owner, and the owner reads that copy fluently.

### 7.8 Settings

**Job.** Change the few things a learner cares about. Everything else stays reachable.

**Default view, five settings:**

| Setting | Control |
|---|---|
| **AI** | *Using ChatGPT plan · Manage* or *Connect* (§6.6); *What leaves this computer*; *Grade my answers: with AI · myself* (today's `manual` grading route) |
| **Daily time** | the remembered minutes, which are also changed with one tap on Today |
| **Reading** | text font (mono · proportional, Reader doc Q1), size, and *ask me questions while I read: often · sometimes · rarely* (the Reader doc's cue density, for the shell) |
| **Appearance** | palette (terminal, dracula, gruvbox, nord, catppuccin mocha), Today backdrop (moved from Start), *Animate the map* |
| **Library** | where the library lives · Switch library… · New library… |

***Advanced*** sits below, collapsed and searchable. It holds everything in today's Settings, unchanged:
- per-use-case AI routes and model slugs;
- the OpenRouter key;
- embeddings and decision models (read-only);
- import (PDF engine, native fallback, audio mode, modalities, transcription);
- animation;
- token budgets and provider limits;
- spend caps;
- *For builders* (*Always show details*, *Classic shell* while it exists).

**Other changes:**
- The settings chip in the bar goes. Settings is in `⋯` and on `Ctrl+,`.
- The health indicator appears only when something the learner uses is broken: *Grading isn't working · Fix*. It does **not** appear when an animation or embedding route is unready (today it goes red for any route, audit B.11).
- Signing in with ChatGPT routes every use case to it unless Advanced says otherwise (§6.6). Today it routes nothing.
- The `LEARNLOOP_AI_PROVIDER` override banner stays, worded *An environment setting is choosing the AI for everything (LEARNLOOP_AI_PROVIDER)*. It is a developer situation, and it is honest.

### 7.9 Notices and errors (shell-wide)

Today, errors, notices and successes all share one red, persistent toast in the page flow (`styles/app.css:795`). About half the messages are raw backend text (audit C.7).

**Errors:**
- Red, with one sentence, the action, and *Try again* when the error is `retryable`.
- *details ▸* holds the raw message and code.
- The catch-all "could not confirm whether this action completed" is used only for writes. Reads say *Couldn't load this · Try again*.

**Notices** ("saved", "building", "grading → codex") are neutral, small and auto-dismissing, at the bottom edge. Most should not exist at all: the object's own state already shows the change.

**Inside the Reader**, in its reading and working postures, no notice appears. Notices are held and delivered at the next destination (Reader doc S11). Errors about the Reader's own action show on that action's control, not as a toast.

**Gating toasts become automatic behaviour:**
- "Start a session before opening practice" becomes an implicit session (§7.1).
- "Begin today's plan on Start first" disappears with Start.

**Developer-facing messages** ("frontend is newer than the running sidecar…", "npm run dev") are shown only in dev builds. In a release they become *LearnLoop needs a restart to finish updating · Restart*.

**One copy module** (`src/copy/errors.ts`) maps the most common sidecar error codes to learner sentences. Unknown codes get *Something went wrong · Try again*, with the raw text under details.

---

## 8. Wireframes

Some wireframes sit in the section they illustrate:

| Wireframe | Shows | Section |
|---|---|---|
| W1 | Empty library, first launch | §6.1 |
| W2 | Reader while a book is being prepared | §6.3 |
| W3 | Library shelf | §7.2 |
| W4 | Today | §7.1 |
| W5 | Practice | §7.4 |
| W5b | Feedback | §7.5 |
| W6 | Progress / the well | §7.6 |

This section adds:
- the first-run flow, frame by frame;
- the Add popover;
- the Connect AI sheet;
- Settings;
- Under the hood.

Every wireframe is at desktop width. Below 1,040 px the Reader's panes stack (Reader doc §3.1), and the shell's four places stay in the bar as icons with labels on hover.

### 8.1 First run, frame by frame

```
F1  launch (≈1 s)                       F2  drop the PDF
┌────────────────────────────────┐      ┌────────────────────────────────┐
│ Today Library Reader Progress  │      │ Today Library Reader Progress  │
│                     [+Add] ⋯   │      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│                                │      │░░                            ░░│
│   ┌────────────────────────┐   │      │░░   Drop to add to your      ░░│
│   │ Drop a book, paper or  │   │      │░░   library                  ░░│
│   │ lecture here           │   │      │░░                            ░░│
│   │ [Choose a file…] [link]│   │      │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│   └────────────────────────┘   │      │                                │
│ ○ Connect an AI to get         │      │                                │
│   questions — Continue with    │      │                                │
│   ChatGPT · other…             │      │                                │
└────────────────────────────────┘      └────────────────────────────────┘

F3  reading (≤ 3 s after the drop)      F4  end of §1.1 (minutes later)
┌────────────────────────────────┐      ┌────────────────────────────────┐
│ ← Library  Probability   p.1   │      │ ← Library  Probability   p.14  │
│ ◐ Getting this book ready ·    │      │                                │
│   chapters found               │      │  …the naive definition of      │
├──────────────────────┬─────────┤      │  probability requires equally  │
│                      │ Guide   │      │  likely outcomes.              │
│  [ page 1 of the     │ Ch. 1   │      │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│    original PDF ]    │ Ch. 2   │      │  End of §1.1 · a quick         │
│                      │ …       │      │  question on what you just     │
│                      │         │      │  read · about 1 min            │
│                      │         │      │  [ ↵ Try it ]     keep reading │
└──────────────────────┴─────────┘      └────────────────────────────────┘

F5  first answer (in the Reader)        F6  next day: Today
┌────────────────────────────────┐      ┌────────────────────────────────┐
│ Reader rail · quick question   │      │ Today Library Reader Progress  │
│                                │      │                                │
│ Why does the naive definition  │      │ 15 minutes today: continue     │
│ fail for a loaded die?         │      │ §1.2, then 3 questions from    │
│ ┌────────────────────────────┐ │      │ yesterday.             why? ▸  │
│ │ Write what you can…        │ │      │                                │
│ └────────────────────────────┘ │      │   [ Begin ↵ ]                  │
│ [Compare ↵] · add to practice  │      │                                │
│                                │      │                       1 day    │
└────────────────────────────────┘      └────────────────────────────────┘
```

### 8.2 The Add popover (from *+ Add*, or `Ctrl+O` without a dialog)

```
                                         ┌──────────────────────────────────┐
                                         │ Add to your library              │
                                         │                                  │
                                         │ [ Choose a file… ]               │
                                         │ or paste a link  [____________]  │
                                         │                                  │
                                         │ PDF · web page · arXiv · YouTube │
                                         │ · Markdown · text · subtitles    │
                                         │                                  │
                                         │ More options ▸                   │
                                         │   Only some pages…               │
                                         │   This is a past exam or problem │
                                         │   set (no reading questions)     │
                                         │   Read with text recognition     │
                                         └──────────────────────────────────┘
```

### 8.3 Connect AI (once)

```
┌───────────────────────────────────────────────────────────────┐
│ Get questions on what you read                                │
│                                                               │
│ LearnLoop uses an AI to write questions from your books and   │
│ to give feedback on your answers.                             │
│                                                               │
│   [ Continue with ChatGPT ]                                   │
│   Use an OpenRouter key                                       │
│   Other (advanced) ▸                                          │
│                                                               │
│ What leaves this computer: passages of the books you add, and │
│ your answers, go to the AI you connect. Your library stays    │
│ here.                                                         │
│                                                    [ OK ]     │
└───────────────────────────────────────────────────────────────┘
```

### 8.4 Settings

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Settings                                                         search ⌕  × │
├──────────────────────────────────────────────────────────────────────────────┤
│ AI            Using ChatGPT plan · Manage        What leaves this computer ▸ │
│               Grade my answers:  (•) with AI   ( ) myself                    │
│ Daily time    25 minutes  (also one tap on Today)                            │
│ Reading       Text: (•) mono ( ) proportional   Size: 14                     │
│               Questions while I read: often · (•) sometimes · rarely         │
│ Appearance    Palette: terminal ▾   Today backdrop: axes ▾   Animate map ☐   │
│ Library       ~/LearnLoop · Switch library… · New library…                   │
│                                                                              │
│ Advanced ▸   AI routes · Import · Animation · Token budgets · Spend caps ·   │
│              Embeddings · For builders                                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 8.5 Under the hood

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ LearnLoop   Today   Library   Reader   Progress              [+ Add]  ^K  ⋯   │
├──────────────────────┬───────────────────────────────────────────────────────┤
│ Under the hood       │ Imports & builds                          (was Ingest)│
│                      │                                                       │
│ Imports & builds   2 │  today's IngestScreen, IngestActivity, outline &      │
│ Study-map changes  1 │  select, collections, staging, PDF engine, exam      │
│ Subjects & topics    │  seeding — unchanged, in its terminal voice           │
│ Concept graph editor │                                                       │
│ Analyst views        │                                                       │
│ Mistake history      │                                                       │
│ Calibration          │                                                       │
│ System health        │                                                       │
│ Data                 │                                                       │
│ Files                │                                                       │
│ Inspector            │                                                       │
│ Spend & AI routes    │                                                       │
└──────────────────────┴───────────────────────────────────────────────────────┘
```

---

## 9. Jargon replacement glossary

**The rule.** Internal terms stay in code, specs, under the hood and the CLI. On learner surfaces each term gets the plain words below, or goes. "Hidden" means that the learner surface never needs the concept, and its effect shows in other words or not at all. Counts are the number of distinct visible strings that contain the term today (audit C.6).

| Internal term (count) | Learner-facing words | Notes |
|---|---|---|
| vault (65) | **library**, or nothing | "your library", "Switch library…", "Where your library lives". Errors say *LearnLoop couldn't open your library*. |
| canonical source | **book**, **paper**, **video**, **article**; collectively *what you're learning from* | |
| source library | **Library** | One meaning only (audit C.2: three things are called "library" today). |
| subject | **subject**, shown only in *details* and filters | Created automatically (§6.4). |
| learning object / LO (45) | **topic**, or the topic's title | Never "LO". |
| facet (108) | **skill**, or the skill's title; in the plural, *the parts of this topic* | Facet ids never appear. |
| concept | **idea** in prose; **concept** is fine on Progress → Connections | |
| practice item | **question** (a short one) or **problem** (a worked one) | |
| study map | **your map**, or *questions for this book* | The verb "build a study map" goes. Building happens without being asked. |
| extraction / extract (34) | hidden; *getting this book ready* | Failures name the symptom: *some pages look scanned*. |
| import / ingest | **add** | |
| inventory, unit, outline & select, collection, source set, synthesis (33), shard, append, bootstrap | hidden | Under the hood → Imports & builds. |
| proposal (66), AI inbox, accept/reject, `auto_apply`/`review_required` | hidden; *AI-written · undo*; *2 changes need a look* | Review by exception (§6.5). |
| role (`primary_textbook`, `alternate_explanation`, `problem_set`, `reference`, `lecture`), authority | *Use as: main text · second explanation · problem set · reference*, only in book *details* | |
| brief (outcome, depth, notation, topics) | *Focus and depth*, in book *details* | |
| token, token budget, ceiling, estimate | hidden; money in plain currency only when unusual (§6.6) | |
| external AI consent | *What leaves this computer* (Settings → AI); asked once at connection | |
| registry | hidden | Under the hood → Subjects & topics. |
| probe (28), probe_eig, EVSI, VOI, EIG, entropy, posterior (3), Brier (2), calibration (19) | hidden; *a quick question to see where you are*; **Check what I already know** | A diagnostic question is just a question. Its *why?* says *to tell apart two possible causes*. |
| diagnostic block, episode, observation | hidden; *a short check* | |
| mastery, mastery estimate, ready, Ready %, readiness | *likely to recall* (on Progress, in words: *solid*, *fading*, *not started*) | No percentages on the surface. Percentages live in *details*. |
| demonstrated, certified (16), certification | `●` **on your own** / *you've shown this on your own* | Same vocabulary as the Reader doc §3.4. |
| instructed, primed (10), assisted, source-fresh | `◌` **with help** | A primed retry is *try again with the passage beside you*. |
| cold, cold check (16) | **on your own**; *a check on your own* | As the Reader doc does. |
| assumed (not tested) | *assumed known — not tested yet* | Kept: it is the owner's honest label (DL S2). |
| untested | `○` *not tried yet* | |
| held flat, absent, no blueprint, content debt, system debt | hidden on the surface; *questions for this aren't written yet* where it matters | "system debt" goes entirely. |
| misconception (17), error type, error event | **a mix-up** (*you may be mixing up X and Y*) | The diagnosis wording (`spec_misconception_diagnostics.md`) stays in details. |
| hypothesis (9), working hypotheses | hidden; *possible causes* in details | |
| repair, minimal repair, guided redo | **Fix this** / *redo the part you missed* | |
| claim (17), ClaimSurface | hidden (§7.1) | |
| rubric (10), criterion | *what the grader looked for*, in feedback *details* | |
| grader confidence, grader tier, manual review recommended | *The grader wasn't sure · Check it yourself* | |
| teach-back | **Explain it** | |
| rung, easier/harder variant | **easier** / **harder** | |
| family, task family, blueprint (16), recipe | hidden; *problems like this* | |
| goal frontier, at-risk facets, trajectory, lanes | *on track* / *needs attention before {date}* (goal card) | |
| scheduler, queue, priority, due, overdue, follow-up | **today's plan**; *comes back {when}* | No *overdue* anywhere. |
| session | hidden | Sessions start implicitly (§7.1). "Start a session first" toasts go away. |
| provenance (10), span, anchor, locator, bbox, revision, manifest | *from p. 212*, *from §5.4*; the rest in details | |
| replay, projection, rebuild, shadow | hidden | Under the hood and the CLI. |
| sidecar | *LearnLoop's background service*, in errors only | |
| Codex / codex grading / provider names | the provider's product name, in Settings and *details* only | |
| mvp-0.x, algorithm version | hidden | Under the hood → System health. |
| adjudication, commissioning, persona, mint gate, identifiability | hidden | Under the hood. |
| Marker, pypdf, native, OCR | *text recognition* (OCR), and only in a fix action | Engines are named only in Settings → Advanced → Import. |
| stage names (`bootstrap_synthesis`, `inventory`, …) | hidden | |

**Enforcement.** A vitest check renders the learner-surface components (Today, Library, Reader shell, Practice, Feedback, Progress default view, Add, Settings basics) with fixture data. It fails if the rendered text matches a deny-list built from the left column. This follows the Reader doc's S17 pattern of turning experience rules into tests. The deny-list lives in `src/copy/denyList.ts`. A term can be allowed in a component only through a named exemption with a reason.

---

## 10. Phased implementation plan

**Sizes:** **S** is up to a day of focused work, **M** is two to four days, **L** is a week or more. Each phase ships behind a switch, so it lands live with a kill switch (the owner's rule):
- `[ui] shell = "simple" | "classic"` (default `simple` from Phase 2);
- `[ingest] auto_build`;
- `[ingest] auto_apply_passing_builds`.

Phase 1 needs no new navigation, so it can ship first and be tested with the tester on the current shell.

### Phase 1. Ingest and first run (the first slice): L overall

| # | Change | Size | Files (change) | Stays as is |
|---|---|---|---|---|
| 1.1 | **Silent default library.** With no remembered library, create `~/LearnLoop` via `create_vault` and remember it. Drop the tracked-fixture fallback (Q1, Q2). | S | `src-tauri/src/sidecar.rs` (`default_vault_path`, `resolve_vault_path`); `handlers/vault.py` (allow no subject, default level) | `LEARNLOOP_VAULT`, `fixtures-local/` order, `select_vault`, recent-vault list |
| 1.2 | **`add_source` sidecar method.** One call that registers the source, stores the original, returns a reader target and enqueues extraction. Extraction runs on the opened chapter first (a page-range job), then the rest. Duplicate detection reuses `existingSourceId`. | M | `src/learnloop_sidecar/handlers/ingest.py` (new method), `content/pipeline/runner.py` (chain), `api/client.ts`, `api/dto.ts` | The durable runner, job types, `start_import_batch` (stays for Under the hood) |
| 1.3 | **Auto-build after extraction.** Auto-file the subject; run the progressive build (first chapter opened plus the next) with the default brief and *as you read*; `apply=True` when the gates pass; append the next chapter as the reading position advances. | L | `content/pipeline/quick_add.py` (subject-free plan, reading-order scope), `content/pipeline/jobs.py` (`apply` honoured on the auto path), a reading-position hook in `handlers/reader.py` (`reader_get_progress`/section completion → enqueue append), `vault/writer.py` (auto subject) | Gates, receipts, proposals as records, `revalidate_synthesis_candidate`, the deliberate outline → collection → synthesize path |
| 1.4 | **Read before extraction.** `reader_pdf_view` accepts a revision with no extraction (`available`, `blocks: []`). The Reader opens the PDF surface at once. Text-dependent features show *available in a minute or two* (coordinated with the Reader doc, K2). | M | `handlers/reader.py` (`reader_pdf_view`, `reader_render_view` "preparing" state), `screens/ReaderScreen.tsx` (the shell-facing part only), `components/PdfReaderPane.tsx` | pdf.js reader, the `llpdf://` protocol, originals store |
| 1.5 | **Add UI.** A window-wide drop target, *Choose a file…*, a paste box, `Ctrl+O`, and `Ctrl+V` outside text fields. Several files at once. Opens the Reader on the first file. | M | new `components/AddSource.tsx`, `components/useSourceFileDrop.ts` (reuse), `app/App.tsx` (window-level handlers) | `detectKind` |
| 1.6 | **Empty Library with the drop zone (W1) and BookCard status lines.** Readiness from `get_source_library` gets a learner `status_line` and a `next_action`. | M | new `components/BookCard.tsx`, `components/BookShelf.tsx`; `handlers/ingest.py` (`get_source_library` adds `status_line`); `LibraryScreen.tsx` (a shelf mode) | `SourceLibrarySidebar` (moves under the hood) |
| 1.7 | **Connect AI once.** A sheet with *Continue with ChatGPT* first. Signing in routes every use case (today it routes none). Consent is recorded once (Q4). | M | new `components/ConnectAI.tsx`; `components/ChatGPTPlanSettings.tsx`; `handlers/settings` (default routing on sign-in); config (`[ai] consent` record); `quick_add.py` (consent read from config instead of the per-build checkbox) | Per-route settings, provider profiles, spend caps |
| 1.8 | **Cost pause above a threshold** (Q5). One line on the book card. | S | `content/pipeline/build_plan.py` (estimate → money via the existing price table), `BookCard.tsx` | `SpendBudget` |
| 1.9 | **Plain failure lines** with one action each (§6.7). | S | `BookCard.tsx`, a small `copy/ingestErrors.ts` mapping error codes to lines | Error codes, `retryable` |
| 1.10 | **Fix the Reader's config flash** (`readerEnabled ?? false` while loading) and the silent quick-check timeout, which should become *couldn't write a check for this section · try again*. | S | `ReaderScreen.tsx:620`, `:792-818` | — |

**Phase 1 exit test.** On a fresh machine profile, run the §11 tasks T1–T4 and meet every target there: time to reading under 10 s for a local PDF, no required decisions, first question within the first section.

### Phase 2. The shell: four places, Add, ⋯, Under the hood (M–L)

| # | Change | Size | Files |
|---|---|---|---|
| 2.1 | The new nav, `Today · Library · Reader · Progress` plus `[+ Add]`, `^K` and `⋯`. `Alt+1…4`. Remember the last place. | M | `components/ui.tsx` (`allNavTabs`, `TerminalFrame`), `app/App.tsx` (`TopTab`, `gotoTab`, `renderBody`), new `app/keymap.ts` (one shared key map, replacing scattered listeners where practical) |
| 2.2 | The Under the hood screen hosts the demoted screens unchanged (§5.2), each under a plain title with its old name in small type. | M | new `screens/UnderTheHoodScreen.tsx`; mounts `IngestScreen`, `ProposalsScreen`, `RegistryReviewScreen`, `MaintenanceScreen`, `SqliteBrowser`, `ReviewScreen`, `CalibrationScreen` (full), Terrain/Strata, the graph editor and the Inspector |
| 2.3 | The notice system: errors red with a Retry when `retryable`; notices neutral and auto-dismissing; nothing during Reader reading/working (held and delivered at the destination). | S | `app/App.tsx` (toast host), `styles/app.css:795`, `errors.ts` (a `kind: "error" \| "notice"`) |
| 2.4 | The palette lists plain commands first; CLI pass-through needs `>` (§5.1). | S | `components/CommandPalette.tsx` |
| 2.5 | `ui.shell = "classic"` keeps the old tabs for a month (Q17). | S | `components/ui.tsx` |

### Phase 3. Today (M)

| # | Change | Size | Files |
|---|---|---|---|
| 3.1 | Merge Start into Today: one plan, minutes chips, ↵ Begin, streak in the footer. Remove *scheduler mode*, the queue preview tiles, the `11 concepts…` fallback and the backdrop chip (backdrop to Settings). | M | `screens/StartScreen.tsx` (retire as a screen, keep the backdrop and minutes components), `screens/TodayScreen.tsx`, `screens/today/DailyPlanView.tsx`, `app/dailyPlan.ts` |
| 3.2 | Implicit sessions: the first practice action opens one with the remembered minutes. Remove the "Start a session first" toasts. | S–M | `app/App.tsx` (`openPractice`, `startQuickCheck`, the repair `onPractice`), sidecar `start_session` called lazily |
| 3.3 | Threads: open questions (they open in the Reader, K6), unfinished work, the wrap-up note (Reader S11). Remove the queue-ranking formula, the algorithm version and the ClaimSurface from rows. InboxStrip shows only when it has something. | M | `TodayScreen.tsx`, `components/QuestionQueue.tsx`, `components/InboxStrip.tsx`, `components/ClaimSurface.tsx` (unmounted from Today) |
| 3.4 | A goal card with plain words; TrackRecordView and facet pills go under details. | S | `components/GoalBanner.tsx`, `components/TrackRecordView.tsx` |

### Phase 4. Practice and feedback (M)

| # | Change | Size | Files |
|---|---|---|---|
| 4.1 | Practice card: remove the raw item id, the mode pill and "codex grading". The inspector never shows the expected answer or rubric while that item is unanswered. | S | `screens/PracticeScreen.tsx:875-879`, `components/InspectorOverlay.tsx:462-495` |
| 4.2 | Feedback: a verdict line, what was right, the one next step, *I think I was right*. Rubric, diagnosis, causal attribution, knowledge model and provenance go behind *details ▸*. Return to the origin. | M | `screens/FeedbackScreen.tsx`, `components/DiagnosisCard.tsx`, `components/CausalAttribution.tsx`, `components/KnowledgeModel.tsx` |
| 4.3 | Diagnostic-check results fold into feedback: one verdict and the next step on ↵. Repair becomes a step (*Fix this mix-up · about 4 min*). | M | `screens/DiagnosticReviewScreen.tsx`, `components/ProbeBlockResult.tsx`, `screens/RepairScreen.tsx` |
| 4.4 | Session finish: one calm summary in the ○◌● vocabulary. Remove the fake telemetry. | S | `components/SessionFinishHud.tsx` |

### Phase 5. Progress (M)

| # | Change | Size | Files |
|---|---|---|---|
| 5.1 | Progress opens on the well. Titles replace ids. One headline sentence. The *next* marker is drawn. *Fading* is visible. No auto-rotation by default (it starts top-down). A three-item legend with *more* behind it. The first-run invitation (§7.6). | M | `screens/KnowledgeWellView.tsx`, `screens/KnowledgeMapScreen.tsx`, `handlers/knowledge_map.py` (titles, `nextGap` and decay on the well payload), `wire3d.ts` |
| 5.2 | Learner card on a bead click: *Practise this · Check what I already know · I know this*. The inspector sits under *details*. | S | new `components/SkillCard.tsx`; `components/PlacementControls.tsx` (reuse) |
| 5.3 | Connections: a read-only concept map with titles. The editor goes under the hood, and edits apply with undo. | M | `screens/GraphScreen.tsx`, `components/graphedit/*`, `handlers` (`propose_graph_edits` with auto-apply on the learner path) |
| 5.4 | Goals and the practice exam as cards on Progress. Exam readiness moves here from Maintain, in plain words. | S | `screens/MaintenanceScreen.tsx` (extract), new `components/GoalCard.tsx` |

### Phase 6. Settings (S–M)

| # | Change | Size | Files |
|---|---|---|---|
| 6.1 | Five learner settings first; everything else under *Advanced*, with search. The health chip turns red only when grading or tutoring can't run. | M | `screens/SettingsScreen.tsx`, `components/NativeMediaSettings.tsx`, `app/App.tsx:397-402` |

### Phase 7. Copy and the guard rails (S, then continuous)

| # | Change | Size | Files |
|---|---|---|---|
| 7.1 | A `src/copy/` module for learner-facing strings on the surface screens, starting with the §9 glossary terms. | S | new `src/copy/*.ts` |
| 7.2 | The jargon deny-list test (§9) and the sigh-audit checklist in the PR template. | S | new `src/copy/denyList.test.tsx`; `.github` or `docs/` PR checklist |
| 7.3 | Under the hood keeps its terminal voice. Nothing there is renamed except titles. | — | — |

### Deferred from Phase 1's usability rounds

Phase 1's two persona rounds (`docs/reviews/ux-phase1.md`, "Usability round 1" and "Usability round 2 fixes") fixed everything found on Phase 1's own path. These findings sit on later phases' screens, and those phases carry them:

| Phase | Deferred finding (round) |
|---|---|
| 2 | The ten-tab bar (Ingest, Proposals, Registry, Maintain) and the Ingest screen's developer words ("learnloop[pdf]", "chatgpt_plan"); the build-plan modal's Escape steps back instead of closing (1). Proposals grows on every practice, with duplicate error-type proposals (1). Notes & files opens previewing `vault.lock` (1). The notice system that clears a notice once it is resolved (2.3): round 2 added a stopgap for the session-first notices only (`app/notices.ts`). |
| 3 | The Start epigraph, "learning_objects", "+ create a new vault", "session warm-up" (1, 2). "Today complete · 1 min · 0 items" with a streak after two pages, beside an offer of new items (1, 2). The session counter (025, then 447 after a relaunch) and "41 retrieval reps" on a 10-minute budget (2). Implicit sessions (3.2): round 2 made Today's own begin start the plan; the other "Start a session first" notices remain. |
| 4 | The practice card's raw ids, "constructed_response" and the mastery estimate (1, 2). Feedback jargon and the red "manual review recommended" banner; no "I think I was right"; `r` duplicates the rubric row; "a ledger fact, not a request for your verdict" (1, 2). The self-grade box's "fallback provider_auth_required" and missing "out of 4"; "what made this case fit?" and "(2/3)" numbering (1). |
| 5 | The progress view (the graph is the table of contents in boxes: "concept", "lo_…", "0 edges") and the Graph key bar's duplicate-key warning (1, 2). |
| 7 / Reader doc | The Reader key bar's "capture box union" and "sweep blocks" (1, 2). Small, dim text (1). |
| Owner (Q-L) | Offering to install text recognition from a scan's card. Today the card says how (`uv sync --extra pdf`) and offers it only where it can run (2). |

**What does not change in any phase:** the sidecar's data contracts beyond the additions named above, the durable runner, gates, receipts, replay and rebuild, kill switches, spend caps, the CLI (all 123 commands), the vault's file layout, and the evidence model.

---

## 11. Usability test plan

**Who.**
- The tester, who saw the current app.
- One fresh person who has never seen LearnLoop: ideally a self-directed learner of maths or ML.
- The owner, as a control for the expert path.

Run each tester alone, about 45 minutes, thinking aloud, with the screen and audio recorded.

**Setup.**
- A machine profile with no `~/LearnLoop` and no remembered library: a fresh `LEARNLOOP_CONFIG_DIR` and a fresh home, or a clean user account.
- An AI connection that is either already signed in, or task T0 below.
- Hand the tester three things:
  - a textbook PDF of 200+ pages with real maths (an open-licence probability or linear-algebra book);
  - an arXiv id;
  - a YouTube lecture URL with captions.
- Paid calls are capped by the existing spend cap, set low for the session.

**Baseline.** Run T1–T4 once on the current build (`57d31c63`) with the fresh person *before* Phase 1, so that before and after are measured rather than estimated (§6.8 estimates from code).

**Tasks.** Read them to the tester as goals, never as steps or with LearnLoop's words.

| # | Task (as read aloud) | Success | Observe |
|---|---|---|---|
| T0 | "Get LearnLoop ready to make questions for you." (Only if AI isn't pre-connected.) | Connected without help | Whether *Continue with ChatGPT* is found; whether the consent sentence is read or skipped |
| T1 | "Here's a textbook. Start reading it in LearnLoop." | Reading page 1 | **Time from launch to first page visible (TTFR).** Hesitations over 5 s. Wrong clicks. |
| T2 | "Read the first section. Keep going until LearnLoop asks you something, and answer it." | Answered one question | **Time from launch to first submitted answer (TTFP).** Whether the status line is noticed or understood. Whether the learner waits on a spinner (Reader doc §9.2 "waiting behaviour"). |
| T3 | "Add this paper and this lecture too." | Both on the shelf and openable | Actions per source. Whether drop or paste is discovered. |
| T4 | "Close LearnLoop. It's tomorrow: open it and do today's learning." (Simulate the next day by advancing the clock in a test build, or run it on day 2.) | Plan started with ↵ | Whether Today is understood without explanation. Whether minutes are changed. |
| T5 | "Find out what you've learned so far and what's next." | Says one solid thing and one next thing | What the tester says the well means. Words they ask about. |
| T6 | "You think a grade was wrong. Do something about it." | Contest submitted | Whether *I think I was right* is found |
| T7 | "Spend only 10 minutes a day from now on." | Minutes set to 10 | Where they look first |
| T8 | "This PDF is a scan. Get it working." (Give them a scanned chapter.) | OCR started from the card | Whether the failure line is understood |

**What to record for every task:**
- Time on task.
- Completion: unaided, with one hint, or failed.
- The **number of questions asked** of the moderator.
- Every **internal word** the tester reads aloud or asks about, so the glossary can be checked.
- **Abandonment points**: where they would have quit, by asking them after the task.
- The Single Ease Question, 1–7, after each task.
- A SUS questionnaire at the end.

**Targets after Phase 1 (T1–T3) and Phase 3 (T4).**

| Measure | Before (estimated, §6.8) | Target |
|---|---|---|
| TTFR, local PDF | tens of minutes | **≤ 10 s** after the drop, **≤ 60 s** from launch for a first-time user |
| TTFP (with AI) | tens of minutes, plus Proposals review | **≤ 10 min** from launch (the north star in `spec_new_improvements.md`) |
| Required decisions before reading | 4 | **0** |
| Moderator questions, T1–T3 | — (baseline measured) | **≤ 1 in total** |
| Internal words asked about | — (baseline) | **0** |
| Unaided completion, T1–T5 | — | **5 of 5** |
| SEQ, T1 and T2 | — | **≥ 6** |

**Instrumentation that needs no new table:**
- TTFR: `ingest_batches.created_at` → the first `reader_section_progress` row for that source. If that proves too coarse, add one `reader_opened` interaction event, which is the only new write.
- TTFP: the source added → the first `reader_authored_questions.answered_at` or attempt.
- Builds: queued → applied.

A small Under-the-hood report, *First-run funnel*, computes these from the database. It doubles as the owner's check that later changes don't regress the first run.

---

## 12. Coordination with the Reader experience design

`docs/specs/ux_reader_workbench_v1.md` (branch `docs/reader-workbench-spec`, read at `8deb75be`) owns the inside of the Reader. This document owns the shell around it: navigation, Add, Today, practice and feedback, Progress, settings and Under the hood.

### 12.1 Where the two documents agree, and what this one adopts app-wide

| Reader doc | Adopted here as |
|---|---|
| §3.4 evidence vocabulary: `○` untested · `◌` with help · `●` on your own · *assumed known (not tested)* | The only evidence vocabulary on every learner surface: Today, feedback, Progress, book cards (§4.2 rule 9) |
| §3.4 three voices: source `§`, model `◇`, learner `›` | Feedback and Today use the same glyphs and labels for model-written text (feedback explanations, plan *why?*, tentative questions) |
| U5 and §4.12 attention budget: no toasts or modals in reading or working | The shell's notice host (§7.9) holds every non-error notice while the Reader is in its reading or working posture, and delivers it at the next destination (Reader S11) |
| U9 "never wait" | Add (§6) returns control at once; nothing on the ingest path blocks reading |
| U12 threads, never debt | Today has no counts. Open questions and unfinished work appear as threads (§7.1) |
| S6: feedback returns to where the attempt started | Adopted for all feedback (§7.5) |
| S11: the wrap-up note shows at the destination | Today shows *Reading wrap-up ready — under a minute ▸* for one view (§7.1) |
| Q7: money shown only near a cap | The same rule for builds (§6.6) |
| §8 anti-patterns (debt counts, engagement as progress, trait labels) | Applied app-wide by the sigh audit (§4.4) |

### 12.2 Conflicts and items to settle

| # | Item | Reader doc says | This doc says | Proposed resolution |
|---|---|---|---|---|
| **K1** | **Who the user is** | "Nobody else will use it, so the design can trust its user, skip onboarding theatre and give full control." (header) | A tester has used it and was lost. First run must work for someone who isn't the owner. | Both documents refuse onboarding theatre. This one adds a *working default path* (silent library, Add, empty states that teach), not a tour. The Reader doc should add one line: learner-facing copy passes the §9 glossary (some of its proposed copy names "facets" and "LOs" in rationale text only, which is fine). |
| **K2** | **Opening a book that isn't extracted yet** | Assumes an extracted source. Span anchoring, cues, section checks and the workbench all need the IR. | §6.3: the Reader opens the original PDF at once and features that need extraction say *available in a minute or two* until it lands. | The Reader doc takes ownership of the **preparing** state inside the Reader: which affordances work on the PDF text layer alone, and how each pending one reads. This doc owns the header status line and the backend change (`reader_pdf_view` without an extraction). |
| **K3** | **The first questions for a new book** | The section-boundary offer (exists) and RW6b cold checks | §6.3 and §6.8: the first question is the section quick check, which needs only the extracted text. Graded questions follow from the background build | The mechanism is agreed. The producer (`spec_reader_quick_check_producer.md`) already needs only the IR, and it fires in *read closely* mode near a section's end. Two Reader-doc items follow: keep *read closely* as the default posture for a new book, and make the check's *Add to practice* bind to the study map once the build lands (today it needs an LO). |
| **K4** | **Sessions** | Not discussed. Workbench submits and section checks just happen. | Sessions become implicit (§7.1). The toasts "Start a session before opening practice" and "Start a session first: the quick check runs inside a practice session" go away. | Adopt in both. The sidecar opens a session lazily on the first practice action, from anywhere, with the remembered minutes. |
| **K5** | **The Reader's library picker** | Unchanged ("← library") | Library is a top-level place. The Reader with no book open shows the same shelf. | One shelf component (`BookShelf`), used by Library and by an empty Reader. The Reader's back control reads *← Library* and goes to the Library place. |
| **K6** | **Two Asks** | Reader asks live in the Reader's Ask and inquiry tree; Today's question queue reopens them in the Reader (§3.1 table: "opening a question from Today's queue") | Today's threads open in the Reader at the passage, not in the global AskOverlay (as they do today, audit C.1) | Adopt the Reader doc's routing. The global AskOverlay stays for practice and feedback. |
| **K7** | **Alt** | Uses `Alt+←/→` and `Alt+↑/↓` inside the Reader. Reserves `alt+digit` for the top navigation. | `Alt+1…4` for the four places | No conflict. **Bug to fix first, in the Reader:** a bare Alt press clears the selection (`ReaderScreen.tsx:1418-1433`), so any Alt chord loses a capture. |
| **K8** | **The 12-action selection rail and 9 "save for practice" verbs** | Replaced by the intent box (RW1b) and dispositions | Wants one learner verb for "bring this back": *Remember this* | The Reader doc owns the inside of the rail. This doc asks that the learner-visible verbs which feed the scheduler collapse to at most three: *remember this*, *practise this now*, *work through this*. The others stay as dispositions in details. Flagged for the Reader doc's §10. |
| **K9** | **Typography** | Q1: default mono, the owner's look | Keeps the look; learner-facing labels move to sentence case ("Back to today's plan", not "BACK TO TODAY'S PLAN"); headings lose `❯ learnloop {command}` frames | Compatible. Owner's call on sentence case (Q11 below). |
| **K10** | **The quick-check blink** | S12: replace it with a static `◆ n` | Same rule app-wide: nothing LearnLoop starts blinks or pulses (the sigh audit) | Agreed. |

---

## 13. Open questions for the owner, with recommended defaults

| # | Question | Recommended default | Why |
|---|---|---|---|
| **Q1** | Where does the default library live? | `~/LearnLoop`, visible and easy to back up | It is a folder of the learner's own files (the "files in folders" promise, N1). The alternative is `~/.local/share/learnloop`, which hides the learner's own notes. |
| **Q2** | Dev fallback: should a launch with no remembered library still open `fixtures/linear_algebra`? | **No.** Create a fresh library instead. The owner keeps `LEARNLOOP_VAULT` and `fixtures-local/` | The tracked fixture is the owner's working vault (CLAUDE.md). A tester should never land in it, and opening it dirties `git status`. |
| **Q3** | Auto-apply study maps that pass every gate, with undo? | **Yes**, for builds started by Add and progressive builds. Deliberate builds from Under the hood keep their current behaviour. | It extends R1 (practice families auto-accepted with undo) to study maps. Proposals become review-by-exception. |
| **Q4** | Consent: once per provider, or once per build? | Once per provider and data flow, recorded with date and provider. No per-book opt-out (owner, 2026-10-13: the draft's *Keep this book on this computer* is retired, §6.6). | Per-build checkboxes are a ritual the learner learns to click through. Once, clearly, is more honest. |
| **Q5** | When does a build ask before spending? | When its estimate exceeds **$1**, or 25% of the remaining daily cap | Most single-chapter builds stay silent. Whole-book builds ask. |
| **Q6** | Progressive builds (the chapter being read, plus one ahead) or whole book up front? | Progressive. *Build questions for the whole book* stays in book details. | It reaches the first question fastest, costs least, and follows M3 (a personal path through the book). |
| **Q7** | Subjects: automatic, or named by the learner? | Automatic: named from the book, filed by an LLM, renamable in book details | DL C2 already decided this for captures. It removes the first-run trap. |
| **Q8** | Keep the Start screen's backdrops (Lorenz, Julia, three-body…)? | Keep one, the calm `axes`, as Today's header art. The cycler moves to Settings → Appearance. | The owner built them and they give the app character. The `backdrop:` debug chip on the main screen goes. |
| **Q9** | Streak | Kept on Today's footer only, quiet: *4 days*. Not in the Reader (Reader doc). Not in red. | Owner decision P5. |
| **Q10** | Tab labels `[1]Start`… | Plain labels. Key hints go in tooltips and in `?` help. | The labels currently show keys that are actually Alt chords, and plain digits do something else on Today. |
| **Q11** | Sentence case and fewer `❯` frames in learner copy? | Yes for learner surfaces. Under the hood keeps the terminal voice. | Lower-case mono reads as a console, which tells a newcomer "this is for engineers". |
| **Q12** | Where is Under the hood reached from? | `⋯ → Under the hood` and the palette, never the top bar. *Always show details* is an owner setting. | The owner uses it daily. A tester should never need it. |
| **Q13** | Past-exam seeding | `Add → More options → This is a past exam` | It is rare, and a mode chip on the main Add path confuses everyone else. |
| **Q14** | Starting level | Not asked. Inferred from answers; *I know this chapter* in the Reader's Guide marks it *assumed known* (DL S2) | The first answers are the placement (DL S1). |
| **Q15** | Goal wizard and practice exam on first run | Not offered until there is a book and a week of practice. Progress shows *Set a goal (optional)*. | A goal is a commitment a new learner can't yet make well. |
| **Q16** | ClaimSurface ("was this queue choice useful?") on Today rows | Remove. Keep *this seems off* on feedback only. | Labelling the scheduler is the owner's research task, not a learner's (audit B.5). The data can come from skips, *too easy* and contests instead (DL R1). |
| **Q17** | Should the old shell stay selectable, and for how long? | `ui.shell = "classic"` for one month after Phase 2, then removed. Its screens stay under the hood. | Respects muscle memory (J8) and keeps a kill switch. |
| **Q18** | Library location of `state.sqlite` in the Files view | Hidden from the Files tree. Reached through Under the hood → Data, read-only by default. | Editing the live database from a file browser is a footgun. |
| **Q19** | A lighter answer type for recall checks (one line, or "show answer, then got it / not quite") next to written answers graded by a model | Explore it as a separate spec. Use it for in-reading checks and for maintenance of `●` items. Keep model grading for anything diagnostic. | Matuschak's 6-second prompts (N4) versus LearnLoop's model-graded answers, which take 10 s or more. The heaviness is real (§3, F6). It is out of scope for this UX pass. |
| **Q20** | A forgiving streak: one "rest day" a week that doesn't break it? | Yes, silently. The footer still shows the true count of days. | Silverman & Barasch 2023: the drop-off after a broken streak is "attenuated when consumers can 'repair' a broken streak". Lally et al. 2010: one missed day doesn't harm habit formation. The streak itself stays (P5). |

---

## Appendix A. Screenshots of the app as it is

**How these were made.** The built frontend at `57d31c63` ran in headless Chromium, behind a small shim that forwards Tauri `invoke` calls to the real Python sidecar. The sidecar ran in a scrubbed environment with no AI provider reachable, so no paid calls were made. Two kinds of library were used:
- a fresh library (`fixtures-local/ux_fresh`);
- a backup-API copy of the tracked `linear_algebra` fixture (`fixtures-local/ux_la`).

The owner's working vaults were never opened. Because no AI was connected, grading shows *self-grade required*. With an AI connected, those screens show *codex grading* instead. The files are in `docs/ux/screenshots/`, downscaled.

| File | What it shows |
|---|---|
| `01-first-launch-no-vault.png` | A launch with no usable library. The first thing on screen is a red box: "LearnLoop could not confirm whether this action completed. Check the current state before trying it again." Its `retry vault load` button wraps into three lines. |
| `03-fresh-start-screen.png` | Start on a fresh library: the `backdrop: axes` debug chip; "Escape will make me improve"; "0 concepts in scope · 0 active learning_objects · 3 error types"; "Nothing due today."; and `begin today's plan · 25 min ↵`. Nothing mentions adding a source except `+ create a new vault ▸`. |
| `06-fresh-ingest-empty.png` | Ingest on a fresh library. There are two entry points, `+ create study map` and `▶ import source`. You must choose between two modes, `canonical source` and `exam seeding`. Also visible: six kind chips, a `pdf engine` picker, `subject (optional)`, `set your level`, `+ stage`, and four paragraphs of help about revisions, extraction, outline & select, collections and roles. |
| `10-fresh-reader.png` | The Reader on a fresh library: "no ready sources yet — ingest a source in the Ingest tab, then return here to read it." and "open demo chapter (fixture)". |
| `14-fresh-settings.png` | The Settings overlay, which opens on per-use-case AI routing. |
| `15-fresh-command-palette.png` | The command palette, titled `learnloop shell`. |
| `16-new-vault-wizard-empty.png` | The new-vault wizard. It has one step (`1·vault`), which defines a vault as a folder holding "the SQLite state". |
| `18-new-vault-created-lands-in-ingest.png` | After you create a vault: `Quick add → study map`, `NEW VAULT SETUP · GUIDED INGEST · 01 source + pages → 02 inventory budget → 03 review + build`. Then come PDF pages, subject, `Enrichment · interesting adjunct`, `INVENTORY OUTPUT BUDGET · PER UNIT 12000 tokens`, `no LearnLoop token ceiling`, `customize brief`, `reader on`, and "one confirmation — import + inventory + synthesis run after this". |
| `20-la-launch-resumes-practice-item.png` | Launching the fixture copy resumes a saved practice item. Its header shows the raw item ID (`pi_what_makes_test_strategy_01`), a `constructed_response` pill, `self-grade required` and `MASTERY ESTIMATE 0.72 ±0.23`. The `THIS CARD: reword · retire · ↓ easier · ↑ harder · ◊ teach it` row and `0 chars · 0 words` follow. Hint, don't-know, skip and ask-tutor exist only in the key bar. |
| `21-la-today.png` | Today's full list on the fixture copy, whose older configuration has no daily plan. It shows the inbox strip; `TODAY · SESSION 025`; `vault ● healthy · ai:codex_low ● down · queue ● ready`; `DUE 21 · PROBE 0 · LATER 19`; *Decay pressure* listed by snake_case facet IDs; about 40 rows, each with a raw item ID, a mode pill and *MASTERY ESTIMATE*; the *Scheduler choice* and *Why this position* panels; and the queue-ranking formula at the foot. |
| `25-la-proposals.png` | Proposals: `AI inbox · 39 pending · 278 resolved · 39 batches`; `local app-server · revision … · ai:codex_low ● offline`; raw ULIDs; `review_required` / `auto_apply` pills; and the payload as raw key/value lines. |
| `29-la-maintain.png` | Maintain on the fixture copy: the measurement and causal health blocks come first. |
| `31-la-knowledge-field-well.png` | The well, reached through Graph → knowledge field → well. Its 39 rim labels are overlapping snake_case facet IDs, most marked `untested`. The side panel shows `Ready variance 0.0557`, `evidence mass 0.73`, `Capability rim` and `Used by` with a raw LO ID. The legend has eight entries. |
| `34-la-library-sqlite-browser.png` | The Library tab: the vault's file tree, with the live `state.sqlite` open. It shows 304 tables, a delete `✕` on every row and an SQL console. |
| `36-la-reader-pdf-source.png` | The Reader on a PDF. It reads well. Its title, however, is the raw `file:///home/…/sheldon_axler-linear_algebra_done_right.pdf` URI, and the key bar teaches `ctrl+drag`, `release ctrl`, `alt` and `alt+drag`. |
| `40-la-learner-model-diff-overlay.png` | The learner-model *diff* overlay. The palette's `diff` command is the only way to reach it. |
