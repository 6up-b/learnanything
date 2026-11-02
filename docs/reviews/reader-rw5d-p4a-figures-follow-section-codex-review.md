# Reader RW5d P4a: figures follow the section — Codex review fixes

- **Review:** Codex (gpt-6.1-sol), job `20261101-231531-kwMbWR`, three Medium findings, no High.
- **Branch:** `reader/rw5d-p4a-figures-follow-section` in `learnanything-ad1`. No migration, no schema change, no
  live calls (fakes only; the only scripts run outside pytest were the desktop catalog generator and validator, under
  `env -i` with an empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR).

## Review

Each finding was reproduced with a failing test first, then fixed.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Failed revalidation leaves a protected figure visible | fixed | 20c6c3ad38 | `figuresFollowSection.test.tsx` "a followed figure its own book stops listing leaves on the next press": success, then listing omits it (held out), then pressed again: removed, `expandedKey` cleared; same after an unreadable (rejected) listing. Failed before the fix. |
| F2 | Medium | The correspondence kill switch leaves followed figures active | fixed | 20c6c3ad38 | `figuresFollowSection.test.tsx` "switching correspondence off clears a followed figure, and a follow still in flight never lands": follow, then `followEnabled` off: cleared, not rendered, press does nothing (no RPC), back on stays cleared; a deferred listing resolved after switch-off returns false and shows nothing. Failed before the fix. |
| F3 | Medium | The quiet correspondence read can perform whole-book verification and writes | fixed | 65dbc9b759 | `test_reader_rw5d_p4a_figures_follow.py::test_the_quiet_read_never_reverifies_an_outdated_sketch_or_writes`: two sketches under an older engine (one in an unrelated section); `reader.correspondents` runs `verify_sketch` zero times and leaves every table count unchanged; opening through `reader.figures` still re-verifies and appends to `judgment_ledger`. Before the fix the read verified both sketches. |

### What changed
- **F3 (backend):** `list_figures` is split into `_listed` (the chain picks, withheld check and placements, read-only)
  and the presentation (`figure_view`). `section_figures` now reads `_listed` and applies only the pure row
  transforms (`shown_row`, panel/sketch/rich switch rows, `worded_row`, `_label`), plus the anchor rule factored
  out of `figure_view` as `_anchor_span`. An outdated sketch is not re-verified by the quiet read; a verdict this
  process already reached (`_RECHECKED`) is honoured (a failed one is not offered). Re-verification and its ledger
  append stay on actual opening (`reader.figures` of its own book); a sketch that then fails is refused by the
  client (F1's path).
- **F1 (frontend, `useFigures.follow`):** a current-generation refusal (not listed, not shown, or unreadable) removes
  every placement of that figure from `followed` and clears `expandedKey` if it was one of them.
- **F2 (frontend):** `useFigures` takes `followEnabled` (ReaderScreen passes the contract's
  `correspondence.alsoInBooks`, present only while `reader.correspondence.enabled` and curriculum are on; default
  false, so the side pane never follows). Off: `followed`/`under()` return none at render, an effect clears the
  state and its open key and bumps a follow generation, so an in-flight follow is dropped when it lands; `follow`
  refuses without an RPC.
- Stage record `docs/reviews/reader-rw5d-p4a-figures-follow-section.md` corrected where the review said its claims
  did not hold (read-only; "shows nothing"; switch-off coverage).

## Gate (this fix step; the full suite runs once in the landing gate)

- `uv sync --extra dev --extra mobile` + `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **40 kept, 0 broken**.
- Targeted pytest (memory-capped scope, `-n 6`): **920 passed, 0 failed** (34 files): every test file that exercises
  `learnloop.figures.service` listing/presentation or `reader.correspondents`, plus contracts:
  `tests/test_curriculum_c0b_landing.py`, `tests/test_figure_label_wording.py`, `tests/test_figure_offers.py`, `tests/test_figure_rich_contract.py`, `tests/test_figure_rich_failed_correction_durable.py`, `tests/test_figure_rich_job.py`, `tests/test_figure_rich_rereview_fixes.py`, `tests/test_figure_rich_review_fixes.py`, `tests/test_figure_rich_rpc.py`, `tests/test_figure_verification.py`, `tests/test_figures_codex_review.py`, `tests/test_figures_final_round.py`, `tests/test_figures_fix_round2.py`, `tests/test_figures_fix_round5.py`, `tests/test_figures_rw5b_review.py`, `tests/test_figures_scope_redesign.py`, `tests/test_figures_show_me.py`, `tests/test_figures_show_me_codex_review.py`, `tests/test_learner_data_relax_2.py`, `tests/test_mobile_allowlist.py`, `tests/test_reader_ca3_landing_ca5a.py`, `tests/test_reader_ca4_landing.py`, `tests/test_reader_ca5_also_in_books.py`, `tests/test_reader_ca5_landing.py`, `tests/test_reader_ca5a_find_section.py`, `tests/test_reader_rw5d_p4a_figures_follow.py`, `tests/test_section_coverage.py`, `tests/test_section_coverage_review.py`, `tests/test_section_coverage_rpcs.py`, `tests/test_sketch_service.py`, `tests/test_architecture.py`, `tests/test_sketch_verify.py`, `tests/test_sketch_sandbox_review.py`,
  `tests/test_desktop_rpc_contract.py`.
- Durability lane: not applicable (no migration, DB or connection code changed).
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` clean; vitest (`--maxWorkers=4`) on every
  test file touching figures, correspondence or `useFigures`: **20 files, 403 passed, 0 failed**
  (`src/screens/reader/alsoInBooksReader.test.tsx`, `figures/FigureInline.test.tsx`, `figures/advancedPanels.test.tsx`,
  `figures/figureGrammar.test.ts`, `figures/figuresFollowSection.test.tsx`, `figures/libraryOfferSettle.test.tsx`,
  `figures/readerFigures.test.tsx`, `figures/richFigure.test.tsx`, `figures/showMe.test.tsx`,
  `figures/sketch/SketchFigure.test.tsx`, `figures/sketch/sketchSandboxReview.test.tsx`, `figures/tutorOfferPress.test.tsx`,
  `figuresWithReadingPath.test.tsx`, `findSectionByPoint.test.tsx`, `findSectionReader.test.tsx`,
  `readerCorrespondenceSettings.test.tsx`, `sideBySideCorrespondence.test.tsx`, `sideBySideIntent.test.tsx`,
  `sideBySideReader.test.tsx`, `alsoInBooks.test.tsx`); `npm run frontend:build` ok.
- `cargo check`: not applicable (nothing under `src-tauri` changed).
- Desktop catalog regenerated after the code commit (e5d5c63de1); `desktop_validate.py` passes: 305/305 TS + 6/6 Rust,
  ACTIVE=311, reproducible byte-for-byte.
- DB reference scripts: not applicable (no schema change).
