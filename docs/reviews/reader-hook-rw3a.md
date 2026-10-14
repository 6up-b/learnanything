# Reader hooks and RW3a: the Reader's orchestration in hooks, then margin cues from the Guide

**Branch:** `reader/rw3a` (worktree `learnanything-merge4`, base main `4cf54a295`, mvp-0.22; not rebased, the orchestrator merges). Owner-queued, 2026-10-13: the rest of the Reader workbench, starting with its first slice. Specs: `docs/specs/spec_reader_workbench_v1.md` §6 (RW3), §12, §14 (G13, G14, G16, G30); `docs/specs/ux_reader_workbench_v1.md` §3.4, §3.5, §4.4, §7, §10 S7/S8.

**A continuation.** The first run of this step was killed when the orchestrating session crashed. It had committed the hook extraction and the RW3a backend (fail-first tests, then the implementation) and left the RW3a frontend uncommitted with regenerated references. This run read the committed work and the uncommitted diff, kept both, discarded only the generated references (regenerated at the end), fixed one typecheck error in a test, added two things (below: Alt chords, the check-me offer helper), committed the frontend fail-first tests separately and checked that they fail on the pre-RW3a frontend, then committed the implementation.

| Part | What | Commits |
|---|---|---|
| 1 | Hook extraction, no behaviour change: `useReaderVisit`, `useReadingProgress`, `useReaderInquiry`, the YouTube watch panel in its own module; hook parity tests | `e44180974` |
| 2a | RW3a backend: fail-first tests, then `reader/reader_cues.py`, the guide plan's `cues`, three RPCs, `[cues]` config, the report's cue funnel | `0a184dba3` (tests), `6a6f6d4a3` |
| 2b | RW3a frontend: fail-first tests, then the marks, popover, footer, Settings, check me through the shell | `ea6eebb9d` (tests), `a933e83ce` |
| — | DB and configuration references regenerated | `d85f143d6` |

**Paid calls:** none ($0.00). Every model call in the tests is a house fake. No real provider, no network, no key read, no vault opened (no manual run was needed: RW3a has no route and no model call).

**Migration:** none. **Schema:** unchanged (head 201, 319 table notes). **Config:** a new `[cues]` section, four leaves: `enabled = true` (the kill switch), `density = "normal"` (`off | fewer | normal | more` = 0/1/2/4 marks per section), `one_per_viewport = true`, `off_sources = []`. Modelled defaults, left out of the decision-only template. All fourteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries were recomputed (`defaults_fingerprint_for_version`), because the effective config gains the section. **Algorithm version:** unchanged, no successor. RW3a is display only (spec §6.5, §12): nothing it writes enters evidence, mastery, projections, FSRS, the plan or serving, and replay reads none of it. **`src-tauri`:** three passthroughs (`reader_cue_action`, `reader_cue_preferences`, `reader_set_cue_preferences`), so `cargo check` ran. **Mobile:** desktop only (spec D20). `tests/test_mobile_allowlist.py` pins the three RPCs, and `reader.guide_plan`, as off the phone.

## Part 1: the hook extraction (no behaviour change)

`ReaderScreen.tsx` went from 4,503 lines to 2,311 at `e44180974`; RW3a's wiring brings it to 2,398. The orchestration moved into focused hooks under `apps/learnloop-tauri/src/screens/reader/`:

| Hook / module | Lines | Owns |
|---|---|---|
| `useReaderVisit.ts` | 138 | The funnel's visit id, `touchVisit`, back-to-reading, usable results, proactive counts (each element once per visit) |
| `useReadingProgress.ts` | 978 | Reading position (saved place, search hit, reading history), section progress and its saves, placement versus the learner's own scroll, **the check offers through `checkOffer.ts`**, the producer trigger, and (RW3a) the passage the learner was restored to |
| `useReaderInquiry.ts` | 1,061 | Ask, branches, the return stack and detour strip, reconnect, inquiry status, the passage quick check |
| `YouTubeWatchPanel.tsx` | 540 | The video and its synchronized transcript (a move) |
| `useReaderCues.ts` (RW3a) | 341 | Which marks are drawn, impressions, Alt+↓/↑, the popover's actions |

**`checkOffer.ts` remains the only place that decides a check offer.** Only `useReadingProgress` (section offers) and `useReaderInquiry` (the passage check) import it. The parity test wraps `checkOffer` in a pass-through spy and asserts that the offered set equals the rule's verdict for every section, called with each section's own inputs.

