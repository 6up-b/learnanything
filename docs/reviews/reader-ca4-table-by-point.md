# Reader CA4: the table by point (stage `reader-ca4-table-by-point`)

Branch `reader/ca4-table-by-point` (worktree `learnanything-dl1`), base CA3's verified tip
`d7850780b` (CA3 is not on `main` yet; it lands after CA5a). Spec:
`docs/specs/ux_reader_compare_ask_v1.md` §5 (all), §9 X3, X4 and X5, §11 K13, §12.2 (the
`source_compare.v2` request, `CompareKeep`'s mapping and the four-view bound), §13's CA4 row
and its kill switch, §15 Q7 (owner decisions 2026-10-25).

**No migration. No successor. No paid call was made** (every model in the tests is a fake;
nothing outside pytest called a route). Comparisons stay display, and a keep stays proposals in
the source-object layer: no scoring, scheduling, projection, serving or replay path reads a
comparison, its points, a kept cell or a hidden row. The successor ruling of §13 holds: I found
nothing that makes a comparison evidence.

## 1. What was built

### `source_compare.v2` (§12.2, K13)

`compare_sources(..., by_point=True)` (`src/learnloop/source_retrieval/compare.py`): the same
route (`source_compare`) and one call, prompt `source_compare.v2`, result model
`SourceComparisonV2`:

| Field | What it is |
|---|---|
| `points[].label` | a short label for one thing the books can be compared on |
| `points[].perspective` | one of the requested perspectives, exactly as written, or empty |
| `points[].cells[]` | per source: `status` `quoted` (a verbatim `quote` and one `line`) or `not_addressed` |
| `points[].relations[]` | per pair addressing the point: v1's `PairRelation` (the unchanged `RELATIONS`, no `complementary`) |

There is no consensus, summary or canonical field (pinned). The code, not the model, decides
what is shown (`_verified_points`):

- every quoted cell's quote is checked against its own source's passage with v1's `_quote_in`;
  a cell that fails is `not_addressed` and listed in `dropped_lines`, never repaired; a cell
  naming no compared source (or one twice) is dropped;
- every compared source has a cell on every point (one the model left out is not addressed);
  a quoted cell names the block that holds its quote (`span_key`; an anchor of several blocks
  names the right one);
- a relation stands only between two quoted cells of its point, with both quotes verified, one
  per pair; others are dropped;
- a requested perspective is a point labelled by the learner's words (`kind: perspective`), one
  per perspective (a second point the model gives for one is an ordinary point); one the model
  gave nothing for is appended with every cell not addressed ("not found in your library");
  the model's points come first, then the learner's views in their order;
- a model point no book quotes, or with no label, is dropped.

Stored in `source_comparisons.comparison_json` (no migration) as `contract`, `points`, and, so
every v1 reader reads a v2 row unchanged (the by-book table, Keep's v1 mapping, the tutor about
a comparison, the exam-withholding provenance), each quoted cell as its source's v1
`contribution` (naming its `point_id`) and each point's relations as v1 `relations` (naming
their point). `missing_perspectives` is the views no book fills. A v2 request is cached under
its own identity (its query hash names the contract), so it never reuses a v1 row and a v1
request never reuses it; v1's hash is unchanged.

### The Reader's request and table

`reader.library_compare` asks by point while `reader_compare.by_point` is on, from every door
(CA3's one request, plus `by_point`; with CA3 off the pinned request asks by point too).
`LA.compare_table(..., by_point=True)` adds `points` (`point_rows`: per point its id, label,
kind, the label's voice, one cell per column keyed by the by-book row's `key`, and its pairs'
relations by column key) and `contract`; `rows` stay the by-book view. The prompt contract adds
`libraryAsk.compareByPoint`.

### The grid (`ComparePointTable.tsx`; §5.1, X3, X4)

- A row per point, a column per book (the anchor's or open book's first, *your passage*), the
  learner's *› you* column last. The point column is sticky; a grid wider than its frame scrolls
  sideways inside the frame (`POINT_COLUMN_PX`, `READABLE_CELL_PX`, `YOU_COLUMN_PX`: layout
  bounds in CSS px, not learned constants).
- A row header is LearnLoop's (`◇`, dotted rule; *LearnLoop's point* the first time, then only
  `◇`) or, for a requested view, the learner's (`›`, amber rule).
