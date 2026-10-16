# UX Phase 4: practice and feedback

**Stage:** `ux-phase4-feedback`, branch `ux/phase4-feedback` (worktree `learnanything-merge4`), base `37a2a7e5f` (main, mvp-0.25, migrations to 204).
**Spec:** `docs/specs/ux_learnloop_v1.md` §7.4, §7.5 and §10 Phase 4 (items 4.1–4.4), plus the findings Phase 1's usability rounds deferred to Phase 4 (§10 "Deferred", `docs/reviews/ux-phase1.md` M-a, M-b, M-f, m12, m13).
**Owner direction (2026-10-15):** build Phase 4 as the spec scopes it. Frictionless by default, glass box on demand, no jargon: feedback leads with one verdict, what was right and ONE next step, and everything technical goes behind *details*. "I think I was right" uses the existing dispute path. A live change behind a kill switch, with no algorithm successor.

## 1. The switch, and why there is no successor

`[ui] practice_feedback = "simple" | "classic"` (new `UiConfig`, default `"simple"`). `"classic"` restores the Phase 4 screens as they were: the practice card, the inspector, feedback, the short check's results, the repair overlay and the session-finish HUD. Two sidecar changes reach classic too (Codex review): one rubric row per criterion after a regrade (M-b's duplicate gone), and the m13 prompt copy (D11). The sidecar sends it in the app snapshot (`config.ui.practiceFeedback`); the desktop reads it through `app/practiceFeedback.ts` (`simplePracticeFeedback()`).

The switch is read only by the display: no grading, scheduling, evidence, projection or replay path reads it, and a test pins `context.py` as the only Python reader of `config.ui`. What the simple screens show is not display only, though (Codex review F1): the full answer they show is an exposure, so it is recorded in the existing reveal ledger. That ledger is read only at write time, and replay keeps the recorded `primed` and admissibility. A routine display counts within the cold retrieval delay (one day): a retry while the answer is fresh is primed, and an unaided answer is not independent. See `docs/reviews/ux-phase4-feedback-codex-review.md`. Under the owner's ruling (serving and display changes that replay never reads go live behind a kill switch), there is **no algorithm successor**. The 17 defaults snapshots in `config/template.py` were recomputed only because the effective config gains the section, the same as Phase 1. A change takes effect on the next vault load: a restart, or the shell's file watcher on `learnloop.toml`.

The sidecar additions are all reads, or bookkeeping the learner starts:
- **Feedback bundle:** `held_for_review` (THE held predicate, `learnloop.held_grades`), the learner's own answer and volunteered line apart (`learner_answer_md`, `learner_explanation_md`, via a new `trace_evidence.learner_answer_part`, the inverse of `compose_learner_trace`), and `answered_presentation` (the question as given: a method-explicit answer's frozen statement and rendered instruction, None otherwise). After the Codex reviews it also sends what the grade stands on: `answered_source` (`contract`, exact; `live`, only in the response of a regrade that has just run; or `unrecorded`), `answered_expected_answer`, `answered_criteria` and `answered_max_points`, and each side's own maximum in the regrade history (round 3 F9, `docs/reviews/ux-phase4-feedback-codex-review.md` §9.3). Nothing is inferred from which versions of the item were served. A due cold check that a routine display covers is deferred wherever it is served (a plan block, a pick, a session open, the TUI's open) until that coverage ends, by itself, within a day and an hour; other reveal kinds keep main's serving. A read (feedback, the inspector, a sibling preview) never opens a cold administration. No probe or placement presentation is committed or served for an item a routine display covers, whoever writes it (the scheduler's slate too). A refused probe offer changes nothing (rounds 5 to 7, review §12 and §13). Such a hold never finishes the daily plan. When the hold is the only thing between the plan and more work (nothing else fits now, and the held item would fit the plan's minutes, item allowance and lanes once its hold lifts later the same day), the plan waits and says so ("Nothing to do right now. Back in 4 min: a question on …"). It offers no Begin and starts no session meanwhile, then serves the item once the hold lifts. Otherwise the plan closes with the chooser's decision, as before (rounds 7 and 8).
- **One rubric row per criterion:** `_latest_evidence_per_criterion` displays the latest epoch's row (M-b's duplicated row after a regrade). The ledger is untouched.
- **"I think I was right":** `trigger_regrade` takes an optional `learner_reason` and a client `contest_id`. The reason is recorded first, as a `grade_contest` ledger-fact claim with the learner's response (presented, then answered) on the presentation-only claim ledger. That is the same store the regrade card's "request review" wrote to. Then the existing regrade runs. The grader never sees the reason. A contest the regrade does not uphold enters the existing grade-review queue (`learnloop grading reviews`, cleared by `adjudicate`; Codex review F3). Without a reason, the plain regrade runs exactly as before.
- **Released short-check feedback:** each entry says `heldForReview` (`mark_released_held`).
- **Session end:** `topics` lists the session's topics in the well's words. `on_your_own` means one of the topic's own unassisted answers raised a facet the session demonstrated (the session diff's `demonstrated_attempt_ids`). A facet another topic's answer raised does not count (Codex review F4: the first build checked the session-wide facets and credited a held or missed answer on a shared facet). `with_help` means a hinted, primed or walkthrough answer that earned points and is not held. A topic only tried, missed, skipped or held is not named.
- **Copy (m13):** the optional line's applicability prompt now reads "Optional, one line: what told you this idea applies here?" instead of "…what made this case fit?". Display copy only: the grader reads the learner's line, never the prompt. This is the one change not behind the switch (D11).

