# UX Phase 1: ingest and first run

**Stage:** `ux-phase1`, branch `ux/phase1-first-run` (worktree `learnanything-ux-impl`), base `4276a8d7` (main `f2f02e32` plus the UX spec).
**Spec:** `docs/specs/ux_learnloop_v1.md` §6 and §10 Phase 1 (items 1.1–1.10), with `docs/ux/audit_current_screens.md` and `docs/ux/research_notes.md`.
**Owner decisions in force:** Q1–Q7 at their recommended defaults (owner approved beginning the work, 2026-10-13); frictionless defaults, honest labels, live behind kill switches, no shadow stage.

## 1. Plan

Phase 1 asks for a learner who launches LearnLoop, drops a book in and is reading it within seconds, with no decision on the way, while LearnLoop prepares the rest in the background. Ten items:

| # | Item | Plan |
|---|---|---|
| 1.1 | Silent default library (Q1, Q2) | The shell falls back to `~/LearnLoop`, created by the sidecar, never to the tracked fixture. |
| 1.2 | `add_source` | One RPC: register a local file and store its original before returning; queue the import and an automatic-build planner in one durable batch. |
| 1.3 | Auto-build after extraction (Q3, Q6, Q7) | A new `auto_study_map` job: automatic subject, reading-order scope, the ordinary inventory → synthesis build applied when the gates pass; one chapter ahead as reading advances. |
| 1.4 | Read before extraction | `reader.pdf_view` answers for a book with no extraction; the Reader shows the original with a "preparing" header. |
| 1.5 | Add UI | Drop anywhere, Choose a file…, paste a link, `Ctrl+O`, `Ctrl+V`; several files at once; the Reader opens on the first. |
| 1.6 | Empty Library and book cards | W1 drop zone; one card per book with one quiet `status_line`. |
| 1.7 | Connect AI once (Q4) | A sheet with Continue with ChatGPT first; connecting routes every use case; one consent record per provider in the library's config. |
| 1.8 | Cost pause (Q5) | Pause only above $1 or 25% of the remaining daily cap. |
| 1.9 | Plain failure lines | One sentence, one action, raw text in details. |
| 1.10 | Reader fixes | No "reader disabled" flash while settings load; a timed-out quick check says so. |

Kill switches (spec §10): `[ingest] auto_build` and `[ingest] auto_apply_passing_builds`, both default `true`. The old flow stays reachable: the Ingest tab, Quick add, the new-vault wizard and the Library's file tree are unchanged (the Library tab now opens on Books, with Notes & files beside it).

## 2. What was built

Commits on the branch, oldest first:

| Commit | What |
|---|---|
| `101a7b81` | Fail-first Python tests (add_source, the automatic build, consent once, the default library) and desktop-only pins. |
| `ba24b754` | Backend: `learnloop/content/pipeline/add_source.py`, the `auto_study_map` job, `handlers/first_run.py`, the library status line, `reader.pdf_view` preparing, the reading-position hook, `initialize` `createIfMissing`, config. |
| `fb433739` | Rust: `~/LearnLoop` instead of the tracked fixture; the four passthrough commands; Rust tests. |
| `42c7c7f1` | Fail-first vitest (Add, shelf, cards, connect sheet, preparing Reader, `Ctrl+O`/`Ctrl+V`, Reader fixes, the jargon deny-list); DTOs and API client calls. |
| `58703c76` | Frontend: `AddSource`, `BookCard`, `BookShelf`, `ConnectAI`, `LibraryPlace`, `PreparingView`, `useGlobalAdd`, `copy/denyList.ts`, `copy/ingestErrors.ts`, App wiring, ReaderScreen preparing branch and fixes. |
| `9369a459` | Fixes found by the headless walkthrough (§5): the original PDF is visible while preparing, "Chapters found", removable failed links, the "already in your library" line. |
| `033e3fe1` | Quick add reads the recorded OK instead of asking per build. |

### By item

**1.1 Silent default library.** `src-tauri/src/sidecar.rs`: `resolve_vault` returns a path and whether it may be created. The order is unchanged until the last step: requested → selected → `LEARNLOOP_VAULT` → remembered (`last_vault`) → first vault under `fixtures-local/` → **`$HOME/LearnLoop` (created)**. The tracked `fixtures/linear_algebra` is never a fallback any more; `LEARNLOOP_VAULT=fixtures/linear_algebra` still opens it. Only the default library carries `createIfMissing`; `initialize` (`handlers/app.py`) then runs `bootstrap.create_vault` (no subject, no level, AI settings and consent inherited from the machine defaults) and refuses to scaffold into a non-empty folder (`library_folder_in_use`, "LearnLoop couldn't open your library: … already has other files in it."). The shell remembers the created library as the last one.

**1.2 `add_source`.** `add_source(sources, pages?, problemSet?, keepLocal?, textRecognition?)` returns one item per input: `added` (a local file, registered with `register_source_revision` before the call returns, original stored, title from the PDF's own title or the file name in words, never a `file://` URI), `queued` (a link, fetched by the queue), `existing` (already in the library: nothing duplicated, "Already in your library — opened where you left off."), or `unsupported` (one plain line). Each add is one `add_source` batch: `import` → `auto_study_map` (depends on it), at priority 110 so the import drains ahead of question builds (100). The import re-registers idempotently (same canonical URI and bytes).

**1.3 Automatic builds.** `run_auto_study_map` (the `auto_study_map` handler) records every decision as its job result, which is the ledger the card, the progressive build and undo read:
- `skipped` (`auto_build_off`, `problem_set`, `nothing_to_build`), `waiting` (`no_ai`, `needs_consent`, `kept_local`), `paused` (`cost`), or `building` (with the build batch, chapters and estimate).
- **Subject (Q7):** the source's existing source-set subject, else an existing subject with the book's name, else a provisional subject named from the title ("Probability — The Long Version" → `probability`).
- **Scope (Q6):** a source that fits Quick add's scope cap is built whole; otherwise the first non-front-matter chapter and the next (tiny page-units accumulate to a floor; the first chapter is always built). The source set is `sset_quickadd_<source>` (Quick add's own id), scopes only grow.
- **Build:** the ordinary `inventory` → `bootstrap_synthesis` batch (mode `auto`, so later chapters route to append), brief `practice_items = "as_you_read"`, `apply = [ingest] auto_apply_passing_builds` (same gates, receipts and proposal records as before).
- **One chapter ahead:** `reader.mark_section_progress` (on reveal or completion, best effort) calls `advance_reading_build`: the chapter being read and the next, minus what is built; only for books whose questions came from Add and were not undone, nothing while `auto_build` is off. *(Corrected after the Codex review, F7: a position that arrives while a build for the book runs is now kept in `source_auto_build_state` and acted on when that build finishes, on reconnection and when the library opens; before, it was dropped.)*
- **Undo (Q3):** `source_action undo_questions` rejects the book's applied proposals for the item types the revert path supports: topics become dormant, questions inactive, links between ideas removed. Ideas, skills and question recipes stay as inert records (see deviation D4). *(After the Codex review, F5 and F12: Undo first advances the book's build generation and cancels its queued work, so a build already running cannot apply; the verdict is recorded in `judgment_ledger`.)*

