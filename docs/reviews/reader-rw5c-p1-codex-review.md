# Reader RW5c P1: Codex review, fix step

- **Review:** gpt-6.1-sol, job `20261102-210953-w9Fl9a`, on branch `reader/rw5c-p1` at `cc4aac36f1`.
- **Fix commits:** `63aafe9199` (the fixes), `ccd9765f62` (desktop catalog), and this record.

## Findings

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Unbraced radical parsing produces a false "checked" | fixed | `63aafe9199` | `test_rw5c_source_check.py::test_an_unbraced_radical_never_certifies_the_meaning_the_page_does_not_show`; `test_rw5c_book_math.py` render corpus; `bookMathRender.test.ts` |
| F2 | High | The audit command exposes equations after their source becomes held out | fixed | `63aafe9199` | `test_rw5c_recheck.py::test_the_audit_lists_no_equation_of_a_source_held_out_after_its_check` |
| F3 | Medium | Scientific-notation endpoints render as different mathematical bounds | fixed | `63aafe9199` | `test_rw5c_labels.py::test_f3_a_scientific_endpoint_is_written_as_the_power_it_means`; `figureLabels.test.tsx` (MathML structure) |
| F4 | Medium | "Open the page" silently fails for another book's equation | fixed | `63aafe9199` | `figureProvenanceReader.test.tsx` (real Reader callback, two books) |

Every finding reproduced before its fix.

### F1

The real pipeline reproduced it: `f(x)=\sqrt16 x` against the definition `4*x` came back `checked`. KaTeX shows `<msqrt><mn>1</mn></msqrt><mn>6</mn><mi>x</mi>`, which is `6x`.

`\sqrt` now takes only `\sqrt{u}`, as §5.3 says (`function_arg`).

The same class went beyond the reported case. KaTeX probes found three more forms where the page and the reader disagree, and each is now refused:

| Form | The page shows | Was read as | Reason key |
|---|---|---|---|
| `2 3 x` | `23x` | `6x` | `syntax` |
| `1\,000 x` | a thousand times x | `0` | `syntax` |
| `x^a_1`, `e^x_1` | `x₁` to the `a` | `x` to the `a1` | `subscript` |

A numeral before a numeric fraction is also refused (`3\frac{1}{2}` is a mixed number on the page, and the product would be 1.5; `syntax`). This one is a reading convention, not TeX grouping, so it sits in the unreadable table rather than the render corpus.

`bookMathRenderCorpus.json` is one corpus for both lanes: vitest pins KaTeX's MathML for each form, and pytest pins what the reader does with the same string. §5.3 gains a paragraph, and the stage record gains Deviation 9.

The closed-reader structure stays, so this is one more list of refusals. It is the first round on this class. If another round finds the same class, the structural answer is to read the source through KaTeX's own parse tree, not to extend the list.

### F2

`audit` now takes the same `withheld` predicate as `coverage` (`FS.row_withheld`). A figure withheld now is left out of `checked`, `figures` and `outcomes`, and is counted under `skipped.withheld`.

The reader report's `source_checks` block holds only counts and no equations, so it is unchanged.

### F3

Both renderers now write an exponent in TeX as `1 \times 10^{-7}`, with the same digits and the same words in Python (`template_words`) and TypeScript (`derivedWords`). The plain strings (`aria-label`, SVG text) keep `1e-7`, which reads correctly as text. §7.2 is amended.

### F4

A cited extraction other than the open one now resolves its book through `reader.render_view`:

- **Another book:** opens as a detour through `openLibraryHit`.
- **An earlier reading of this book:** reopens through `openSource` with `jumpReading`, so the span is translated and never peeked as a span of this reading.
- **Cannot be opened:** an unknown extraction shows the error it raised. A book not in the library, or an open already in progress, shows "That page couldn't be opened."

`get_span_view` was not used for the lookup because it records a `source_exposure` on every view. The press costs one extra `render_view` read.

The new tests fail on the old callback (3 of 4; the fourth pins the same-reading case, which already worked).

### The review's claims and conformance notes

- "Every deviation is additive or stricter": true again now that the bare radical is gone (Deviation 9).
- "Bounds ... written losslessly": record line amended (F3).
- Automatic recheck on lesson and attempt hosts: already recorded as Deviation 8 and in the record's open questions. No change.

### Also found

`desktop_validate.py` failed on this branch: its inventory pins still counted 308 TypeScript files, without the stage's `figureLabels.tsx`. The pins are now 309 files, 299 entry-reachable and 315 ACTIVE. The stage record's desktop row (`PASS`) cannot have been a run of the validator on that tree.

The coverage numbers in the stage record (92 of 319 relations read) predate these refusals and were not re-measured, so they may read slightly high.

## Gate

Targeted only, per the owner's 2026-10-17 rule; no full suite and no whole-vitest run. Every test, npm and vitest command ran in the 5G memory-capped scope. Python outside pytest ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No live calls and no spend.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 42 kept, 0 broken |
| targeted pytest `-n 6` (16 files below) | **749 passed** |
| `npm install`, `npm run typecheck` | clean |
| vitest `--maxWorkers=4` (the `screens/reader/figures/` directory, plus 2 files below) | **465 passed**, 22 files |
| `npm run frontend:build` | built |
| `desktop_generate.py`, then `desktop_validate.py` | PASS |
| `module_validate.py` | PASS |
| `cargo check`, durability lane, DB references | not needed: no `src-tauri`, migration, connection or schema change |

**Pytest files:** `test_rw5c_book_math`, `test_rw5c_display_twins`, `test_rw5c_judgments`, `test_rw5c_labels`, `test_rw5c_migration`, `test_rw5c_never_evidence`, `test_rw5c_recheck`, `test_rw5c_source_check`, `test_rw5c_switch_off`, `test_codex_output_schema`, `test_figures_migration`, `test_figure_label_wording`, `test_figures_scope_redesign`, `test_cli_help_snapshot`, `test_architecture`, `test_public_tip_guards`.

**Vitest files:** everything under `src/screens/reader/figures/` (including the new `bookMathRender.test.ts` and `figureProvenanceReader.test.tsx`, and `figureLabels.test.tsx`), plus `src/screens/reader/alsoInBooksReader.test.tsx` and `src/screens/reader/figuresWithReadingPath.test.tsx`.
