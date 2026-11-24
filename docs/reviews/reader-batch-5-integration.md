# Reader workbench v2: batch 5 integration (2026-11-23)

One landing branch, `land/workbench-batch-5`, cut from main `684892aba5`, with three finished branches merged, a
critical review of the two written by Codex workers that could not run a browser, the desk harness or the visual
comparison (and whose working trees were committed unreviewed), the fixes that review found, and the proof.

## 1. What was merged, in order (one merge commit each)

| # | Branch (tip merged) | Merge | Conflicts and how they were resolved |
|---|---|---|---|
| 1 | `reader/ink-glm-ocr` (`3dd42552a5`: handwriting read by GLM-OCR, the vision route removed; `reader-rd8a.md` §13) | `4a28954eb6` | None |
| 2 | `reader/menu-protection-gaps` (`df348296bf`: `workbench_protection.py`, WB-DOCS-1 to WB-DOCS-5) | `d934ba6be0` | None |
| 3 | `reader/workbench-copy-fixes` (`a1c431d839`: learner-facing strings, COPY-1 to COPY-13) | `7de673becd` | `passage_union.py` keeps the protection code with the copy's clearer pad-line message; the pen's refusal lines keep GLM-OCR's reasons (the copy's were written for the removed vision route); the pad menu keeps its protection-aware header; Show me keeps the protection branch's block ids with the copy's toasts; the ledger keeps both sides |

`git grep -n -E '^(<<<<<<< |>>>>>>> )'` was empty before each merge commit. Generated vault notes were not
regenerated.

## 2. Review of the menu protection branch (brief A)

The idea holds: the menu's verdict gates every verb, every contributing passage and pad block is checked at the
destination on the server, kept job rows are rechecked at delivery, and a missing verdict fails closed. Two places
overshot, and one stale fixture hid its effect in the harness:

- **BATCH5-2, the legacy-quote rule.** "A source quote without an anchor can be inserted or reused only while the
  vault's protected set is empty" blocked, in any vault with exam material, the learner's own older unplaced quotes
  in insert, lift, Ask, Carry, Find, practice and Show me: realistic learner-visible harm with no protection gain for
  quotes from ordinary books. Narrowed: such a quote is refused only when a run of 8 of its words (all of it, when
  shorter) appears verbatim in a protected passage (`repeats_protected_text`, `check_placed_quote` in
  `workbench_protection.py`); an unreadable protected reading still refuses. Learner-typed text is never checked.
- **BATCH5-6, the verdict revoked by a stopped search.** A judged job that stopped (a model down, a budget spent,
  another vault opened) or a poll that could not reach it was treated as a failed protection read: on a plain passage
  the header went neutral and every quoting verb stopped silently. Now a stopped search shows its own Retry and the
  first answer's verdict stands; only a first answer that fails or carries no verdict fails closed, and a verb pressed
  while the verdict is unknown says how to go on.
- **BATCH5-10, captures on protected passages.** `check_selection` in `reader.capture` refused every capture of a
  protected selection, so a plain highlight or margin note on the learner's own exam material (classic Reader and
  desks) was refused where main stored it. A plain capture queues no model work: it is stored again, and the menu
  offers Note in margin on protected material without waiting for the verdict. What sends words on stays refused
  (a preset when its request is sent; Ask, Find, Compare, Show me, Make it practice, Teach me, Carry and Append at
  their destination). Each downstream reader of stored annotations was checked and already withholds a mark beside
  protected material: the union read (BATCH5-3), the promoted rows and passage details, the notes corpus behind
  `notes.search`, `notes.marks`, the workbench search's notes group and the teacher's notes, and pad proposals; the
  companion's context reads no stored annotation. Tests both ways in `tests/test_menu_protected_material.py`, with a
  control mark on an open passage that does reach those surfaces.
- **BATCH5-8, the harness fixture.** The fake finished promoted job carried no verdict, so in the harness every judged
  search failed closed and the promoted rows vanished from the source menu. The server sends the verdict; the fixture
  now does too.

Ordinary material: every verb (Append, Carry, Ask, Find, Compare, Show me, Make it practice, Teach me, Note in
margin), the pad menu and the notebook-frame menu behave as before on plain passages. The branch's own test changes
to plain-passage paths only add the span ids the server needs for its destination check (`openSearch`, Make it
practice, the capture's `spanIds`); no wait beyond the first verdict was added (the vitest menu and DeskShell suites
and the harness's menu runs).

## 3. Review of the copy branch (brief B)

**Goal names (BATCH5-4 = COPY-4).** The branch hid every goal's name on the client ("Goal 1 · set …", "Your goal",
"A topic still needs a match"). Fixed on the server through the goal lens's one protection: `Protection.mask_names`
replaces only a held topic's name (whole words, longest first) with "[topic hidden]"; `protect_goal` and
`protect_unmatched` apply it to the band's goal and unmatched rows inside `protect_band` (a masked phrase is marked
held and not offered to add). The desk's chooser reads a new desktop-only `goal.choices` (Rust passthrough, client,
DTO, fixture; pinned desktop-only in the mobile allowlist and the goal lens RPC list), masked the same way; until it
answers it names goals neutrally. The why card's "For <goal>:" and the path view show the masked words again.

**COPY-2 (BATCH5-3).** `passage.union_range` now applies the menu's withholding to stored quotes, authored
questions, links and the other word-bearing rows (one helper, `_withhold_rows`, for both reads); the word origins
come from the union's placer.