## 2. What was built

| Commit | What |
|---|---|
| `0ffcdcde6` | Fail-first sidecar tests (`tests/test_ux_phase4_feedback.py`). 13 of the first 14 failed against the base sidecar; the 14th is a guard (a plain regrade records no contest). The three tests added this session (the question as given, the m13 prompt) failed before their code. |
| `ba3b4b9bc` | Sidecar: the switch, the bundle fields, the contest, released held marks, session topics, the prompt copy. |
| `39bff905f` | Fail-first vitest: one file per screen plus `copy/denyList.phase4.test.tsx` and `app/practiceFeedback.test.ts`. 37 failed against the base desktop; the classic tests passed, as they should. |
| `bb022fb4d` | Desktop: every screen below. |
| `4475283b4` | Fixes from the harness walk (§5), each pinned by a test. |
| `ae06ee39f` | A trap found in review: a second `^↵` on the plain self-grade would have sent an untouched all-zero grade. The test failed without the fix. |
| `27f18525b` | References: `Config - ui.md`, the `ui` section's function in `db_generate_reference.py`, and the leaf counts (857 → 858); provenance elsewhere. |
| `0be2f7bd8` | The gate's first full-suite run found one older test, `test_conjunctive_instruments.py::test_schema_interpretation_gets_the_applicability_prompt`, still asserting "fit" in the applicability prompt (m13's rewording). It now pins "applies here" and that the prompt isn't the decision-point one. |

### 4.1 Practice card (`screens/PracticeScreen.tsx`, `components/InspectorOverlay.tsx`)