**Existing tests are unchanged.** `e44180974` edits no existing test file: the 11 `ReaderScreen.*.test.tsx` files and the 16 test files under `screens/reader/` pass as they were on `main`. `readerHooks.parity.test.tsx` (now 10 tests) pins each hook's public behaviour without the screen around it:
- the one offer rule;
- a jump is a placement, the learner's own scroll is reading, and an offered check stays pinned;
- the saved place, a search hit and the history;
- leaving a book saves and resets;
- one visit per source, with each proactive element counted once;
- a follow-up is a branch detour, and walking back asks to reconnect;
- another source is a detour;
- with the switch off, no detour and no parent;
- added in this run: an arrow key is the learner's scroll but Alt+↓ is not, and the restored passage.

## Part 2: RW3a, margin cues from the Guide's own citations

### Backend (`src/learnloop/reader/reader_cues.py`, `handlers/reader.py`)

- **Where cues come from.** The guide plan's own `suggested_passages` with `learner_signal = 'recent_misunderstanding'` (`reader_guidance._passages_by_section`). The Guide already reads the diagnoser's overlay since `fix/guide-overlay`. For each passage, RW3a takes the same strongest overlaid error that the rail's reason names (`active_errors_by_learning_object_overlaid`: highest severity, then newest). Order and rank are the rail's order within each section. Ranking for spacing puts each section's first cue before any section's second, then reading order.
- **Never on held-out or exam material.** A section in `reader_guidance.held_out_sections`, or a span the `exam_material` predicate covers, never yields a cue. `find_cue` refuses a tap on one.
- **The learner's choices.** The density budget per section (from vault config). "Not relevant" withholds that (passage, target) until undone; a new error on the LO is a new target and so a new cue. A book switched off yields no marks.
- **Fixed templates (G16).** The note is "Connects to something you worked on: {LO title}." The "because" line is "Because: your answer on {2 Oct} · from the Guide's citations", or "Because: an answer you gave · from the Guide's citations" when the date is missing. The screen reader label is "Note on this paragraph: {note} {because}". The rail's "Revisit this to resolve: …" stays in the rail only.
- **`reader.guide_plan`** carries `cues` only when `cues.enabled`. Switched off, the plan is byte-identical to `main`'s (tested).
- **`reader.cue_action`** handles open, check me, not relevant and its undo.
  - It writes one salience-only `reader_action_invoked` event (`cue_opened`, `cue_check_me`, `cue_not_relevant`, `cue_not_relevant_undone`).
  - It appends a `learner_card` verdict on task `passage_cue` (`same`, `same`, `different`, `undone`), keyed by (extraction/span, error event) and superseding the previous verdict. A repeated verdict appends nothing.
  - "Not relevant, because…" text goes into the verdict's rationale as judge feedback. It never reaches the event and never becomes learner text for gaps.
  - **Check me** proposes one item on the cue's LO through `find_practice`, under the Reader's caller (`propose_practice` when the instructional service is on). The question the learner already answered and recently revealed families are excluded. Its result is `found | none | failed`.
- **`reader.cue_preferences` / `reader.set_cue_preferences`** read and change the density and per-book off in vault config (`apply_config_updates`, then a reload), logging `cue_density_changed`, `cue_source_off` or `cue_source_on` with where the change came from. No change means no write. Both refuse with `cues_disabled` when switched off.
- **The reader report** gains the cue funnel: marks shown, open, check-me and not-relevant rates against marks shown, marks per reading hour, and density and per-book choices. Marks also count in the proactive load. `cue_shown` joins the client activity vocabulary.

### Frontend

- **`screens/reader/cues.ts`** holds the restraint rules as pure functions:
  - `placeCueMarks` draws marks by rank, and skips a lower-ranked mark within one viewport height of a higher-ranked one when `one_per_viewport` is on. It never draws on the restored passage, and draws nothing while skimming or in the workbench's source pane.
  - `stepDown`, `stepMark`, and the PDF page model.
  - `CUE_COPY`, every fixed string a cue surface shows.
- **`useReaderCues.ts`**:
  - **When placement runs:** in a layout effect, only when the text's layout key, the marks, skim, the restored passage, the surface, the PDF page width or the window size change. Never on scroll, so nothing appears or disappears while reading.
  - **Impressions:** each mark shown is logged once per visit as `cue_shown` (`element: margin_mark`); since the Codex review (F6), once it is in view.
  - **Alt+↓ / Alt+↑** move focus between marks in reading order, starting from the reading position when no mark has focus. If the target's PDF page is not drawn yet, the Reader jumps there first and then focuses the mark.
  - **The popover's actions** each come with a receipt and an **undo until the learner leaves the source** (the receipt resets with the extraction).