**1.4 Read before extraction.** `reader.pdf_view` accepts a source or revision with no finished extraction: `available` (original in the store), `preparing: true`, `extractionId: null`, `blocks: []`. `screens/reader/PreparingView.tsx` shows the original PDF at once with "← Library", the title, one quiet line ("◐ Getting this book ready") and "Highlights, notes, Ask and questions on each section — available in a minute or two, when the text is ready."; it polls the shelf and hands over to the full Reader when the text is ready. `ReaderScreen` changes are limited to that branch, the picker listing every book (no more "N sources are still getting ready"), and 1.10. `PdfReaderPane` shows every page of the original when there is no block geometry (`components/pdfPages.ts`); before, it showed none (this also fixes a blank original surface for text-only pypdf extractions).

**1.5 Add UI.** `components/AddSource.tsx`: the Add box (Choose a file…, paste a link, More options ▸: Only some pages, past exam or problem set, keep on this computer, text recognition), `useAddSource`, the `+ Add` popover and the full-window drop overlay. `App.tsx`: `+ Add` in the header, a window-wide drop target at the lowest drop priority (Ingest, Quick add and the wizard keep their own), `Ctrl+O`, and `Ctrl+V` with no text field focused when the clipboard holds a link, an arXiv id or a file path (`app/useGlobalAdd.ts`). A file opens in the Reader at once; a link opens when its text is ready.

