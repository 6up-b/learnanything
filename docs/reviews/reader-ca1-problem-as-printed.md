# Reader CA1: the problem as printed (stage `reader-ca1-problem-as-printed`)

Branch `reader/ca1-problem-as-printed` (worktree `learnanything-dl2`), base `main`
at `0db8291c1` (migration head 220, latest algorithm mvp-0.31). Spec:
`docs/specs/ux_reader_compare_ask_v1.md` §8 (all), §9 X13 and X14 (the two
as-printed rows), §11 K15, §1 C10, §12.4, §13's CA1 row and kill switch, §15
Q10 and Q12 (owner decisions 2026-10-25). Behaviour rules it leans on: the
workbench spec's §5.4 (the source visible = one hint-equivalent; "Original
page" behaves like any other source opening during practice) and D46/G61
(DL2: nothing that locates a check on your own until feedback).

**No migration, no successor, no model call, no exposure semantics changed.**

## 1. What was built

| Surface | Before Submit (not a check on your own) | During a check on your own | After feedback |
|---|---|---|---|
| Practice screen (answer box) | header `From Strang: Exercise 6.1.12 · p.297 · … · original page ↗ · counts as a hint`; `▸ as printed (Strang p.297)` under the stem | `From Strang` only (DL2); `▸ the figure, as printed` when the item was imported with a figure block, open from the start, figure only | — (the screen moves to feedback) |
| Work in Steps on the practice screen | `▸ as printed` under the stem (the practice card's); **no original page** (this screen has no book: UX §5.1 "hidden while the book is hidden") | as the practice screen | — |
| Reader workbench | `▸ as printed` under the stem (item view when bound, the multi-block crop of the session's anchors before binding); `original page ↗` in the header only while the book is shown, opening the page in the book pane (it never costs more than the book already does) | the item view applies the cold rule | — |
| Feedback (both layouts) | — | — | `Exercise 6.1.12 · Strang p.297 · original page ↗` (free, unlabelled) and `▸ as printed`; `▸ your photo` for a photo card |
| Compare methods (RW2c) | — | — | `▸ the solution as printed` under the book's solution, when it came from a page |
| Reader exercise candidates (RW4b) | `▸ as printed` beside `open in the book ↗` | — | — |
| Phone | nothing (D20; CA7 is the owner's) | nothing | nothing |

Backend (`src/learnloop/reader/as_printed.py`, `src/learnloop_sidecar/handlers/as_printed.py`):

- **`practice.as_printed`** `{practiceItemId, render?}`: the server decides what may show.
  It reads DL2's served check itself (`intent.checks.served_check`, `locators_hidden`), so
  a check on your own gets `kind: "figure"` (figure blocks only; each crop is
  `{index, image}`: no page, label, box or span id) or `kind: "none"`, whatever the
  client asks. An error reading the check fails closed (treated as cold). Without
  `render` the view is the header's locator and labels (no images, one cheap read on
  serve); `render: true` adds the crop PNGs.
- **The crop (C10)**: `crop_boxes` joins the problem's own blocks, in reading order,
  page by page, into the union of their boxes, and joins two consecutive blocks only
  while the union holds no other block's **centre**. A worked example, a solution or
  another exercise sitting between two of the problem's blocks therefore splits the
  crop rather than showing in it (so a page may give two crops). Structural rule, no
  padding, no tolerance constant. A block with no page or box crops nothing (listed in
  `skipped_span_ids`); a crop that cannot be made is `no_original`, **never** the
  whole page (unlike the single-block form's `page_fallback`).
- **`reader.block_original_region`** gains the multi-block form `{extractionId,
  spanIds}` (one of `spanId`/`spanIds`, validated); the single-block form is unchanged.
- **Page label**: the PDF's own page label (`/PageLabels`, pypdfium2
  `get_page_label`) when the file has one, else the page's one-based position in the
  file.
- **A variant is not the book's problem**: `relation = "variant_of"` shows nothing
  (the parent's print would be another problem, with its neighbours).
- **Your photo**: `capture.photo_for_practice_item` is the reverse lookup the spec asks
  for (§12.4) over `capture_routes.result_refs_json` (routes `make_card` /
  `photo_to_item`, `$.practice_item_id`; an image capture not purged, no deletion
  pending; the latest). No index: the capture inbox is small and the read is one
  query per serve of a non-canonical item. The UI shows it through the existing
  `get_capture_media` (resolved from the stored hash only). Hidden during a check on
  your own.
- **The transcription doesn't match the page** (`practice.report_transcription`
  `{practiceItemId, note?}`): a maintenance notice, type `transcription_mismatch`
  (aging `auto_resolution`, severity `action_needed`), one per item: each report adds
  the learner's text (trimmed, when any) and counts; a report on a dismissed/resolved
  notice opens it again; the feed's collector keeps it while the item's prompt hash is
  the one reported and resolves it once the wording changes (a reword, a re-import or
  the item gone). It records nothing else: no evidence, no retirement, no item change.
  Only for a verbatim import (`validation_error` otherwise).
- **Kill switch** `practice.as_printed.enabled` (default true): off, `practice.as_printed`
  answers `{enabled: false, kind: "none", reason: "disabled"}`, the report refuses
  (`disabled`) and every screen is as before (no control renders).

## 2. Q12: the original page before Submit, and why it is not a successor

The spec's stop rule: "if that changes an attempt's classification beyond existing
hints_used/reveal meaning, stop and treat it as a successor". It does not:

- Opening the original page before Submit sets the practice screen's **book
  component**, the one the answer box already sends for a book counted in steps
  (`bookCounted`), so the submit carries `hintsUsed = authored + 1` and
  `bookCounted: true`: exactly spec §5.4's "source visible → `hints_used` += 1",
  the existing meaning (assisted: FSRS-fed, certifying nothing). The server's
  `combine_held` already treats `client_book` as one component, so the page and a
  book counted in steps are one hint-equivalent, never two. Going into steps it is
  carried as `carriedBook` (the workbench's existing `source_shown_at`).
- It is timed (the first-hint marker is marked when it is the attempt's first help)
  and kept with the draft as `pageSeen` under the retry key (the `hintSeen`
  pattern: `save_practice_draft.page_seen`, `checkpoint_dto.pageSeen`, the App
  mirror), so a restart before Submit still counts it.
- The view records the exposure where it opens (`get_span_view`, context
  `provenance`, entity `practice_item`), as every source opening does. No new
  exposure context (the column's CHECK would need a migration), no new reveal kind.
- It is not offered where a hint would void or is barred: a diagnostic block, a
  cold follow-up (`cold_retry`, `certification_cold_probe`), a check on your own
  (D46), teach-back, and in steps on the practice screen. *As printed* (the
  problem's own blocks) stays free there: it shows only the stem the learner has.
- After Submit (feedback) it is free and unlabelled.

## 3. Tests (fakes only; the crop on a PDF made in the test, no book text committed)

`tests/test_reader_ca1_as_printed.py` (20): the split rule and its union; blocks with
no geometry; the crops cut from a real two-page PDF drawn with PIL hold only the
problem's own ink (no neighbour, no caption pixels) at the reader's scale; no
original → geometry kept, no image; the practice view's locator, original page and
outline spans, and no exposure written; the cold rule (figure only, no locator keys)
with a stub and with a real DL2 due check (`cold_now` over `make_intent_vault`); a
check with no figure shows nothing; an unreadable check fails closed; a variant
shows nothing; no print, no photo; the switch off; your photo (and its media), cold
and purged; the report (count, notes, reopen, resolve on reword, verbatim only);
the multi-block RPC and its one-form validation; the draft's `pageSeen` under its
retry key.

Vitest: `src/screens/PracticeScreen.asPrinted.test.tsx` (9: the header and the
original page counting once, both layouts, Esc staying in the page, the exposure
call, the draft flag and the submit's `hintsUsed: 1, bookCounted: true`; as printed
free; a restored `pageSeen`; the cold check's figure only, both layouts; no page on a
cold follow-up; the switch off; the page carried into steps as `carriedBook`, and no
page in steps); `src/components/AsPrinted.test.tsx` (7: pending then "the page image
isn't available", the remembered open state and zoom, the report with its text, your
photo with its date, the multi-block crop, after-feedback locator, nothing when the
server shows nothing or the call is absent); `src/app/practiceDraft.test.ts` (+1).

## 4. Gate

(filled in at the end of the stage; see §6)

## 5. Open questions / follow-ups

1. **"this question is wrong" does not exist in the code.** The spec says the existing
   practice `⋯` *this question is wrong* gains a first option; neither the card's
   controls nor any RPC has it. CA1 puts *the transcription doesn't match the page*
   under the crop (wireframe X13's line) and records it as a maintenance notice. If
   the owner wants it in `⋯` too, it is one more entry point to the same RPC.
2. **Page labels.** A PDF without `/PageLabels` shows the page's position in the file
   (`p.N`, one-based), which may differ from the printed number. No page-label data
   exists elsewhere.
3. **Region selections' sub-box** (§12.4, third bullet: a learner-drawn crop stored on
   the imported exercise) is not done: today's imports keep span ids only, so a
   region-selected exercise shows its whole blocks.
4. **"open in the Reader ↗" from the original page view** (§8.3) is not added;
   `OpenInSource` has no Reader-open callback today.
5. **The page's hint is counted by the client's book component** (with the draft
   flag), not re-derived on the server from the exposure row. The row is there to audit
   it; a server-side fold would be a change to the submit path's assistance count,
   which this stage avoided.
6. The image drop-in path is still only specced; *your photo* covers the capture-inbox
   card route.