- **`MarginMark.tsx`**:
  - **The mark:** a `◌┆` glyph drawn with CSS, with no text node (a selection or marquee never quotes it). It never animates, and LearnLoop never focuses it.
  - **Hover or focus** shows the note and the "because" line. **Enter** or a click opens the popover.
  - **The popover:**
    - *open · what you worked on* shows the date, the question, and LearnLoop's model's reading, in the model's voice (or "still reading" while the diagnosis is pending).
    - *check me · a short question on your own, with the book out of view*.
    - *not relevant…* opens an optional "why?" and says where it goes: "It isn't read for gaps in your understanding, and it never grades you."
    - *fewer marks like this*.
    - *marks off for this book* and *marks off everywhere*.
    - *close · esc*.
  - **Esc** closes it and returns focus to the mark.
- **The Guide's footer** (`CueFooter`) carries the density control (*margin marks: off · fewer · normal · more*, labelled "a display limit to protect your attention"), a "turn back on" for a book switched off, the receipt with *undo*, and a legend. Settings has the same density control (`ReaderCueSettings`). With the kill switch off, both are absent (W11: never a disabled control).
- **Surfaces:**
  - the text view's gutter;
  - the original PDF: an overlay gutter at the left of the passage's box, only for passages with a box;
  - a transcript's time column.
- **Check me through the shell** (`App.tsx`, `app/readerCheck.ts`):
  - **Plan on:** the item opens as a learner pick through DL1's `plan_learner_pick`, served by the pick's block, which records the proposal's delivery itself.
  - **Plan off:** the open serves it as an ordinary attempt and carries the proposal, so that serve records the delivery.
  - **With no session:** the check waits and opens when the session begins ("Start a session to take this check on your own — it will open automatically.").
  - **Where it opens:** on the practice screen, so the book is out of view. **Esc or b from its practice or feedback** returns to the passage in the Reader. Any other item goes back to the queue as before.
- **Alt chords are no longer scroll keys** (`useReadingProgress`). Alt+↓ / Alt+↑ never scroll natively, and a mark brought into view by focus is a placement, not reading. Before this fix, focusing a far mark credited the passages in between as read.

### Gates and where they are tested