**1.6 Library.** `screens/LibraryPlace.tsx`: Books | Notes & files. Books (`components/BookShelf.tsx`, `BookCard.tsx`): empty, the first-run welcome (W1) with the AI line only when nothing can write questions; otherwise one card per book (title, kind, one status line with at most one action, Continue/Open, details ▸ with the raw message, subject, *Build questions for the whole book*, *Undo this book's questions*, *Read it again with text recognition*, *Open in Imports & builds*), links still being fetched, and Add at the foot. First launch on an empty library lands here instead of Start. `get_source_library` cards gain `status_line`, `kind_noun`, `subject_id`, and the snapshot gains `pending`.

**1.7 Connect once.** `components/ConnectAI.tsx` and `connect_ai` / `get_ai_connection`: Continue with ChatGPT first (signs in through the browser if needed, then routes grading, diagnosis, ingest, tutor and animation to a `chatgpt` plan profile with the account's first listed model); Use an OpenRouter key (saves the key, routes the same use cases); Other (advanced) ▸ opens Settings. When an AI is already set up (e.g. Codex), the sheet says "LearnLoop is set up to use ChatGPT." and the one sentence on what leaves the computer, with **OK**. Consent is `[ai.consent.<provider family>]` with `granted_at` and `data_flow = "passages_and_answers"`, mirrored to the machine's AI defaults so a library made later inherits it, and connecting releases every book that was waiting. Quick add's synthesis consent entry now carries the recorded OK and starts ticked.

**1.8 Cost pause.** `[ingest.cost_pause]`: `threshold_usd = 1.0`, `daily_cap_fraction = 0.25`, `daily_cap_usd` unset, `default_price_per_million_tokens = 5.0`, `prices.<profile>`. The estimate is the build plan's input plus maximum output tokens times the route's price; Codex and the ChatGPT plan cost nothing extra and never pause. A pause shows "Building questions for Ch. 1–2 would cost about $3.10 · Build them"; Build them passes the pause once for those chapters. *(Corrected after the Codex review, F2: this was a confirmation threshold only, not a spend limit. Now "Build them" never passes `daily_cap_usd`; every paid job of an automatic build is admitted through `SpendBudget` against the build's authorization and the day's cap, priced at the route resolved when it runs, with spending counted from the model-call receipts; subscription builds keep a token estimate with `cost_basis = estimated_only` instead of recording $0; `learnloop sources build-preview` is the zero-call dry run. Corrected again after the Codex re-review, F2: beyond the job's admission, every physical request of an automatic build (transport retries, a provider's JSON repair, append reconciliation's follow-up call, each parallel inventory worker) is admitted by a `MeteredRequestGate` against the same limit and settled with what it reported.)*

**1.9 Failure lines.** On the card: "Couldn't reach the page · Try again", "This video has no captions · Try again", "Couldn't read this PDF · Try again", "Questions for Ch. 3 need another try · Retry", "Some pages look scanned · Read them with text recognition", "Maths may look rough in the text view · Fix it"; a failed link also offers Remove. In the Add box and the sheet: `copy/ingestErrors.ts` maps codes to one sentence.

**1.10 Reader fixes.** `readerEnabled` reads as on while the contract loads and the disabled notice shows only when the config says so. A section's quick check that takes past the poll window shows "Couldn't write a check for this section · Try again".

**Plain words.** `copy/denyList.ts` holds the glossary's left column (49 terms) with named exemptions; `copy/denyList.test.tsx` renders the Add box, a card for every line the sidecar can produce, the empty and full shelf, the connect sheet in its three states and the preparing Reader, and fails on any term. The backend status lines are checked against the same vocabulary in `tests/test_ux_phase1_auto_build.py`.

**Algorithm successor.** None. No scoring, scheduling, projection or serving change. Auto-applying study maps from Add is a content change under the owner's R1 decision ("auto-accepted when confident, with undo"); the defaults snapshots in `config/template.py` were recomputed because the effective config gains the new keys (comment added there). No migration in the stage itself (job types are open strings; consent lives in config). *(The Codex review fixes add migration 186: `source_artifacts.keep_local` and the WORKFLOW table `source_auto_build_state`; see `ux-phase1-codex-review.md`.)*

## 3. Deviations

| # | Spec says | Built | Why |
|---|---|---|---|
| D1 | Extraction runs chapter-first (a page-range import of the opened chapter, then the rest). | The whole book is extracted in one job; the original PDF is readable at once and the **first build** is chapter-scoped. | Unit and span ids are positional (`u1…`, `s1…`). A chapter extraction followed by a whole-book extraction of the same revision gives two incompatible id spaces: the Reader would switch extractions mid-read, and the study map's source-set scope and provenance would point into the superseded one. Doing it safely needs the revision-refresh re-anchor chain (span aliases, `reanchor_selection_to`, annotation re-anchoring) applied to a same-revision page-range → whole run. Proposed as Phase 1b. Reading is never blocked meanwhile; with Marker on a CPU the preparing state can last minutes. |
| D2 | Subjects filed by an LLM, renamable in book details (Q7). | Deterministic filing: existing source-set subject → a subject with the book's name → a provisional subject named from the title. The subject shows in details, read-only. | No LLM filer exists yet (DL C2 is unbuilt for captures too); renaming a subject is a Registry operation. |
| D3 | Cost "via the existing price table" and "the remaining daily cap". | A price per profile in `[ingest.cost_pause]` (default $5 per million tokens for metered routes), no daily cap unless set. | There is no chat-model price table and no daily dollar cap in the code (`SpendBudget` is per command). *(Corrected after the Codex review: subscription routes are never paused or capped under the owner's 2026-10-12 rule, but their cost is kept as a token estimate, `estimated_only`, not recorded as $0.)* |
| D4 | Undo takes the book's questions back out. | Topics dormant, questions inactive, idea links removed; ideas, skills and recipes stay as inert records. | `reject_applied_items` cannot revert facets, blueprints, rubrics or a still-referenced concept. Nothing the learner earned is deleted. |
| D5 | The status line hides when there is nothing left to say ("done → quiet"). | "Questions ready for Ch. 1–2 · Undo" stays on the card. | It carries the one-tap undo; when to retire it (days, first answer) is an owner call (Q-A below). |
| D6 | `get_source_library` gains `status_line` and `next_action`. | `status_line` with its one action; Continue/Open is the card's next action. | A separate field duplicated the line's action. |
| D7 | Phase 1 needs no new navigation. | A `+ Add` button in the current header; Library opens on Books. | Add must be reachable from every place; the four-place shell is Phase 2. |
| D8 | Audio: a "Transcribing — about N min" card; opens when the transcript is ready. | Audio uses the generic "Getting this recording ready" line and the preparing view's "It opens here as soon as it is ready." | No transcription-time estimate exists to show. |
| D9 | While preparing, Ask about a selection is grounded in the page text. | Text features say "available in a minute or two". | Reader-doc territory (coordination item K2). |
| D10 | Notices are neutral (§7.9). | "Already in your library — opened where you left off." uses today's toast. | The notice host is Phase 2 (item 2.3). |
| D11 | "Before" count: about 20 actions and 4 required decisions, including accepting proposals. | Corrected to about 18 and 3 (§4). | At the base, `enqueue_quick_add_build` already sets `apply: True`: a Quick add build applies itself; the Proposals steps are not on that path. |

Other notes:
- The PDF pane fix (1.4) changes `PdfReaderPane`, which the spec lists for Phase 1; its "N ingested pages" label now reads "original pdf" when there is no geometry.
- `CLAUDE.md` still says the desktop default is "last-opened, then fixtures-local/*, then tracked fixtures/linear_algebra"; it is now "…then `~/LearnLoop`". Not edited here (project instructions are the owner's).

## 4. Before and after, counted from the code

**Scenario (spec §6.8):** a first-time user with an AI already connected adds a textbook PDF, starts reading, and answers a first question.

**Before (base `4276a8d7`):** spec §6.8 steps 1–19 and 22–24, with D11's correction: find `+ create a new vault ▸`; read the vault definition; choose a folder; type a subject (required in practice: Quick add's `enqueue_quick_add` raises `subject_required`); choose a level; create; Quick add opens; choose the PDF; optional page range; five offered decisions; Analyze; Import first; a blocking extraction wait inside the dialog; read the confirmation; tick the external-AI consent (`allConsented` gates Confirm); Confirm & build; wait for inventory and synthesis on the Ingest tab; open the Reader tab; pick the book. **About 18 actions to reading, 3 required decisions (folder, subject, consent), about 10 offered, 2 long waits, about 25 internal terms.** Reading starts after extraction plus the build.

**After (this branch):**

| # | The user… | From the code |
|---|---|---|
| 1 | Launches | `default_vault_in` → `~/LearnLoop`, `initialize createIfMissing`; `landOnLibraryIfEmpty` opens Library → Books: W1. |
| 2 | Drops the PDF (or Choose a file… + pick: 2) | `useSourceFileDrop` (priority −10) / `pickSourceFiles` → `add_source` → `openAddedItem` → Reader. |
| 3 | Reads the original PDF | `PreparingView` + `reader.pdf_view` (`preparing: true`); the full Reader takes over when the text is ready. |
| 4 | Keeps reading | The card line goes "Getting this book ready" → "Chapters found" → "Questions for Ch. 1–2 in about 5 min" → "Questions ready for Ch. 1–2 · Undo". |
| 5 | Reaches the end of a section, opens the check, answers | The Reader's existing section check (read closely, past 60% of the section), unchanged. |

**After: 1 action to reading (2 with the file dialog), 0 required decisions, 0 blocking waits, 0 glossary terms on the Phase 1 surfaces (deny-list test).** Not yet clean: the Reader's own chrome ("extracted text →", "quick checks on", the key bar) is Reader-doc territory.

When the provider is set up but the one OK is missing (an existing Codex vault): **+2 actions, once per provider** (Review → OK). With no AI: Connect → Continue with ChatGPT → the browser sign-in, then questions start by themselves.

| Source | Before | After (to reading / to first question) |
|---|---|---|
| Textbook PDF | ~18 / ~20+ | 1 / 2–3 |
| arXiv id or web page | ~16 / ~18+ | 1 (paste) / 2–3, opens when its text is ready |
| A second book | ~11 / ~13+ | 1 / 2–3 |

**Measured in the headless walkthrough** (§5; pypdf, no Marker, the sidecar busy extracting): the preparing view showed 1.0–2.1 s after the add click for a 157-page PDF, the original was drawn by about 3 s, and the full Reader took over at 8–11 s; a 5-page PDF reached the full Reader in 3.7 s.

## 5. Manual run (headless walkthrough)

The real sidecar under the frontend's dev build, in headless Chromium, through the UX audit's Tauri shim and an adapted bridge (scratchpad `usability/`). The sidecar ran in a network namespace (`unshare -cn`) with a scrubbed environment: a fresh scratch `HOME` (so the first run created `<scratch>/runA/home/LearnLoop`) and a fresh `LEARNLOOP_CONFIG_DIR`. Two runs:
- **No AI (run A):** first launch lands on W1 with the AI line; Choose a file… opens the preparing Reader on the original; the card says "Questions need an AI connection · Connect"; the sheet opens; a link (no network) shows "Couldn't reach the page · Try again"; plain words for an unrecognised input; adding the same book again opens it.
- **Scripted fake AI (run B):** a `sitecustomize` wired the test suite's house fakes (`FakeInventoryClient`, `FakeSynthesisClient`, built on `tests/structured_ai.py`'s `StructuredClientFake`) into the sidecar's job seams and marked the route ready; output is clearly canned ("bootstrap map for symmetric matrices"). The card asks for the one OK; the sheet shows the sentence; OK → "Chapters found" → "Questions ready for Ch. 1–2 · Undo"; the subject `probability` and `[ai.consent.codex]` were written; Undo → "Questions for this book were taken back out · Build them again".

It found four defects, fixed with fail-first tests in `9369a459` (the blank preparing surface, the planning line, the stuck failed link, the missing "already in your library" line). Screenshots: `docs/ux/screenshots/phase1/`. **No paid call and no real provider was used anywhere in this stage**; the owner's working vaults were never opened; every server started was stopped.

## 6. Gate

Run in the worktree at `033e3fe1` with `TMPDIR=<worktree>/fixtures-local/tmp` after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` (the review and screenshots were committed after):

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | 8679 passed, 0 failed, 0 skipped (6 min 05 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | 94 passed, 8585 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date · clean · 44 files, 238 tests passed · built |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished, no warnings |
| `cargo test` (src-tauri, beyond the gate) | 26 passed |
| DB reference scripts | not run: no schema change |

## 7. Owner commands

```bash
# A first run exactly as a new learner sees it (nothing remembered, no LEARNLOOP_VAULT,
# and no vault under the checkout's fixtures-local/, which still wins for the owner):
cd apps/learnloop-tauri && HOME=/tmp/ll-first-run LEARNLOOP_CONFIG_DIR=/tmp/ll-first-run/.config/learnloop npm run dev
#   -> creates /tmp/ll-first-run/LearnLoop and opens on the Library's welcome.
# Your own vault, as before:
LEARNLOOP_VAULT=$PWD/fixtures-local/<copy> npm run dev
# Kill switches, per library (learnloop.toml):
#   [ingest] auto_build = false                  # Add only makes the source readable
#   [ingest] auto_apply_passing_builds = false   # automatic builds wait as proposals
#   [ingest.cost_pause] threshold_usd / daily_cap_usd / prices.<profile>
uv run learnloop config effective --vault ~/LearnLoop
# The tests for this stage:
uv run pytest tests/test_ux_phase1_*.py tests/test_mobile_allowlist.py
cd apps/learnloop-tauri && npx vitest run src/copy src/components src/screens/reader src/app/useGlobalAdd.test.tsx src/screens/ReaderScreen.preparing.test.tsx src/screens/ReaderScreen.quickcheck.test.tsx
```

## 8. Open questions for the owner

- **Q-A.** When should "Questions ready for Ch. 1–2 · Undo" leave the card: after a few days, after the first answer in that chapter, or never (D5)?
- **Q-B.** Chapter-first extraction (D1): build it as Phase 1b on the re-anchor chain, or accept whole-book extraction with the original readable meanwhile?
- **Q-C.** Subjects (D2): is the deterministic provisional subject enough until an LLM filer exists for captures and books alike?
- **Q-D.** Undo (D4): is "dormant topics, inactive questions, inert ideas and skills" the right meaning, or should undo also retire skills and recipes (needs a revert path in `patches.py`)?
- **Q-E.** Money (D3): keep $5 per million tokens as the metered default and no daily cap, or set a daily cap so the 25% rule applies?
- **Q-F.** Consent travels to libraries created later on the same machine (mirrored with the AI defaults). Keep, or ask once per library?
- **Q-G.** `Ctrl+V` outside a text field adds a pasted link from any place. Keep it app-wide, or only on the Library?
- **Q-H.** `CLAUDE.md`'s line on the desktop's default vault is stale (§3 notes); update it.
- **Q-I.** In-flight merges (router R1, learner-text gaps, facet identity, Reader work) will conflict in `config/template.py`'s defaults snapshots (recompute at merge) and possibly in `ReaderScreen.tsx` (this branch touches only the preparing branch, the picker list, the enabled default and the quick-check timeout).

## Usability round 1

**Who and how.** Two scripted personas drove the real frontend and sidecar (branch at `67ece2c7f`) through the stage's headless harness, against a scripted fake AI built on the suite's fakes (`StructuredClientFake`, the house inventory/synthesis/append fakes, `ReviewFakeClient`; every learner-visible AI sentence starts with `[fake AI]`), with fresh scratch `HOME` and `LEARNLOOP_CONFIG_DIR`, no network and no real provider:
- **A**, a first-time grad student: empty `HOME`, "Continue with ChatGPT" through a simulated sign-in, then the honest no-AI path.
- **B**, a three-month user: a backup-API copy of the worktree's tracked linear-algebra library, Codex reading as ready.
- **C**, an optional third reviewer (Codex), who read both sessions and 27 screenshots and reacted in persona. C also qualified the findings, and the triage keeps those qualifications: the AI is fake, so nothing here says anything about grading quality; "tomorrow" was a same-day restart; and the timings include the harness's own pauses.

The sessions, screenshots and logs are in the stage's scratchpad (`usability/_personas_round1/{a,b}/`), not in the repository.

### Triage

De-duplicated across A, B and C, there are **5 blockers, 14 majors and 25 minors**.

What happens to them:
- **Fixed now:** all 5 blockers, 5 majors and 5 minors.
- **Deferred to a named later phase:** 9 majors and 11 minors.
- **Rejected with a reason:** 9 minors.

"Scope" means Phase 1's path: ingest, first run, the book cards, the preparing state, Connect AI, the cost pause, and the copy on that path. The first question is on that path too: the Phase 1 exit test is T1–T4, and §6.3 makes the section check the first question.

| # | Finding (who) | Severity | Decision |
|---|---|---|---|
| U1 | In a library with months of practice, every new book's questions were refused: "Bootstrap synthesis refused: subject '…' has locked identities". This hit both Add and "Build questions for the whole book", and Retry failed instantly (B; C) | blocker | **Fixed.** The lock check read every facet in the library, not the subject being built. |
| U2 | The original PDF didn't follow the learner. Contents didn't move it. Scrolling wasn't tracked, so no quick check ever came in the default view; one came only in "extracted text" (A, B, C) | blocker | **Fixed** |
| U3 | The Reader lost the learner's place: a tab switch, Library → Continue and a restart all opened the title page. Jumping to a section ticked every section before it as read (A, B, C) | blocker | **Fixed** |
| U4 | Today's reading step was "Continue Table of Contents · about 10 min", even after reading to §1.4 (A, C) | blocker (T4) | **Fixed** for the reading step. The rest of that moment ("Today complete · 0 min · 0 items" and a streak after two seconds) → Phase 3. |
| U7 | A scanned PDF was a dead end (T8). It showed "◐ Couldn't read this PDF" above "available in a minute or two". Details said "install marker-pdf". The scan's card had no text-recognition action, and Try again failed the same way (A, B, C) | blocker (T8) | **Fixed.** The OCR itself needs text recognition installed (`--extra pdf`), which this environment does not have. |
| U5 | The quick check couldn't be reached. "quick check →" at the section break did nothing, and the check was "waiting below" the whole Contents list (A, B, C) | major | **Fixed** |
| U6 | "compare with the source ↵" didn't send on Enter, and the learner's own answer vanished on compare, leaving nothing to compare. Ask had the same ↵ label with no shortcut at all (A, C) | major | **Fixed** |
| U8 | "Questions ready for … · Undo" sent the learner looking for questions while Today said "Nothing due", and Undo read as "undo the good thing" (A, C) | major | **Fixed** (copy). Practising a book's questions on demand is a Phase 3/4 flow. |
| U9 | Two Libraries. The Reader's "← library" went to its own list, which also offered "open demo chapter (fixture)" (A, B, C) | major | **Fixed** |
| U10 | Every new book's subject became the default in the Tutor-subject and Maintain dropdowns, and subjects showed as slugs (B; A) | major (trust) | **Fixed** |
| M-a | The feedback page speaks database: grader_tier, FSRS, Kalman, nats, "manual review recommended: unanchored_diagnosis_facet…", a 0.92 "conceptual_schema_error" beside "demonstrated ✓" (A, B, C) | major | Defer → **Phase 4** (4.2) |
| M-b | No "I think I was right". `r` regrades silently to the same score, **duplicates the rubric row** and moves the next-due time. The reply was "This is a ledger fact, not a request for your verdict", and "request review" was only "saved locally" (A, B, C) | major | Defer → **Phase 4** (4.2). The duplicated rubric row is a bug to fix there. |
| M-c | The learner can't say what they've learned. There is no Progress place, the well is a radar of `facet_…` labels, the graph is the table of contents in boxes, and Today showed "0 demonstrated" after a 4/4 (A, B, C) | major | Defer → **Phase 5** |
| M-d | Start on relaunch: "session warm-up", an epigraph typewriter (fake-AI text), "learning_objects", "+ create a new vault". Also "Today complete · 0 min" plus a streak, "0 demonstrated · 0 assumed · 4 untested", "41 retrieval reps" for 10 minutes, and "(why)" saying 21 minutes (A, B, C) | major | Defer → **Phase 3** (3.1, 3.3) |
| M-e | Ten tabs (Ingest, Proposals, Registry, Maintain). "Imports & builds" leads to a tab called Ingest, whose screen and errors are for developers ("learnloop[pdf]", "chatgpt_plan"). The build-plan modal's Escape steps back instead of closing (A, B, C) | major | Defer → **Phase 2** (2.1, 2.2) |
| M-f | The practice card header shows raw ids, "constructed_response" and "mastery estimate 0.50 ±0.43" before any answer (A) | major | Defer → **Phase 4** (4.1) |
| M-g | The extracted-text view is rough: hyphenation, page headers glued into paragraphs, mangled maths (A, C) | major | Defer → **Phase 1b / D1** (Marker, chapter-first extraction) and the Reader doc. U2 means the learner no longer has to use this view. |
| M-h | Proposals grows on every practice, with duplicate error-type proposals (B) | major | Defer → **Phase 2** (Under the hood). It is outside this path. |
| M-i | "○ no streak yet" and "SESSION 001" after months of use (B) | major (trust) | Defer → **Phase 3** (streak and footer). Not caused by Phase 1. It is likely the copied fixture's dates (C: "not proven"); verify in round 2. |
| m1 | The settings dot stayed red after "Connected to ChatGPT" (A) | minor | **Fixed**: the sheet refreshes the health on connect (it turned green after a restart) |
| m2 | "+ Add" wrapped onto two lines, and the library switcher was squeezed to "l." (A, B) | minor | **Fixed** (CSS). The crowded bar itself → Phase 2. |
| m3 | A paper is labelled "book" (A, B) | minor | Defer → **Phase 7** (needs a paper/notes detector) |
| m4 | A video still being fetched was titled with its raw URL (A) | minor | **Fixed** ("YouTube video", "arXiv 1706.03762", a host and path) |
| m5 | "Questions … in about 13 min" for an 11-page paper (A, B) | minor | Defer: calibrate the estimate from round 2's timings |
| m6 | "Subject: introduction-to-probability" in details (A) | minor | **Fixed** with U10 (titles) |
| m7 | A book added through the old Ingest route gets a file-name title, no status line and no automatic questions (B) | minor | Reject: Ingest is the deliberate path the spec keeps as it is (§6.4); "Build questions for the whole book" is in details |
| m8 | Notes & files opens previewing `vault.lock` (B) | minor | Defer → **Phase 2** (Under the hood → Files, Q18) |
| m9 | The one-time OK names ChatGPT while the status bar says "ai:codex_low" and Settings says the ChatGPT plan isn't signed in (B) | minor | Defer → **Phase 6**. Glossary §9 keeps "Codex" in Settings; Phase 6 names the provider the same way everywhere. |
| m10 | The Reader key bar: "capture box union", "sweep blocks" (A) | minor | Defer → Reader doc / **Phase 7** |
| m11 | Ask prints the question twice and shows a raw "answer_directly" tag (A) | minor | Defer → Reader doc |
| m12 | The no-AI self-grade box doesn't say "out of 4", and shows "fallback provider_auth_required" (A) | minor | Defer → **Phase 4** |
| m13 | "Optional, one line: what made this case fit?" under a question that isn't about a case; "(2/3)" numbering (A) | minor | Defer → **Phase 4** |
| m14 | Two identical "Explain Probability and counting" items (A) | minor | Reject: the fake AI's canned output |
| m15 | Adding a paper opened it at once when the learner wanted it on the shelf (A, C) | minor | Reject: spec §6.2 opens the first file. If it recurs, it becomes an owner question. |
| m16 | `Ctrl+V` outside a field adds a link, and nothing says so (A) | minor | Defer: already Q-G |
| m17 | Remove a failed link without a confirmation (A) | minor | Reject: nothing is lost, because the link never arrived |
| m18 | A React duplicate-key warning in the Graph key bar (B) | minor | Defer → **Phase 5** |
| m19 | No classic-shell switch (B) | minor | Reject: Phase 2's switch doesn't exist yet; the classic shell is still the shell |
| m20 | Axler's Continue opens at 1% (B) | minor | Reject: the copied fixture has no reading position for it. New reading is tracked now (U2, U3). |
| m21 | Small, dim text is tiring (C) | minor | Defer → **Phase 7** |
| m22 | "Couldn't reach the page" for the YouTube link and the arXiv id (A, B) | minor | Reject: the harness has no network; this is the designed line |
| m23 | "Connect an AI" shows again under `--ai none` (A) | minor | Reject: the harness artefact (`--ai none` removes the connection) |
| m24 | "My answer was right but got 2/4" (A, B) | minor | Reject as a grading claim: the fake AI's rubric counts words (C). The missing way to contest a grade is M-b. |
| m25 | In the paper, Abstract was ticked ✓ before a word was read (B) | minor | **Fixed** by U3 (ticks only for sections read through) |

### What changed

Python: `tests/test_ux_phase1_usability_round1.py`. Vitest: `screens/ReaderScreen.followsLearner.test.tsx` plus additions to `PreparingView.test.tsx` and `BookShelf.test.tsx`. Every test below failed before its fix.

- **U1. Locks are read per subject.** `identity_locks(…, subject_id=)` now honours the argument it already had: only the facets the subject's learning objects and items exercise. `_bootstrap_lock_refusal` passes the subject being built. Source-ingestion §8.2 says "legal only where nothing *touched* is identity-locked", and a new subject touches nothing in another. Apply still re-checks every entity it touches (`_accept_time_rechecks`), and a locked subject is still refused. Tests:
  - the per-subject read;
  - a second subject builds and applies beside a locked one;
  - the locked subject is still refused.

  Re-run in the harness: B's paper in the practised library went to "Questions for this book come up as you read" (`u1-06`).
- **U2. The original PDF follows the learner without block geometry.**
  - `reader.pdf_view` gains `pageSpans`: every passage's page, which a text-only (pypdf) extraction knows even though it has no boxes. This is additive.
  - In the Reader, a Contents click scrolls the original to the section's page.
  - The reading position comes from the page under the reading marker and how far down it the marker is (`pagePositionAt`, `spanOnPage`), so section progress moves smoothly through a one-page section.
  - A resume and the preparing hand-over land on the page.
  - The section check now triggers in the original, and the original has its own section-break offer, held at the foot of the reading area (U5).

  Re-run: Contents moved to Chapter 1 (`u1-01`). Scrolling through §1.1 wrote the check about 3 s after passing 60% of the section (`u1-02`).
- **U3. Places and ticks.**
  - Contents ticks a section only when it was read through or its check was done; a jump never ticks the sections it passes.
  - The Reader saves how far into each section the learner has read (`reader.mark_section_progress` `spans_seen`/`span_count`). The new `readerNoteReadingProgress` call gathers those writes for 1.5 s and sends them again when the Reader closes. The Reader reads them back on open, so the ticks survive a restart. *Round-2 Codex review (F3): a write that failed was counted as sent and never retried; a count is now settled only when the backend acknowledges it, a failed write is retried (three timed tries, then again on leaving the book or the Reader).*
  - Opening a book, a jump and a resume hold their position for a moment (1.5 s), so the first layout pass no longer overwrites a restored place. Before, that pass overwrote the saved place with the top of the book.

  Re-run: after a restart, Library → Continue opened at §1.2 with only §1.1 ticked (`u1-04`).
- **U4. Today's reading step.**
  - The step is never front or back matter while a chapter is left. The heading pattern moved to `content/sources/front_matter.py`, shared with the automatic build's scope.
  - The step continues from the furthest section the learner has read into, not a section they skipped.
  - The Reader's progress reports also keep the questions one chapter ahead (`advance_reading_build`); before, only a reveal or a finished check did.

  Re-run: the computed target became "Sample spaces and Pebble World" (§1.2). The plan already composed that same day kept its old row (same-day restart).
- **U5. The quick check is reachable.**
  - "quick check →" opens the Guide, puts the check directly under the section card (above Contents), scrolls to it and starts it with the answer box focused.
  - Open checks always sit above Contents.
  - The rail line reads "A quick check on this section is ready, just below."
- **U6. Answer and keys.**
  - After compare, "YOUR ANSWER" stays above "INTENDED ANSWER — COMPARE, DON'T GRADE" (`u1-03`).
  - Enter stays a new line, because answers can need several. The buttons name the key that sends: "compare with the source · ctrl+↵", "record answer · ctrl+↵", "ask · ctrl+↵".
  - Ask and the boundary answer gain the `Ctrl+Enter` they advertised.
- **U7. Scans.**
  - An import that found no text layer says "This PDF is a scan · Read it with text recognition" when an extractor that recognises text is installed.
  - Otherwise it says "This PDF is a scan — LearnLoop can show its pages but can't read them yet", with no futile Try again and the reason in details.
  - "Some pages look scanned" without text recognition no longer sends the learner to a Settings page that can't install it.
  - `source_action text_recognition` on a book that never had text also builds its questions.
  - The preparing view tells a stopped book from a working one: no ◐, no "in a minute or two", the line's own action, and "You can look through the pages here. Highlights, notes, Ask and questions need its text." (`u1-05`).
- **U8. The done line** is "Questions for Ch. 1–2 come up as you read", with no action; Undo stays in details. It names every chapter built so far, not only the newest build.
- **U9.** The Reader's "← Library" (now a button) and the preparing view's go to Library → Books, and the open book stays remembered. The demo chapter shows only while the background service is down (spec §7.3).
- **U10.** The snapshot's `subjects` come practised-first (active items, then topics, then name), and the snapshot gains `subjectTitles`. The Tutor-subject and Maintain dropdowns show titles, and cards gain `subjectTitle`. Re-run: B's tutor subject stayed "vector spaces" after a new paper.
- **Minors fixed:**
  - m1: health refreshed on connect.
  - m2: `+ Add` doesn't wrap, and the switcher keeps 7ch.
  - m4: readable names for links being fetched.
  - m6: subject titles.
  - m25: covered by U3.

**Deviations this round adds:**
- **D12.** The done line differs from §6.3's "Questions ready for Ch. 1" (U8).
- **D13.** The daily plan's reading step now means "from where the learner left off" and skips front matter (U4). This is a workflow suggestion, not scoring or scheduling, so it gets no algorithm successor. A plan already composed keeps its row. *Corrected by the round-2 Codex review (F2): it changes what the plan's reading block serves; it is now a live change behind `plan.reading_from_furthest` (off restores DL1's selection), and whether it should also mint a successor tag at merge is open (`ux-phase1-round2-codex-review.md`).*
- **D14.** `snapshot.vault.subjects` changes order: it was alphabetical. `subjectTitles` and `reader.pdf_view.pageSpans` are additive.

No migration. No change under `src-tauri`.

### Before and after on the plan's measures

The "after" column is a scripted re-walk by the agent on the fixed branch, not a new persona. Its times include the harness's command latency and about a minute spent working out its scroll command.

| Measure (target) | Before (A, round 1) | After (re-walk) |
|---|---|---|
| TTFR, local PDF (≤ 10 s after the drop) | ≈ 5 s | ≈ 3.4 s to the Reader on the original |
| Required decisions before reading (0) | 0 | 0 |
| TTFP with AI (≤ 10 min) | ≈ 5 min 47 s. It came only after finding "extracted text →"; the default view never asked. | ≈ 2 min 20 s from launch, in the **original PDF**: Contents → §1.1 → scroll → section-break offer → answer |
| Moderator questions, T1–T3 (≤ 1) | 2: "Why doesn't Contents take me there?" and "Where's the quick check?" | Both are answered by the UI now (U2, U5). Not re-measured with a fresh person. |
| T3 for an existing library (questions for a new source) | ✗: "locked identities" | ✓: the paper's questions built and applied |
| T4 next day (plan started with ↵) | ◐: the plan was "read the Table of Contents" | The reading step continues at §1.2. Phase 3 still owns "Today complete" and the streak. |
| T8 scan (OCR started from the card) | ✗: "install marker-pdf" | An honest line with no false promise. OCR starts from the card when text recognition is installed (tested with it faked as installed). This environment has none, so T8's target needs `--extra pdf`. |
| Internal words asked about (0), SEQ T1/T2 (≥ 6), unaided T1–T5 (5/5) | many; 6 and 2; 2½/5 | Needs round 2 with a persona. The words left are on Phase 2–5 screens (M-a to M-f). |

### Gate (this round)

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock … uv run pytest -n auto -q -p no:cacheprovider` | 8734 passed, 0 failed (6 min 12 s). An earlier run made while vitest ran alongside failed 2 timing tests (`test_the_deadline_shuts_a_stalled_stream`, a 250 ms bench limit); both pass alone, and the rerun on its own was clean. |
| `flock … uv run pytest -m durability -n auto -q -p no:cacheprovider` | 94 passed |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | installed · clean · 46 files, 264 tests passed · built |
| `cargo check` | not run: `src-tauri` unchanged |

The harness instances were stopped, and their ports are free. No key or credential file was read. No real AI or network was used. The owner's working vaults were not opened. Instance b's library is a backup-API copy of the worktree's tracked fixture, which is unchanged in `git status`.

### Open questions for the owner (round 1)

- **Q-J.** The done line. Is "Questions for Ch. 1–2 come up as you read" (D12) right, or should the card offer "Practise these" once a section's questions exist (a Phase 3/4 flow)?
- **Q-K.** The reading step (D13). Is "continue from the furthest section read" right for a learner who jumps around, or should skipped sections come back first?
- **Q-L.** Text recognition on a desktop install. Should the app offer to set up marker-pdf, or the hosted Marker runtime, from the scan's card? Today it can only say it isn't installed.

## Usability round 2 fixes

**The re-test.** After the round-1 revisions (`037de53f`), one agent ran both personas again through the same harness, with the same fake AI, scratch `HOME` and no network:
- A: a first-time user with an empty `HOME`, then `--ai none`.
- B: a fresh backup-API copy of the worktree's linear-algebra library, with Codex ready.

All five round-1 blockers held. The first answered question came at 2 min 55 s from launch, against 5 min 47 s in round 1. Two new error banners sat on A's path, and two round-1 problems remained. The re-test's notes and screenshots are in the stage's scratchpad (`usability/retest.md` and `usability/_round2_retest/{a,b}/`), not in the repository.

### Triage

Every finding below was on Phase 1's path, and every one is **fixed**, each with a test that failed first. Items R5–R9 were found by this round's own harness re-walk of the fixed build, or by checking its own fixes (see "Re-walk" below). Nothing is deferred from this round's list. The findings that later phases carry, from both rounds, are now recorded in the spec (§10, "Deferred from Phase 1's usability rounds").

| # | Finding | Severity | Fix | Test |
|---|---|---|---|---|
| R1 | A red "query is disabled" banner appeared after Today → "more new material" with no failed call, and stayed on every tab until restart | major (new) | The cause: Today's batch poll refreshed the full list when a background batch finished, but the plan view turns that read off, and refetching a turned-off cached query rejected with "query is disabled", which Today showed as an error. A turned-off query now resolves on refetch (with whatever is cached) and never fetches; being off is a state, not an error. | `useCachedQuery.test.tsx`; `TodayScreen.plan.test.tsx` R1 |
| R2 | Today's own "begin ↵" bounced to Start with "Begin today's plan on Start first.", and the banner stayed over the Reader and Today after the plan began | major | Today's begin starts today's plan itself, as Start's does: a session for the plan's minutes, then its first step. A pick from the full list with no session begins the plan with that pick. Session-first notices clear once a session begins (`app/notices.ts`). | `TodayScreen.plan.test.tsx` R2; `notices.test.ts` |
| R3 | A long-used book (Axler) opened at Chapter 1, 0%, while Contents ticked sections into 1C | major | With no saved place, the Reader reopens where the reading history leaves off, by the rule Today's reading step uses: the first unread passage of the furthest section read into, or the next section once it is finished. A saved place still wins. | `readingPosition.test.ts` (`resumeSpanFromHistory`); `ReaderScreen.followsLearner.test.tsx` R3 ×3 |
| R4 | "Read it again with text recognition" was offered on every readable book and ended in "Something went wrong. Try again." | minor–major | Cards carry `textRecognitionAvailable`, and details offer the action only when it is true. The backend's sentence reaches the screen (`text_recognition_unavailable` is shown in its own words) and says how to get text recognition. | `test_r4_*`; `BookShelf.test.tsx`; `ingestErrors.test.ts` |
| m-a | Scan details ended with the raw "install marker-pdf for OCR support" | minor | The details say how, plainly: "To add it, run uv sync --extra pdf in LearnLoop's folder, then restart LearnLoop." The extractor's own message is no longer appended. The Add box's message says the same. | `test_scan_details_*`, `test_adding_with_text_recognition_*` |
| m-b | An 11-page paper was a "book", with "in about 13 min" for a build that took seconds | minor | A short PDF (60 pages or fewer) whose first units include an Abstract is a "paper". A first build says "Writing questions for Ch. 1–2" with no number. Later builds are estimated from this library's own finished builds, at the median seconds per section in scope ("in about 2 min", "in under a minute"). | `test_a_pdf_with_an_abstract_is_a_paper`, `test_a_first_build_*`, `test_a_later_build_*`, `test_the_estimate_scales_*` |
| m-c | The one-time OK named ChatGPT to a Codex user | minor | A Codex library's OK reads "LearnLoop is set up to use Codex (your ChatGPT account)." | `test_the_one_time_ok_names_codex_*`; deny-list test (named exemption) |
| m-d | A book added through Ingest got its file name as its title, and its card had no line at all | minor | The Ingest import takes a PDF's own title, as Add does. A book that no study map covers says "No questions for this book yet · Build them", and the action plans its first build. A book in a study map stays quiet. | `test_a_pdf_imported_through_ingest_*`, `test_a_book_with_no_questions_*`, `test_a_book_already_in_a_study_map_*` |
| m-e | The Reader tab opened on its own second library list | minor | With no book open, the Reader shows the Library's own shelf (spec K5, `LibraryPlace booksOnly`), with search across every book kept above it. | `ReaderScreen.followsLearner.test.tsx` K5 |
| m-f | The library button was truncated ("Le…", "li…") and "[Alt+S]" was clipped | minor | Tabs give back padding on narrower windows, the switcher keeps 12ch, and the settings chip never shrinks; its key hint steps aside below 1300px. | `styles/navBar.test.ts` |
| m-g | Ask printed the question twice and a raw "answer_directly" tag | minor | The question is shown once (in full, with its maths, when open), and the answer style is in words ("answer directly"). | `ReaderScreen.followsLearner.test.tsx` |
| m-h | With no AI, cards still said questions "come up as you read" | minor | The line carries a no-AI version, which the shelf shows while no AI can write questions: "Questions for Ch. 1–2 come up as you read once an AI is connected · Connect". | `test_the_as_you_read_line_*`; `BookShelf.test.tsx` |
| m-i | A quick check was written for a paper's Introduction before anything was read | minor | Reading is the learner moving the page (wheel, keys, touch, the scrollbar). Until they do, after an open, a resume or a jump, no check is written, no section is counted as read, and the guide does not say "near the section break". | `ReaderScreen.followsLearner.test.tsx`, `ReaderScreen.quickcheck.test.tsx` |
| m-j | After comparing, the guide still said the check was "ready, just below" | minor | Once answered: "You answered this section's quick check: compare below, then keep reading." The Guide tab and Contents stop counting the check as waiting (R7). | `ReaderScreen.followsLearner.test.tsx` |
| m-k | An unexplained "?" after a finished section's ✓ | minor | Contents says "quick check" in words, and only while the check is still to do. | `ReaderScreen.followsLearner.test.tsx` |
| m-l | A visible "opening…" list on the way to reading | minor | The preparing view (the original PDF) stays on screen through the hand-over until the full Reader is ready. Opening a book otherwise names it ("◐ Opening …") instead of showing a list of books. The hand-over never lands on a later page while earlier pages are unmeasured (R8). | `ReaderScreen.followsLearner.test.tsx`; `readingPosition.test.ts` |
| R5 | Re-walk: with a 630-page book, every library read took 6–8 s. It is polled every 3 s while a book is prepared, so the sidecar stalled (13–24 s per call). | major (found here; from round 1's U8) | The card's chapter phrase reads the extraction's unit tree, not the full outline, which loaded the book's text once per unit. 6.1 s → 0.07 s. | `test_a_built_books_line_reads_its_text_at_most_once` |
| R6 | Re-walk: a book with block geometry (Axler) restored its place in the header, but the PDF stayed on the chapter title | major (found here) | A passage with boxes is reached through the pane's own wait for layout (`scrollToPage`), then centred. *The round-2 Codex review (F4) found only the page-top scroll survived a cold resume; the pane now keeps the passage until its page is drawn (`PdfReaderPane.scroll.test.tsx`).* | `ReaderScreen.followsLearner.test.tsx` R3 geometry |
| R7 | Re-walk: the Guide tab still said "1 quick check ready" after the learner compared | minor | An answered check is not counted as waiting. | (with m-j) |
| R8 | Re-walk: one textbook hand-over landed on the Contents page instead of the title page | minor | Not reproduced in two later drops. The hand-over's reading position is unknown while a page before the top is not laid out yet, so a later page can no longer stand in for it. | `readingPosition.test.ts` |
| R9 | Self-check of m-i's fix: a video's position moves by playback, not scrolling, so the reading gate would have silenced its quick checks | regression guard | Playback that moves past the cue a video resumed at counts as reading. | `ReaderScreen.followsLearner.test.tsx` (video) |

### Deviations this round adds

- **D15.** The build estimate is measured, not predicted: it is the median seconds per section of this library's last five finished automatic builds, applied to the new build's sections. A first build has no number. (Spec §6.3 shows "in about 5 min".)
- **D16.** A book that came in another way and that no study map covers gets a line and an action, "No questions for this book yet · Build them" (the action plans the ordinary first build). Round 1's m7 rejected this; the re-test asked for it again, so it is fixed here. *Round-2 Codex review (F6): "covers" means a finished build whose questions were applied; filing the book in a collection, a failed build or one turned down counts for nothing, and a finished build still waiting for a look says "Questions for this book need a look · Review".*
- **D17.** "Reading" means the learner's own input moved the page, or, for a video, that playback moved on. A resume, a jump, a hand-over or a re-layout no longer count as reading toward ticks or quick checks. *Round-2 Codex review (F5): a seek in a paused video counted; now only playing on counts (a seek sets the cue playback starts from).*
- **D18.** A book's kind ("paper") comes from a cheap heuristic on its first units and page count. Phase 7's detector can replace it.
- **D19.** A Codex library names Codex on the one-time OK and in that line's details, as Settings does. The deny-list test allows "codex" there through a named exemption; everywhere else it stays denied.
- **D20.** The empty Reader shows the shelf and keeps "search all sources" above it (K5 says only "the same shelf").
- `get_source_library` cards gain `textRecognitionAvailable`, and a status line may carry `withoutAi`. Both are additive.

No migration. No change under `src-tauri`. No scoring, scheduling or projection change, so no algorithm successor. *(Round-2 Codex review, F2: round 1's U4 changed what the plan's reading block serves; see D13.)*

### Re-walk (the author, on the fixed build)

In the same harness, with fresh instances: A with the fake AI and then `--ai none`, and B on a fresh copy. The screenshots are `docs/ux/screenshots/phase1/u2-*`.

**Persona A**
- Drop the textbook: the original PDF showed within about 1 s, and the full Reader followed at about 4 s, on the title page, with no list in between.
- Contents → §1.1, then two scrolls: the section-break offer appeared. "quick check →", answer, ctrl+↵: "You answered this section's quick check…", and the tab dropped its "1 ready". done for now: "✓ Why study probability?" with no marker.
- Today → keep going → **begin ↵**: the plan started and the Reader opened at §1.2 with no banner (`u2-01`).
- After the second check, Back to today's plan → **more new material**, then a 16 s wait through two batch polls: no banner, and `errors` was clean. add them → begin → the practice item.
- The paper: no check was written on its first page (`u2-06`), and its card read "paper".
- The scan: the details said how to get text recognition, plainly. No readable book offered "Read it again with text recognition".
- `--ai none`: both built books read "… come up as you read once an AI is connected · Connect" (`u2-05`).
- Measured on A's first build: chapter 1 had 10 sections and took 22 s, chapter 2 had 12 and took 19 s, and the paper's whole-source build had about 30 sections and took 48 s. The per-chapter estimate (before D15's fix) had said "about 4 min" for the paper; per section it is about 1 min.

**Persona B**
- The header showed "linear-algebra" in full, and "[Alt+S]".
- Axler → Continue opened at Section 1C, "1.36 definition: sum of subspaces", 72% (`u2-03`). The first attempt, before R6's fix, showed the right place in the header but not in the PDF.
- Ingest → browse… → import: the card was titled "Introduction to Probability (Chapters 1-2)" and read "No questions for this book yet · Build them" (`u2-04`).
- Build them → "Questions wait for your OK · Review" → "LearnLoop is set up to use Codex (your ChatGPT account)." → OK → "◐ Writing questions for Probability and counting" → "… come up as you read" 26 s later. Its details had no text-recognition offer.

Not re-walked: Ask (asking needs a drag selection on the PDF; the test covers the fix), and T5/T6 (Phases 5 and 4).

### Gate (this round)

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`. The Python lanes ran at `e93d9730`; the last commit changes only the Reader (TypeScript), its tests and this file, and the frontend steps ran on it.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install puts it back) |
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | 8750 passed, 0 failed, 0 skipped (6 min 12 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | 94 passed, 8656 deselected (serial, 1 min 40 s); also 94 passed with `-n auto` |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date (281 packages) · clean · 51 files, 318 tests passed · built |
| `cargo check` | not run: nothing under `src-tauri` changed since `67ece2c7f` |
| DB reference scripts | not run: no schema change |

### Codex review scope

The review that follows covers everything since `67ece2c7f`: round 1's revision commit `037de53f`, which no reviewer has seen yet, and this round's `1de7f1f6`, `8cbd71da`, `70f163cd`, `e93d9730` and the commit that adds this section (the video guard, R9).

### Safety

- No paid call, no real provider and no network. The harness sidecar ran in a network namespace with the scripted fake AI.
- No key or credential file was read.
- The owner's working vaults in the main checkout were never opened.
- For inspection, a backup-API copy of the worktree's tracked `fixtures/linear_algebra` was made under the worktree's gitignored `fixtures-local/la-round2`, and a copy of the harness library was made in the scratchpad. Both were read only.
- `git status fixtures/` is clean. Every harness instance was stopped, and its ports are free.

### Open questions for the owner (round 2)

- **Q-M.** The estimate (D15): is "measured from this library's own builds, no number on the first" right, or should a first build show a conservative range?
- **Q-N.** Reading (D17): should keyboard and scrollbar reading count, as now, or only the wheel and touch? And should a resume at a section's end offer its check again without any reading this visit (today it does not)?
- **Q-O.** "run uv sync --extra pdf in LearnLoop's folder": keep the developer-install command in the learner's details, or say "ask whoever installed LearnLoop to add its PDF tools" until Q-L (an in-app install) exists?
- **Q-P.** Naming (D19): is "Codex (your ChatGPT account)" the name Phase 6 should use everywhere for that route?
- **Q-Q.** Books added through Ingest (D16): offer "Build them" (as now), or build automatically as Add does?