**Surface:**
- **Header:** the topic title and `⋯` (the card controls: easier, harder, reword, retire, teach it, I know this).
- **Removed from the surface (now in details):** the item ULID, the mode pill (`constructed_response`), "\<provider\> grading" or "self-grade required", the mastery estimate, the character/word count and the source paths.
- **Question:** `ItemPresentation` unchanged, so a method-explicit question keeps its rendered instruction (`required_method_instruction`; vitest pins it).
- **Buttons:** Submit, then Hint, I'm stuck, Ask and Skip, each keeping its key.
- **A check on your own:** "On your own · no hints on this one", and no Hint button (D6). Ask stays.
- **A short check:** one line, "Feedback comes when this short check ends · hints are off for now · why? ▸", plus *Teach me instead*.
- **A guided redo:** "Redo the part you missed", what to fix, and "Your work so far, kept". No failed-step ids, no "Demonstrated credit".
- **Primed practice:** "◌ with help".
- **States:** loading is "Loading the question…" (no "Verifying diagnostic safeguards…"). An unavailable question reads "This question isn't available any more · Next question · Try again". A submission needing recovery reads "Your answer is saved. LearnLoop is finishing the grading · Try again", with the attempt id under details.
- **Plain self-grade (no AI, m12):** Submit freezes the whole trace (the answer and the optional line) in the session checkpoint before any full answer shows, and locks both, across navigation and restarts (Codex review F1). The key then shows only while a display row written for the pending draft covers it, so every other production is judged against it at once; only the commit of exactly the frozen trace is exempt (its retry key and trace hash, carried by each row as a versioned JSON identity and compared field by field; a field named twice, or a version that is not the integer 2, exempts nothing; round 3 F1, rounds 4 to 6 F1-2). The learner's answer shows beside a full answer (not during a short check, whose contract withholds the answer). Then *Got it · Partly · Missed*. *Partly* asks "Which parts did you get?" (one tick per criterion, then Done). The per-criterion numbers live under *grade it in detail ▸*, each saying "(out of N)". There is no "fallback provider_auth_required" and no outage banner. A second `^↵` never submits an untouched grade.
- **Inspector:** never shows the expected answer or the rubric of a question the learner hasn't answered, meaning one never answered (a skip is no answer) or the one open on the practice screen now (App passes `answeringItemId`). The section says "The answer and how it's graded show here once you've answered this question."

### 4.2 Feedback (`screens/FeedbackScreen.tsx`, new `screens/feedback/FeedbackSurface.tsx`, `components/DiagnosisCard.tsx`)