| Gate | Backend (`tests/test_reader_cues.py`) | Frontend |
|---|---|---|
| **G13** display only, and the per-section budget and spacing | `test_cues_and_their_taps_write_no_evidence_mastery_fsrs_or_plan_row`; `test_the_plan_with_cues_off_is_byte_identical_and_the_rail_unchanged`; `test_no_section_shows_more_cues_than_the_density_budget` (off/fewer/normal/more); `test_cues_are_ranked_each_sections_first_before_any_second`; `test_check_me_proposes_one_item_on_the_cues_learning_object` (an ordinary learner pick) | `cues.test.ts` "G13 spacing" (2 tests); `ReaderScreen.marginMarks.test.tsx` "G13: at most one mark per screenful"; `readerCheck.test.ts` (learner pick with the plan on, an open carrying the proposal with it off) |
| **G14** skim, the restored line, never animated, Guide cues never held out | `test_the_default_is_normal_one_per_viewport_and_on` (spacing on by default). RW3a has no holdout path, so Guide cues are never held out by construction | `cues.test.ts` "G14" (restored line, skim and working, static CSS glyph); `ReaderScreen.marginMarks.test.tsx` "G14" (restored passage, skim mutes, never animates and never takes focus) |
| **G16** fixed template wording | `test_cue_copy_is_fixed_templates_that_never_judge_the_learner` | `cues.test.ts` "G16 lint" over every `CUE_COPY` string and every sentence-like literal in the cue components; `ReaderScreen.marginMarks.test.tsx` "G30 and G16" (note, "because" line, the rail's reason and the statement absent from the note) |
| **G30** the margin and the rail agree | `test_each_cue_is_one_of_the_rails_misunderstanding_passages_in_the_rails_order`; `test_a_split_cue_names_the_diagnosers_statement_as_the_rail_does` | `ReaderScreen.marginMarks.test.tsx` "G30 and G16" (every drawn mark is one of the rail's misunderstanding passages, beside its own passage) |
| **Actions** | `test_taps_are_salience_only_events_and_learner_card_verdicts`; `test_not_relevant_withholds_the_cue_until_the_learner_undoes_it`; `test_a_new_error_on_the_learning_object_is_a_new_cue`; `test_every_server_cue_event_is_salience_only`; `test_the_client_records_cue_impressions_and_cannot_forge_a_tap`; `test_cue_action_rpc_records_the_tap`; `test_check_me_never_offers_the_question_the_learner_answered`; `test_preferences_rpc_writes_vault_config_and_the_plan_follows`; `test_the_cue_rpcs_answer_cues_disabled_when_switched_off`; `test_step_down_walks_more_normal_fewer_off`; `test_the_report_counts_marks_shown_taps_and_choices_against_marks_shown` | `ReaderScreen.marginMarks.test.tsx`: Alt+↓/↑; Enter, open and Esc; not relevant with its why and undo; fewer with undo; off for the book and everywhere with undo; check me found, none, and absent without a shell; impressions once per visit; the kill switch; a transcript. `PdfReaderPane.marks.test.tsx`: the original's gutter. `readerCheck.test.ts`: the way back to the passage |
| **Held-out exclusion** | `test_a_held_out_section_never_carries_a_cue_though_the_rail_still_lists_it`; `test_exam_material_never_carries_a_cue`; `test_a_cue_on_held_out_material_cannot_be_tapped` | (the Reader draws only what the plan carries) |
| **Hook parity** | — | `readerHooks.parity.test.tsx` (10 tests); every existing `ReaderScreen.*` test unchanged |

**Fail-first evidence.**
- **Backend:** `tests/test_reader_cues.py` fails at collection on `4cf54a295` (no `reader_cues` module).
- **Frontend:** the pre-RW3a code was stashed and the five test files committed in `ea6eebb9d` were run against it:
  - `cues.test.ts` and `readerCheck.test.ts` fail at collection;
  - 17 tests fail: 14 of 15 in `ReaderScreen.marginMarks`, 1 of 2 in `PdfReaderPane.marks`, and 2 of 10 in the parity file (the restored passage and the Alt chord);
  - the passing cases are the switched-off case and "without marks the pages carry no gutter", both correct on the old code.
- **The Alt chord fix:** with only that fix reverted, the Alt test fails again.

## Decisions taken within the spec, and deviations

1. **Check me opens on the practice screen, not in the Reader's working posture.** The spec (§6.1, D40) and UX (S7) want the item in the Reader's working posture with the book hidden, which RW2a builds. Until then the practice screen gives the same two guarantees: the book is out of view, and Esc after feedback returns to the passage. RW2a should swap the destination and keep the learner-pick call (friction note 3).
2. **"Marks off everywhere" sets the density to off.** The spec says "off is 'cues off'". It is reversible from the Guide's footer and from Settings. The kill switch `cues.enabled` stays the owner's switch, not the learner's.
3. **The note's wording.** The spec's example ("Connects to a distinction you worked on: density vs cumulative probability. Not yet checked on your own since.") assumes a named distinction and a since-check that RW3a does not compute. RW3a's template names the Learning Object the Guide cites, and the diagnoser's statement (model text) stays behind *open*, in the model's voice. The note never claims "not yet checked", because RW3a reads no evidence to back it.
4. **Impressions are events, not a table.** RW3a has no table (spec §6.3). A mark shown is a `cue_shown` event once per visit (since the Codex review, F6: a mark in the learner's view, not a mark placed; `reader-hook-rw3a-codex-review.md`). A cue suppressed by spacing, the restored line or skim is not logged: `suppressed_reason` belongs to RW3b's `reader_cue_impressions`. The client computes the reason (`CuePlacement.suppressed`), so RW3b can send it.
5. **The original PDF's spacing uses a page model.** It assumes letter pages at the pane's width, not the drawn pages, so spacing never depends on which pages have been drawn yet. For A4 and similar pages the error is a few percent of a page. *Superseded by the Codex review (F5): landscape pages broke the rule; the spacing now reads each page's own size, loaded with the document and still independent of drawing.*
6. **No `●┆` marks yet.** UX U6 ("a week of only `◌` marks fails") is met by RW3b's "new application" kind. RW3a has the one kind, *revisit*.

## Friction notes for the next phases (RW6a, RW2a, RW1b, RW2b with adaptive hints)

1. **`ReaderScreen.tsx` is still 2,398 lines, mostly render tree.** The text column's block loop (the per-block chrome: guide passages, health badges, the margin mark, section breaks, the inline reconnect) and the two rails make up most of it. RW2a's working posture changes the layout (the source pane beside the workbench). Extract a `ReaderTextColumn` (block loop plus gutter) and a `ReaderRails` component before or as RW2a's first commit, so the posture switch is a layout change and not a 2,400-line diff.
2. **`useReaderInquiry` (1,061 lines) and `useReadingProgress` (978) are each still large.** RW1b (the intent box, next step, why step, reconstruct) lands in `useReaderInquiry`. Splitting reconnect and the passage quick check into their own hook first would keep RW1b's diff readable. `useReadingProgress` mixes position, section progress and offers. The offers part is small, because `checkOffer.ts` decides; the rest is position bookkeeping.
3. **RW2a must wire two RW3a seams.** `placeCueMarks({ working })` is passed `false` today; the rule and its test already exist (`cues.test.ts`), so RW2a passes `true` for the source pane while working. Check me's destination lives in `App.tsx` (`pickCheckMe`, `backFromPractice`) and `app/readerCheck.ts`. RW2a moves the open into the Reader's working posture, keeps `plan_learner_pick` and `readerCheckOffer` as they are, and can delete the practice-screen return.
4. **RW6a ("Last time here") can reuse the restored passage.** `useReadingProgress.restoredSpan` is the passage the Reader placed the learner at, from a resume, search hit, history or walk back. RW6a's card should not greet them with a judgement there either, so it can read the same value.
5. **A tap re-reads the whole guide plan.** `reader.cue_action` rebuilds the plan to find the cue (`find_cue`), and the Reader re-reads the plan after every tap or preference change (`reloadGuidePlan`, forced). That is cheap at RW3a's size. RW3b's discovered cues should come on their own RPC, resolved by link id, so a tap does not rebuild the plan.
6. **Late layout shifts are not re-spaced.** Placement runs when the text is laid out, never on scroll (by design). An image or a late KaTeX node that grows the column afterwards can leave two marks closer than a screenful until the next layout key or resize. That is acceptable for "nothing moves while reading", but RW5 (figures) adds tall content and should bump the layout key when a figure mounts.
7. **One lint, three copies.** The G16 lint exists as `BANNED` in `cues.test.ts` and as the backend test's word list (the inquiry components have their own). RW2b's hint ladder and RW6's recap add a lot of learner-facing copy. Move the word list into one shared test helper (frontend) and one fixture (backend) before RW2b.
8. **The keyboard map is spread out.** Alt+←/→ (return stack) and Alt+↓/↑ (marks) are window listeners in two hooks; bare Alt (clear capture) completes on keyup (`bareAlt.ts`). RW1b's next step and RW2b's ladder will add keys. A small `readerKeys` registry (the file exists for the palette) would show conflicts in one place.
9. **Settings shows only the density.** Books switched off are turned back on from that book's Guide footer. If the owner wants to see them from Settings, `reader.cue_preferences` already returns `offSourceCount`.

## Not done

- **No real-UI look.** The usability harness (`…/scratchpad/usability`) is wired to another worktree (`learnanything-ux-impl`) and may be in use by parallel stages. Showing a mark would also need a vault copy with a live misunderstanding on a cited passage. The screen-level vitest drives the real `ReaderScreen` (marks, popover, footer, keyboard) with jsdom layout stubs instead.

## Open questions for the owner

1. Is check me on the practice screen acceptable until RW2a's working posture lands (decision 1)?
2. Should "marks off everywhere" also be listable and undoable per book in Settings, or is the Guide footer's "turn back on" enough (friction note 9)?
3. The note names the Learning Object, not the distinction (decision 3). Is "Connects to something you worked on: *Densities*." plain enough, or should the note carry the diagnoser's statement (model text, so it would need the model voice in the note itself)?

## Gate

Run in the worktree with `TMPDIR` set to `fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,678 passed**, 0 failed, 0 skipped (48 warnings), 627 s; run against `d85f143d6` |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,579 deselected (1 warning), 104 s |
| `npm install`, `npm run typecheck` | ok, clean |
| `npm test` (vitest) | 80 files, 559 tests passed |
| `npm run frontend:build` | built (the usual chunk-size warning) |
| `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml` | finished |
| `db_generate_reference.py`, `db_validate_reference.py`, `validate_vault.py` | regenerated; errors []; passed, 1103 notes |