**COPY-3 (BATCH5-5).** Every chapter delivery (list, decide, a suggestion's result) masks a chapter over protected
spans with current protection: times and ids kept, title and tags neutral.

**Nouns and glyphs.** Grep over the branch's diff: no glyph's count changed except one added `↵` in a key title.
"Scratchpad" stays in the pad title (the branch only dropped the selection quote from it). The owner's "cold check"
had been replaced in the held-material wording and elsewhere ("Details are hidden while a question is due",
"Topic details hidden", "Follow-up question scheduled", "Based on your answers and LearnLoop's estimates"); restored
(BATCH5-7).

**Strings read for sense (BATCH5-1, BATCH5-7, BATCH5-9).** Put back or made true: alt+; inserts a video time ("Copy"
was wrong); a later section is needed only at a deeper level and a skippable one is not needed for the goal (the copy
inverted both: "Included at a deeper level", "Optional at this depth"); unmapped and judged-not-about are distinct
again; assumed topics say "(not tested)"; exam or held-out sections say why they are not mapped; the lesson's three
figure states, its close card's cold check and "no later cold check", the lesson end's "everything so far is saved",
an OpenRouter lesson's spending limit; the lesson's wait says "Checking your answer…" while grading and "The teacher
is writing…" otherwise, and a failed opening keeps "nothing was saved"; notebook run times and retry counts; the
drain's results ("kept", "left in the library") and "skipping costs nothing"; the overview card's "not opened yet";
the server's full-slot refusal; the band's "readiness from cold checks". The footer's longer hints pushed the window
dots and the alt note out at laptop width (BATCH5-9): short plain labels now. Four harness checks the branch could
not run failed on its words; they follow the words kept.

## 4. Menu items left for the menu worker (brief C, audit §1, §2, §4)

Applied, nouns and glyphs untouched: the `i` panel is "passage details" (its adjustments row says what LearnLoop
inferred; an alias is "from an earlier version of this source; the link may open nearby"); a transcript cue is a
caption; a search match is "possible match from search, not checked by LearnLoop"; Append and Show me say "adding …"
until the write is confirmed; no-result and failure toasts name the next step; an exercise import failure says how
to try again and its button reads close; an import that made nothing says so; the current pad's ✓ and a
suggestion's dismiss mark have words. Audit §3 and its glossary were left to the owner.

## 5. Proof

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| vitest, 4 workers | 395 files, 4382 tests, exit 0 |
| `cargo check` | clean |
| desk harness, every run | 152 passed, 0 failed (display math in the companion, pad hover card, after resize and the lesson: never clipped) |
| Python, the brief's list (protection: menu, RD6, RD10; pads, carried, companion, search, library ask, lesson, teacher, ink and GLM-OCR, routing, retired-config identities, mobile allowlist, desktop RPC contract, identity pins, structure ratchets, registry audit, plan-first transport, CLI snapshot, kill switches, SQLite copies), 122 files | 2,565 passed; 1 failed (the goal lens RPC pin lacked `goal.choices`), fixed and rerun |
| Python, second set (goal lens, GLM-OCR, figures and Show me, item and exercise authoring, retired keys) | 351 passed; 1 failed (the switched-off test lacked `goal.choices` params), fixed: 55 of 55 |
| `tests/test_architecture.py` alone; `tests/test_test_layout.py` alone | 18 passed; 3 passed |
| `ruff check` | clean |
| `lint-imports --no-cache` | 54 kept, 0 broken |
| `check_gate_partition.py` | 34,070 = landing 34,004 + arc_close 66 |

`tests/goldens/structure.toml`: `private_patch_sites` 465 → 466, with its reason on the line (the handwriting reader's
tests patch the GLM-OCR client's private opener and probe cache so no test reaches a network or an OCR server).

### Visual comparison, every stage at both viewports, against main's `findings` lines (same run of the tool)

| Stage | main `684892aba5` | batch 5 before the fixes | batch 5 tip |
|---|---|---|---|
| rd1 | 36 (colour 2, geometry 30, missing 2, type 2) | 40 (+4 missing: footer dots and note, BATCH5-9) | 36 (colour 2, geometry 30, missing 2, type 2) |
| rd2 | 21 (colour 8, geometry 6, missing 5, type 2) | 25 (+4 missing: the same, BATCH5-9) | 21 (colour 8, geometry 6, missing 5, type 2) |
| rd3 | 7 (colour 1, geometry 4, missing 2) | 7 | 7 (colour 1, geometry 4, missing 2) |
| rd4 | 19 (geometry 1, missing 15, type 3) | 19 | 19 (geometry 1, missing 15, type 3) |
| rd5 | 2 (colour 2) | 3 (promoted rows missing in the menu, BATCH5-8) | 2 (colour 2) |
| rd6 | 7 (colour 4, missing 3) | 7 | 7 (colour 4, missing 3) |
| rd8 | 3 (colour 2, geometry 1) | 3 | 3 (colour 2, geometry 1) |
| rd9 | 4 (geometry 4) | 4 | 4 (geometry 4) |

117 comparisons, none unreachable. At the tip every finding is identical to main's (same region, kind, property,
mockup and app values); none new, none gone. The menu, band, shelf, pads' bars, companion and pen lines show no
change from the longer strings.

## 6. Not reconciled

- COPY-5 to COPY-10, COPY-12 and COPY-13 stay open (outside this brief).
- A few `DeskShell.menu.test.tsx` tests failed once each (0 to 5 ms) when run beside other files while the C edits
  were in progress; they pass alone, repeated, and in both full vitest runs since.
