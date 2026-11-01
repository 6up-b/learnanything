# Reader follow-ups Nov 1b: Codex review and fix step

Stage `reader-followups-nov1b`, branch `reader/followups-nov1b`, worktree `learnanything-merge2`. Codex review job `20261101-144233-8vrpBc` (gpt-6.1-sol). Stage record: `docs/reviews/reader-followups-nov1b.md`.

- No migration, no config key, no successor. Kill switches unchanged.
- No paid or live model call. Every model in the tests is a fake. Cost: $0.
- No Python ran outside pytest except `lint-imports` and the doc scripts. The doc scripts ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## Review

### Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | The forbidden "matches the book" claim passes | fixed | `c6a9063313` | `tests/test_figure_label_wording.py::test_f1_*`: 6 matcher cases (none has `(checked)` or a check glyph), the Manim narration refused, the spec's repair call. All failed before the fix. |
| F2 | Medium | Collapsing newlines lets narration impersonate check labels | fixed | `c6a9063313` | `test_f2_a_label_lead_on_its_own_line_is_matched` (7 cases: bare, `\r\n`, `**Checked:**`, `- Verified:`, `## Checked`, `1. Checked:`, `> __Verified__`) and `test_f2_a_manim_narration_with_a_check_line_is_a_problem` failed before the fix. `test_f2_ordinary_multiline_prose_is_not_matched` (5 cases) passes. |
| F3 | Medium | Cached figures bypass the wording rule | fixed (the successor part rejected, see below) | `c6a9063313` | `test_f3_*`: a spec listed, reused and as first delivered; a sketch listed; a Manim title, transcript and report assumptions listed. The stored row is unchanged in each. All 3 failed before the fix. |
| F4 | Low | An aged-out cancellation resurrects an obsolete failure | fixed | `98fc6f253e` | `tests/test_figure_rich_failed_correction_durable.py::test_codex_f4_…_after_500_newer_rich_jobs` uses a real queue of 500 newer `figure_rich` jobs, not a filtered window. It failed before the fix: A's failed line came back. |

### What changed

**F1** (`figures/labels.py`). N-a's source-verification claim is matched on its own, without needing a check word or glyph. The constants are `SOURCE_CLAIM_VERBS` and `SOURCE_NOUNS`, both `keep` wording-rule constants and not model parameters.

- It matches *match/matches/matched/matching* or *agree(s/d) with*, then *the* or *your*, then *book(s)* or *textbook(s)*.
- It also matches a check word followed by *against the/your book(s)*.
- RW5c's eventual label stays RW5c's to draw. Until then, no model text can claim it.
- *the book's notation for the rate* is not matched (negative test).

**F2** (`figures/labels.py`). `label_like` now also reads each line at the text's original line breaks, before whitespace collapses.

- The Markdown lead (quote, heading, list or number marker) and the emphasis (`* _ \` ~`) are ignored.
- On each line it looks for the badge forms: a lead (`Checked:`), a whole line (`Verified`), a `·` segment, brackets or a glyph.
- Ordinary prose that wraps (*The box is\nchecked when…*, *First we check…\nWe verified…*) is not matched.

**F3** (`figures/service.py:worded_row`, applied in `figure_view` after the sketch re-verification). Every presentation goes through `figure_view`: a first delivery, a listing, a reuse, and a quick figure's fuller version. In each, a stored figure is shown without its label-like text:

- `spec_json`'s `demonstrates` is emptied, and its label-like assumptions are dropped (`strip_json`);
- the stored report's label-like assumptions are dropped;
- for a Manim figure, a label-like title is left out, and each label-like transcript line is replaced by `LINE_WITHHELD` in code's words (`labels.strip_lines`), so the cut is never silent. If the transcript still reads like a label across its lines, all of it is replaced by `TEXT_WITHHELD`.

The stored row, which is the paid output, is never rewritten.

At presentation the transcript is cut in code's words rather than refused, as the author-time rule would refuse it. The reason: a stored figure was already built and paid for, and the learner had it. The proportionate bar (owner, 2026-10-24) removes the realistic harm (the label-like text) without taking the video away. An author answer still gets its repair call, and is refused if it still violates.

**F4** (`figures/rich.py:rich_job_for_figure`, `service.rich_pending`). A stored failed correction found outside the window is listed only while its job is still the figure's newest correction over the whole queue. The lookup is by payload `supersedes_id` (`newest_ingest_job_by_payload`), so a newer cancelled correction, which stores no row, still speaks for the figure after 500 newer rich jobs. This is the same rule the window applies.

### Rejected

- **F3, "version and gate the changed admission behavior" (and the claim that author answers are now repaired without a successor).** Rejected. The rule changes which figure text is shown, not evidence. Nothing it touches feeds scoring, scheduling, projections, grading or the help-outcome path. The spec's §15 rules that a change to what is served, rather than to evidence, takes a kill switch and no successor (the `explore_figure` and `+figures-v1` precedents). The algorithm-change playbook's successors are for persisted meaning.
  - The rule runs only inside the figure tiers, which keep their own kill switches: `figures.enabled`, `figures.sketch_enabled` and `figures.rich_tiers_enabled`.
  - It rewrites no stored row, so turning a tier off or on reproduces the same views.
  - The stage record's sentence "Nothing here changes … serving" was inaccurate. It now says what changed and why that takes no successor.

### Claims corrected in the stage record