**Surface (W5b):**
- **Header:** "← Today's plan / Today / Back to the book" and the topic.
- **Verdict:** in words (*Right · Partly right · Not yet*, or *Held for review* with one sentence and never a score), then "◇ graded by AI · I think I was right ▸" or "graded by you".
- **Quiet honesty lines:** practice with help, and the check-on-your-own result in plain words.
- **The question as it was given,** then "› You wrote" beside "◇ A full answer": the key the grade stands on. When nothing recorded says which version of the question the grade read, one plain line says so ("The version of this question it was graded against wasn't kept."), there are no criteria lines, and the panel shows "The answer as the question reads now" with "It may not be the one this was graded against." (round 3 F9). The answer shows only while a committed reveal-ledger row covers it: one is written before it appears and renewed while it is in use, and an unattended screen hides it ("Hidden while you were away. Show it ▸"; Codex review F1, round 3 F1). Every signal that may precede a suspend or a loss of attention (hidden, pagehide, freeze, blur, and every shell window resize, scale or focus change, before the window's state is asked) and a clock discontinuity hide it at once, until a fresh row is acknowledged (rounds 4 and 5). In the shell, only the answer to the latest question about the window's state may bring it back: every such signal asks again, a reply to an earlier question is ignored, and a new answer shown while the window is held asks again too (round 6).
- **The criteria as ✓ / ◐ / ✗ lines,** with "· not judged" for a route that never exercised a criterion.
- **One sentence on what went wrong:** the diagnosis summary when it lands, a matched mix-up's correction, or the grader's note. It updates in place, with no "analyzing your pattern…" banner. Behind it, *why? ▸*: possible causes, what you already showed, how it happens, "You've made this mistake before" with dates and quotes, and the single "this doesn't sound right".
- **One next step besides Next,** the one the system recommends: *Fix this mix-up · about 4 min*, else *Redo the part you missed*, else *Try a similar one (t)*. None after a right answer.
- **A Next button,** plus *details ▸* (`.`).
- **Next returns to where the attempt started:** an attempt from a Reader check goes back to its passage (App passes `origin` and routes Next there). The plan and the queue behave as before.

"I think I was right" (or `r`) opens a one-line box ("Why? One line, optional") with *Look again*. The regrade happens in place and one line says what came of it: "Looked at it again: now Right." or "…still Partly right. Your note is kept." When the grader can't run: "Your note is kept. The grader can't look again right now." That line, and every "Your note is kept", shows only once the sidecar confirms the record (Codex review F7). A failed or unknown delivery says "Your note couldn't be sent. Try again.", keeps the box and the reason, and a retry of the same reason reuses the contest key. An edited reason, or a contest opened again after *never mind*, is a new contest under a new key; the sidecar refuses a key sent with another reason (`contest_key_conflict`, Codex re-review F10). It is never a red error. It isn't offered on a self-grade or a right answer.

**Details** (curated, not the classic page):
- the score in numbers, out of the maximum the grade stands on, or the points alone when the graded version is unrecorded and no maximum was recorded with the grade (round 3 F9); an unrecorded grade lists only what it recorded, each criterion id with its points, under "What this grade recorded" (round 4 F9); who graded it and how sure the grader was (a held grade: "Held for review: the grader's score doesn't count until this answer is reviewed", with no number anywhere, and after a regrade released it, "Looked at again: Held for review → Right", never the held score; Codex review F6);
- the full check-on-your-own and with-help notes;
- what the grader looked for (rubric rows with points);
- errors that cap the grade;
- the regrade history in words, each side out of its own grade's maximum ("Looked at again: 2 / 4 → 6 / 8."; final verification F9);
- the clarification card (the surface says "This grade may change after one question ▸");
- one question, unaided;
- why it went wrong (the causal panel, the one-tap cause question, the diagnosis card fed by the screen's single poll, via the new `useDiagnosisCard` hook);
- the source panel;
- tutor questions counted as hints;
- the card controls and keep-a-copy;
- *open in inspector*.

Gone from the simple screen: the attempt-ULID breadcrumb, `grader_tier`, the FSRS rating, the interval factor and retrievability target, the belief-update chart, surprise in nats, the follow-up gate card and need ids, error-attribution severity, the duplicated criterion trace, ClaimSurface's ledger and misconception cards ("This is a ledger fact…"), and the red "manual review recommended" banner (M-a, M-b). `⇧D` and `a` still work as keys, off the key bar.

### 4.3 Short-check results and repair (`screens/DiagnosticReviewScreen.tsx`, `components/ProbeBlockResult.tsx`, `screens/RepairScreen.tsx`)

**Short check:**
- **Surface:** "That's the short check done. Here's what it showed.", then the topic and one verdict per question ("Question 2 · Partly right", with the grader's note). A held grade reads "Held for review".
- **One next step on ↵:** *Fix this mix-up · about 4 min* when a released answer carries a shared fix, else the route's step (*Learn it with the tutor · A few more questions · Back to practice*). Esc leaves.
- **Details:** `ProbeBlockResult` in its plain variant. "question N", no raw status, no route slug, no "Feedback withheld… released now", and "held for review" in place of a held score. `DialogueProbe` keeps the classic result.

**Repair as one timed step:**
- **Title:** "Fix this mix-up · about 4 min" (D10).
- **Compare the two ideas:** "Some answers were consistent with this mix-up: …" and "The distinction to use here: …", plus "This came back after it was fixed before." when it relapsed.
- **↵ *Read both passages*:** "The idea to use" / "What it gets mixed up with", each with *see it in the book ▸*.
- **↵ *Try one now*:** primes the related question and opens it at once (classic needed four clicks). With none: "There's no question to try for this one yet."
- **Details:** the mechanism, state, dated history and whether a check on your own was planned. "Reading is recorded as exposure, not proof", "Demonstrated credit" and "not measurable" are gone.

### 4.4 Session finish (`components/SessionFinishHud.tsx`)

A dismissible card, not a modal: "26 minutes · 9 questions", then "Since last time: ● Conditional probability (on your own) · ◌ Mixtures (with help)", then "3 days in a row" and *Done ↵* (Enter or Escape; typing elsewhere is left alone). It never counts what did not move. The fake telemetry is gone:
- registration codes, `LL//RUNNER`, `LOG #`, `K-12`, `RLA`;
- the 0→100% meter, sonar pings and satellites;
- the attempts, items and follow-ups grid;
- facets and predictions counts.

`"classic"` keeps the HUD exactly (`ClassicSessionFinishHud`).

### Shared

- `app/practiceFeedback.ts`: the switch, the verdict words, `FIX_MIX_UP_LABEL`, the origin labels, and `expectedAnswerText` for structured keys.
- `components/PlainParts.tsx`: `DetailsToggle`, the one primary and quiet actions, the voice panel.
- `.plain-action` styles in `styles/app.css`.
- `copy/denyList.phase4.test.tsx` renders all five surfaces against the §9 deny-list, including the stuck prompt, the Partly checklist, the contest box and *why?*.

## 3. Deviations

| # | Spec says | Built | Why |
|---|---|---|---|
| D1 | The inspector *never* shows an unanswered item's answer. | The rule follows the kill switch: `"classic"` shows it, as before. | The owner asked for "classic" to restore the screens exactly; the inspector is under the hood. Open question Q1. |
| D2 | Session end: *Next time: finish §5.4.* | Not shown. | `end_session` carries no next reading step; adding the plan's read there is daily-plan territory. Q3. |
| D3 | *see it in the book (§2.2) ▸* on the practice card and feedback. | Provenance stays in details (the source panel). The repair step's passages open in the book. | Opening the Reader at a passage from feedback is the Reader doc's RW6b; the parallel Reader stage owns those screens. |
| D4 | *Explain it* (teach-back) as one of the next steps. | It stays under the card controls ("teach it"), in details and under `⋯`. | Minting a teach-back is CardControls' own flow. The surface keeps one step. |
| D5 | The grading wait: "Reading your answer — usually about N s" from measured latency, and "The grader is slow right now · Keep waiting · Grade it yourself". | "Reading your answer…". | No measured latency reaches the practice screen yet. Q6. |
| D6 | On a check on your own, Hint and Ask stay visible, and using one says "This becomes practice with help". | Hint is not offered (`^h` says why). Ask stays. | `apply_attempt` rejects a hinted cold retry outright: it would not become practice with help, and the answer would be lost. |
| D7 | Exam mode header. | Not touched. | ExamScreen isn't a Phase 4 file. |
| D8 | `⋯` holds the card controls, with *Not for me* replacing *retire* and the 11 reasons in details. | `⋯` holds CardControls unchanged. | Renaming retire and its reasons is a CardControls change used by four screens. |
| D9 | "Feedback after the next 2 questions." | "Feedback comes when this short check ends." | Under value-of-information stopping (mvp-0.21) the count isn't known in advance. |
| D10 | *Fix this mix-up · about 4 min*. | A fixed planning label: about a minute to compare and read, plus one question at the daily plan's fallback estimate (3 min). | No per-learner repair duration exists yet. Q4. |
| D11 | Every change behind the switch. | The m13 prompt copy is not. | It is backend display copy with no structure to restore; "classic" shows the new wording. |
| D12 | — | The session finish names a topic ● when a "Partly right" answer earned certification credit (seen in the walk). | The sidecar reuses the session diff's "facets demonstrated", the model's own measure. Q5. |
| D13 | *with help* ◌ on feedback. | Labelled for primed and auto-primed attempts. A hinted attempt isn't labelled on feedback. | The bundle carries no hint count (only tutor-question equivalents). |
| D14 | "I think I was right" uses the existing dispute/adjudication path. | The claim ledger (where the regrade card's "request review" already wrote), then the existing regrade; a contest the regrade does not uphold enters the existing grade-review queue (Codex review F3). | The grade-review intake (`review_flag` heads, `learnloop grading reviews` / `adjudicate`) is the existing path for grades; the diagnosis adjudication queue covers diagnoses only. |

## 4. Before and after, counted from the code

| Workflow | Before (base `37a2a7e5f`) | After (simple) | Friction left |
|---|---|---|---|
| **Answer a question** | Header of 5 machine items (ULID, LO link, mode slug, subject, "codex grading") plus a mastery estimate with ±; Hint, Ask and Skip keyboard-only; card controls and source paths always shown. | Topic and `⋯`; Hint, I'm stuck, Ask and Skip as buttons; receipts under details. 0 glossary terms (deny-list test). | The optional confidence row and the optional one-line *why* still sit under the box; "don't know" (pre-mvp-0.13 libraries) is still key-only. |
| **Grade it yourself (no AI)** | "AI grading is unavailable", N numeric inputs with no reference answer and no "out of", a confidence select, notes; 2 clicks plus N entries. | The locked answer beside a full answer; 1 click (Got it, Missed), or Partly plus ticks plus Done. | Fatal errors and error attributions need *grade it in detail*. |
| **Read feedback** | About 14 sections; no question, answer or full answer; Next keyboard-only; the red "manual review recommended"; 4 to 5 diagnosis verdict widgets. | One verdict, the question, both answers, ✓/✗ lines, one sentence, one step, Next. Everything else is 1 click (*details*). | The causal panel inside details keeps its terminal voice ("claim checked", "causal_p2_v1"). |
| **Contest a grade** | `r` regraded silently (same score, duplicated row). "Request review" on a "ledger fact" card was saved locally. | 2 actions (I think I was right, Look again), the reason kept, the result said in place; an unsettled contest goes to the owner's grade review. | The review queue is the CLI's (`learnloop grading reviews`); no desktop screen lists it. |
| **Short-check results** | Raw status, a route slug, "Feedback withheld… released now", score pills per "observation N", Esc to continue. | One line, a verdict per question, one step on ↵. | — |
| **Fix a mix-up** | 4 clicks from the card (*repair this → · show me the sources · prime a related item · practice this ▸*), plus measurement copy. | *Fix this mix-up · about 4 min* opens the step; 2 × ↵ to the question. | The causal hold panel (when the cause is undecided) keeps its own copy. |
| **Finish a session** | A full-screen HUD capturing every key, a 2.4 s fake meter, telemetry, 5 counts and up to 3 count lines. | One card: minutes · questions, what moved in ● / ◌, the streak; Done. | — |

## 5. Real UI look (usability harness, fake AI)

The stage's own copy of the persona harness (scratchpad `phase4/usability/`): ports 1471/1472, its own chrome tmp, and the command mapping regenerated from this worktree's `commands.rs` (349 commands). The original `usability/` was being used by another stage. Instance **b** ran a backup-API copy (`learnloop.db.copies`) of the worktree's tracked `fixtures/linear_algebra`, with the scripted fake AI (Codex reading ready) and once with `--ai none`. For the repair step, one misconception was seeded into that scratch copy with `Repository.insert_misconception`. The sidecar ran with no network. **No paid call; no real provider; the owner's working vaults were never opened.** The instance was stopped at the end.

Screenshots: `docs/ux/screenshots/phase4/`.
- **01:** the restored open question. Topic, `⋯`, the question, the box, and Submit · Ask · Skip as inline buttons. The key bar drops `^h` when the question has no hints.
- **02:** the card's details: question id, mode, "graded by AI", "likely to recall now 0.70 ±0.28", counts.
- **03:** the inspector opened from that id while answering: "The answer and how it's graded show here once you've answered this question." (the item had a graded attempt 80 days earlier).
- **04:** an 8-word answer, graded by the fake grader. *Partly right*, "◇ graded by AI · I think I was right ▸", the question, both answers side by side, one ◐ criterion line, *Next ↵* and *Try a similar one (t)*, *details ▸*.
- **05:** details. 2 / 4, "how sure the grader was 0.90", what the grader looked for, why it went wrong (the causal panel), the card controls, *open in inspector*.
- **06:** *why? ▸* with "Possible causes" and "this doesn't sound right". It recorded `contest_causal_diagnosis` and then said "Noted. Thanks."
- **07–08:** `r` opens the one-line box; *Look again* ran the fake regrade (2.5 s): "Looked at it again: still Partly right. Your note is kept."
- **09–11 (no AI):** a hint shown plainly; Submit locked the answer and showed it beside a full answer with *Got it · Partly · Missed*; Partly listed the two criteria as ticks; Done gave *Partly right · graded by you*, with ✓ and ✗ lines.
- **12–13:** *Fix this mix-up · about 4 min*: compare, then ↵ read both passages, then ↵ *Try one now* opened the primed related question.
- **14:** the session finish card over Start: "5 minutes · 1 question · Since last time: ● What Makes a Vector Space? (on your own)".
- **15:** `[ui] practice_feedback = "classic"` in the copy's `learnloop.toml`, after a restart: the classic card exactly (ULID, mode pill, "codex_low grading", the mastery estimate, the THIS CARD row, counts).

What the walk found, each fixed with a test (`4475283b4`):
1. The plain buttons used the queue's full-width grid row ("Subm / it" in a narrow column). They now use inline `.plain-action` buttons.
2. The repair step named facet slugs, cut short ("…to each o"). It now uses the case's own statement as an evidence relation.
3. Passage headings were raw block addresses ("/page/14/SectionHeader/0 › …"). They are now left out.
4. No *why?* when the grader wrote no sentence but the causes were known. It is now offered.
5. "I think I was right" was offered on a right answer. It no longer is.
6. "this doesn't sound right" vanished after use. It now stays as "Noted. Thanks."
7. A primed retry said nothing about help. It is now labelled "◌ with help".

Not reached in the real UI: the short check's results. The probe episodes this library can start need a session of more than 20 minutes and the probe queue was empty. That screen is covered by vitest (5 tests and the deny-list).

Also seen, and pre-existing: a primed retry reopened after a reload is no longer primed (the checkpoint doesn't carry it), and the Today and Start screens around Phase 4 still speak the old language (Phases 2 and 3).

## 6. Gate

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp` after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 11846 passed, 0 failed (13 min 24 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 11740 deselected |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | typecheck clean; vitest 92 files, 655 passed; build succeeds (the usual chunk-size warning) |
| `cargo check` | not run: nothing under `src-tauri` changed (`trigger_regrade` is a passthrough) |
| DB/config references | regenerated; `db_validate_reference.py` on the final tree: 0 errors |
| `tests/test_coordinated_migrations.py` | in the full suite (no migration in this stage) |

The first full-suite run (after the restart, on `27f18525b`) gave 1 failed, 11845 passed: the older test pinning m13's old wording, fixed in `0be2f7bd8`. The counts above are from the run on the final tree.

## 7. Owner commands

```bash
# Phase 4 is on by default. Per library, learnloop.toml:
#   [ui]
#   practice_feedback = "classic"   # the screens exactly as before Phase 4
uv run learnloop config effective --vault <library>
# The tests for this stage:
uv run pytest tests/test_ux_phase4_feedback.py
cd apps/learnloop-tauri && npx vitest run src/screens/*.phase4.test.tsx src/components/*.phase4.test.tsx src/copy/denyList.phase4.test.tsx src/app/practiceFeedback.test.ts
```

## 8. Open questions for the owner (defaults applied)

- **Q1.** Should the inspector's unanswered-item rule hold even under `"classic"`? *Default applied: it follows the switch.*
- **Q2.** Settled by the Codex review (F3): a contest the regrade does not uphold now enters the existing grade-review queue. Open: should a desktop screen list that queue? *Default: the CLI only.*
- **Q3.** Add "Next time: finish §N" to the session finish (the plan's next reading step in `end_session`)? *Default: omitted.*
- **Q4.** The repair step's "about 4 min": keep the fixed planning label, or estimate it from the learner's own durations? *Default: fixed.*
- **Q5.** Should the session finish name a topic ● on any certification credit (as now), or only after a fully right answer? *Default: the model's own measure.*
- **Q6.** Build the grading wait with measured latency and the "Grade it yourself" fallback as a follow-up? *Default: deferred.*
- **Q7.** Merges: `config/template.py`'s 17 snapshots conflict with any branch that adds config (recompute at merge). `FeedbackScreen.tsx` and `PracticeScreen.tsx` will meet the parallel diagnosis-provenance landing if it touches feedback.