- A cell is the book's verified words (`§ "…"`, two lines at most, `more`/`↵` to expand), then
  LearnLoop's line under a dotted rule; *— not addressed here*, or *— not here* on a requested
  view. A view no book fills reads *· not found in your library*, with *where else is this
  explained? ▸* where the host offers it.
- Chips (`comparePoints.ts` `rowChips`): exactly the relations the row's pairs returned, in the
  table's order, in the shipped plain words; *the same claim* only when every pair of the books
  quoted on the row said it; *only in Axler* when one book alone is quoted; no colour, no count.
  `↵` on the row header (or a press on a chip) opens the pairs: *Axler ⇄ Strang · different
  assumptions · ◇ statement § "…" / § "…"* (RW4d's band, on its row).
- The three voices never share a box; a screen reader hears *"Strang, on why eigenvalues exist.
  From the book: … LearnLoop's reading: …"*, *"…: not addressed here."*, chips as *"LearnLoop's
  reading of how they relate: …"*, and once the table is there *"Comparison ready: 4 points"*
  (Q7). Nothing takes focus on landing or animates (K16).

### Keep, takes and hidden rows (§5.2, §12.2)

The grid holds keep (`k`, *keep comparison ⇄*), *remove*, the takes and hide row; `CompareKeep`
renders nothing under a table by point. `reader.library_compare_keep` gains `hiddenPoints` and
takes by row (`pointId`) or on the whole comparison (`about: "comparison"`); exactly one target
per take.

`kept_comparisons.py`, a keep by point (`layout: "by_point"`), maps each quoted cell of every
row not hidden to **one claim** (`source_objects`, proposed, AI-authored, cited to the block
holding its quote, rechecked against the block as it is now), with the row's `point: {id, label,
kind}` and its line in `content_json`; each verified relation of a row becomes a relation
between that row's two claims by the same `RELATION_MAP`. A row take is a `learner_connects`
relation on the row's first two claims (a row no book fills is refused: nothing to hold it); a
take on the whole comparison relates its first two claims from different books. A take is
idempotent by its row and words. A hidden row before Keep is left out (and recorded); hiding a
kept row supersedes its claims, relations and takes (append-only; each successor recorded on
`hidden_rows`, which `relation_lineage` now reads with the removals); showing it again proposes
it again from the stored comparison. Reopening shows only kept cells and relations, hidden rows
folded with their stored cells (so *show* can propose them). A v1 comparison, or any keep while
the switch is off, is kept by source exactly as before.

### Keys (§5.5)

Checked against the comparing posture's keys. Roving focus starts on the first row header and
moves only on the learner's key: `↑↓←→`, `Home`/`End`; `Space` peeks the cell's passage (the
library answer's peek, now able to read any compared passage); `o` opens the book there in the
left pane (with a crumb); `↵` expands a quote or opens a chip's pairs; `t` your take; `-` hide
or show; `v` by point / by book; `k` keep. `/` (refine), `+` (*+ add a book*, new in
`useCompareControls`) and `Ctrl+↵` (the tutor about this comparison) are left to the
comparison's controls, as before; `Esc` closes pairs or a take box first, then belongs to the
posture.

### Narrow widths and by book (§5.6, X5)

- Below the app's 1,040 px breakpoint, or in a pane too narrow for the point column and two
  readable cells, the grid becomes cards by point (the label and chips, each book's cell under
  its name, *› you* at the foot) with the same keys (`↑↓` points, `←→` books).
- The comparing posture stacks below the breakpoint (the comparison above the book, UX §3.1), and
  a resized window re-clamps the remembered pane width (RW4a computed it once, at mount).
- *By book* (`v`, or the toggle in the header; remembered per device in `localStorage`,
  `ll.compare.layout`): one card per book with its cell on every point.

### Old comparisons (§5.3)

A comparison with no points (stored before v2, or any comparison while the switch is off)
renders by book exactly as today (three cells and the relations band), with no "old" label.
Where a library question hosts the table, *compare again by point ▸ · runs one comparison*
re-runs its passages by point (pins = its passages, its views kept).

### The kill switch

`[reader_compare] by_point = true`. Off, exactly today: the Reader requests v1 (no `by_point`
in the call, `source_compare.v1` stored), the table has no `points`, the prompt contract has no
`compareByPoint`, the posture does not stack or re-clamp, keep is by source, and `hiddenPoints`
and row takes are refused (`reader_compare_by_point_disabled`). A keep by point made while on
reopens by book while off.

## 2. Parameters (no made-up constants, owner 2026-10-24)

Classified in `src/learnloop/params/parameter_registry.py` (structural, display):

- `reader_compare.by_point`: a kill switch.
- `reader_compare.max_perspectives = 4` (`keep`: a stored-size bound, §12.2; `le=8`, the RPC's
  own request bound). It replaces CA3's module constant `MAX_PERSPECTIVES`; the RPC, the keep
  contract (`compareKeep.maxPerspectives`) and the refine box's limit read it.

No weight, margin or threshold was added. The chip rule is the spec's table; the clamp length
for *more* (140 characters) and the column widths are display bounds.

The defaults snapshot moves only because the effective config gains the two keys: all 28
`DEFAULTS_SNAPSHOT_BY_ALGORITHM` values were recomputed from the composed defaults
(`defaults_fingerprint_for_version`), each with one comment. The DB/config reference was
regenerated (1,071 leaves) and validated (`errors: []`).

## 3. Tests changed to pin v1 with the switch off

Tests that pin RW4d's keep by source, RW1c's and RW4d's switch-off goldens and CA3's anchor
keep now set `reader_compare.by_point = false` (each with a comment), because the v1 path is
exactly what the switch restores: `test_compare_sources_keep.py` (its `library` fixture),
`test_compare_keep_switch_off.py`, `test_reader_tutor_switch_off.py`,
`test_reader_ca3_codex_review.py` (its `library` fixture), `test_reader_ca3_compare_anywhere.py`
(the switched-off request; the four doors now also send `by_point`), and
`test_rw4_kill_switches.py` (the on-contract gains `compareByPoint`). The shared fake
(`tests/source_service_fakes.py`) answers `SourceComparisonV2`.

## 4. Deviations and open points

1. **Column headers** show the book and page (*§ Strang p.12*), not the section locator
   (*§6.1*): the comparison's row carries no section today. Adding it is a read of the block's
   section path at table time; left for the owner to want.
2. **Pending** stays CA3's one line; the provisional *by book* layout of excerpts before the
   rows exist (§4.2) needs a progress signal from the job, which it doesn't have.
3. **Compare again by point** is offered where a library question hosts the table (a library
   answer's *you compared these on … · reopen ⇄*, the comparing pane). A kept comparison reopened
   from a `⇄` margin mark has no library question beside it, so it opens by book there with no
   re-run button.
4. **Hiding a kept row supersedes its takes too** (they are learner relations on that row's
   claims); showing the row again proposes its cells and relations again but not the takes,
   which stay superseded (their words are kept in the superseded rows and the hidden-row
   history).
5. **A v2 comparison viewed with the switch off** (a keep made while on) renders by book from
   the stored cells (each cell is its book's contribution there).
6. No real comparison call verified the v2 request (launch rule: no live calls). The schema is
   built from typed models, so the provider gets a strict schema; a minimal paid check on a
   backup copy is cheap if the owner wants one before the landing.

## 5. Gate (this step; the full suite runs once at the landing)

All test commands inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

GATE_PLACEHOLDER
