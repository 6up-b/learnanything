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