- Open item 3 ("matches the book" is not matched) is superseded by F1.
- The "Nothing here changes persisted meaning … serving" bullet is corrected, as above.
- The spec's §9b.4 note now records F1 to F3.
- The labels module docstring now records F1 to F3.

## Gate (this step; the full suite runs once, in the landing gate)

Every pytest ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, at most `-n 6`, one run at a time, with `TMPDIR` outside the worktree. No frontend, `src-tauri`, schema, migration or DB/connection code changed, so npm, vitest, cargo and the durability lane do not apply.

- **Environment:** `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`: ok.
- **`uv run lint-imports --no-cache`:** **36 kept, 0 broken**.
- **Fail-first runs:**
  - `tests/test_figure_label_wording.py -k "f1 or f2 or f3"`: 19 failed, 6 passed. The 6 that passed are the ordinary-prose negatives.
  - `tests/test_figure_rich_failed_correction_durable.py`: 1 failed (F4), 4 passed.
- **After the fixes:**
  - `tests/test_figure_label_wording.py`: **64 passed**.
  - `tests/test_figure_rich_failed_correction_durable.py` plus `tests/test_figure_rich_rereview_fixes.py`: **11 passed**.
- **Targeted pytest** (`uv run pytest -q -n 6 -p no:cacheprovider`): the same 112 files as the stage gate. **2739 passed, 3 skipped, 2 xfailed, 0 failed** (5:49). That is the stage gate's 2711 plus this step's 28 new tests.
  - The set covers every test file that imports or drives `figures.service`, `figures.rich`, `figures.labels`, `figures.manim_figure` or the figure fixtures, including every caller of `figure_view`, `list_figures` and `rich_pending`. It also covers the contract tests: architecture, registry audit, tracked fixture databases, public-tip guards and SQLite file copies.
- **References:** `db_generate_reference.py` and `desktop_generate.py` were rerun because line citations and source commits moved. Results:
  - `db_validate_reference.py`: errors `[]`;
  - `desktop_validate.py`: passed, 297/297 TS/TSX and 5/5 Rust, byte for byte;
  - `validate_vault.py`: passed, 1365 notes, 1363/1363 reachable.
- **After the last docstring and doc edits:** `tests/test_figure_label_wording.py`, `tests/test_registry_audit.py`, `tests/test_architecture.py` and `tests/test_public_tip_guards.py` were rerun: **114 passed**.

Test files run: the 112 listed under "Test files run" in `docs/reviews/reader-followups-nov1b.md` (they include `test_figure_label_wording.py` and `test_figure_rich_failed_correction_durable.py`, the two files changed in this step).

## Orchestrator scoped verify remainder, fixed

The orchestrator's scoped Sol verify (job `20261101-151747-gKdoDv`) found F2 and F4 closed and F3's presentation coverage closed. It left one remainder of F1:

> Source claims survive ordinary Markdown formatting — labels.py:186. `This curve matches **the book**.` returns no match: Markdown-normalized lines run only _BADGE, excluding _SOURCE_CLAIM. Manim parsing accepts this narration and stored presentation leaves it unchanged. Fix: run source-claim detection on Markdown-normalized text too, retaining detection across line breaks.

It also reported that the ordinary-prose examples pass, that nothing is wrongly refused, that listing and reuse do not diverge, and that the newest-correction scan (about 0.21 s for 20 lookups over 50,000 jobs) is not a finding.

**Fix** (`figures/labels.py`). `label_like` now also reads the text as its Markdown renders. Emphasis, code spans and link or image targets are dropped (`_LINK`, `_EMPHASIS`). The lines are joined without their leads. `_PHRASE` and `_SOURCE_CLAIM` run on that text, and `_BADGE` still runs per line (F2). A claim inside `**...**`, `` `...` `` or `[...](...)`, or one broken over a line break (including a link text that spans lines, or a next line starting `> `), is matched. `strip_lines` replaces the line that holds it. When no single line reads like a label but the whole text does, it replaces all of it with `TEXT_WITHHELD`.

**Tests** (`tests/test_figure_label_wording.py`, 23 new):

- `test_f1_remainder_a_source_claim_inside_markdown_formatting_is_matched`: 13 cases (bold, italic, `__`, code span, inline link, link around the verb, image alt, emphasised *verified against the book*, `_agrees with_`, three split across a line break, a link text split across lines).
- `test_f1_remainder_ordinary_formatted_prose_is_not_matched`: 8 cases, among them *the **book's** notation*, *We \*match\* the curve to\nthe data.*, *[The book](#p3) defines the rate*, and *This curve matches the data.\nThe book has more examples.*
- `test_f1_remainder_a_manim_narration_with_a_bold_source_claim_is_a_problem`: `parse_figure` refuses the bold and the line-broken narration.
- `test_f1_remainder_a_stored_transcript_with_a_formatted_source_claim_is_presented_without_it`: `strip_lines` replaces the line, replaces the whole text for a claim split across lines, and leaves ordinary text unchanged.

**Fail-first.** Before the fix: **9 failed, 14 passed**. The 14 that passed are the 8 negatives and the 6 matched cases the plain fold already caught: italic, code span, the link around the verb, and three of the line-broken cases. They stay as regression guards. After the fix: `tests/test_figure_label_wording.py` **87 passed**. Then `tests/test_figure*.py`, `tests/test_figures*.py`, `tests/test_manim_figure_checks.py`, `tests/test_sketch*.py`, `tests/test_registry_audit.py` and `tests/test_architecture.py` (`-n 6`, 5G scope): **850 passed**.
