# Reader RW5c P1: the source equation is read from KaTeX's own tree

- **Why:** an independent Astra review (job `20261102-214532-PSawo6`), after two Sol rounds on the same class, found two more ways our TeX reader disagreed with what KaTeX shows on the page. Orchestrator's stuck-loop ruling: a structural fix, not another refusal list.
- **Branch:** `reader/rw5c-p1`, from `ab6ae05d7c`. No migration (238 stands), no successor.
- **Bumps:** `READER_VERSION` is `book-math-v3+katex-0.16.47`, `CERTIFICATION_VERSION` is 3, so a stored `checked` from before this is neither delivered nor skipped by a recheck.

## Findings

| Id | Severity | Finding | Reproduced on the old code by | Fixed by |
|---|---|---|---|---|
| A1 | High | `$\def\sin{\cos}f(x)=\sin(x)$` with figure `sin(x)` on [0,1]: `checked`, while the page shows `cos` | `test_rw5c_source_check.py::test_a_macro_definition_in_the_segment_is_never_checked` | any definition is `macro_definition`; the tree shows the rest |
| A2 | High | `$f(x)=e^x^2$` with `exp(x)^2`: `checked`, while the page shows red TeX | `::test_a_double_superscript_the_page_shows_as_an_error_is_never_checked` (the old run printed `outcome='checked'`) | KaTeX refuses it: `not_rendered` |
| A3 | Medium | A marker at `(2^3)^2` sits at 64; its SVG label said `2^3^2`, which is 512 | `test_rw5c_labels.py::test_a_power_of_a_power_keeps_its_grouping_in_plain_text` (512.0 == 64.0) | `to_plain`: `^` groups to the right |
| A4 | Medium | `(1e-3)^2` wrote `1 \times 10^{-3}^{2}`, a KaTeX error shown as red raw TeX | `::test_a_scientific_literal_as_a_base_is_grouped_in_both_writers` | both writers group a scientific literal as a base |
| A5 | Low | `reader report --since` filtered on check dates and counted lifetime activity | `test_rw5c_recheck.py::test_since_*` (run against the old `report_block`: `{'with_book': 0} != {'with_book': 1}` and the reverse) | opens and revision notes go by their own `created_at`; a figure's "has a book element" comes from its latest check whatever its date |

## 1. KaTeX in the engine: what was measured

**The sketch engine cannot run KaTeX, so a variant does.** Loading the vendored file in `sketch-engine.wasm` stops at once: `load: SyntaxError: RegExp are not supported`. KaTeX's lexer is a regular expression, and a sketch must never have one (spec_reader_show_me_figures_v1 §9). A hand-written RegExp in JavaScript would have been a new reader of TeX, so it was not considered.

**The variant.** `build.py` gains `variants` in `engine.lock.json`: the same `sketch_engine.c` and the same pinned sources under `-DSK_WITH_REGEXP`, one `#ifdef`. Output `apps/learnloop-tauri/sketch-engine/book-math-engine.wasm` (965,463 bytes, G8's `APP_WASM` lists it, `LICENSES.txt` covers it). `build.py --check` rebuilds both: `reproduced sketch-engine: 7fc76715…` (unchanged, so no stored sketch re-verifies) and `reproduced book-math: f2b6894c…`. The fallback in the brief was not needed.

**The caps are not weakened or even different.** A test pins `sk_limits()` of the variant to `SKETCH_MEMORY_BYTES`, `SKETCH_FUEL_PER_CALL` and `SKETCH_SERIALIZE_TICKS`. Builds at other tick counts measured what that leaves room for:

| Measure (carson, wasmtime) | Result |
|---|---|
| Compile the module, once per process | ~120 ms |
| Load KaTeX 0.16.47 (272,537 bytes) | ~20 ms; fits at 4 ticks of the 16 allowed; 287 M of 4,000 M wasm fuel |
| A real segment (`f(x)=…`, a `cases`) | 0.2–0.7 ms; 1–7 M wasm fuel |
| 40-level `\frac`, 200 parens | ~5 ms; fits at 8 ticks |
| 2,400 tight characters (`x+x+…`) | over 16 ticks: `too_long` (64 would fit; not worth widening) |
| The whole coverage run below, 895 segments, with the old reader and MathML beside it | 1.8 s |

**Where it runs.** `read_candidates` opens one `katex_tree.Trees` per check, only if a segment needs reading; `SC.check_figure` runs at build and at recheck. `test_reading_a_figure_never_opens_the_katex_engine` pins that a Reader read does not. `test_a_check_loads_one_engine_however_many_segments_it_reads` pins the reuse. `sketch_engine` and wasmtime stay out of the sidecar's start (`test_sidecar_start_imports_neither_wasmtime_nor_the_engine` caught the first version; the import is now inside `Trees`).

**The vendored file.** `sketch-engine/katex/katex.min.js`, ASCII text with no NUL, byte-identical to `node_modules/katex/dist/katex.min.js`, MIT notice in `katex/LICENSE`. `test_the_vendored_katex_is_the_one_the_reader_locks` ties version, npm integrity and SHA-256 to `package-lock.json` and rules out a second KaTeX; a second test compares bytes when `node_modules` is there. A bump also fails `test_a_katex_bump_moves_the_reader_version_and_needs_a_certification_bump` until `CERTIFICATION_VERSION` moves.

## 2. What the page's pipeline is, read from the code

- **Settings.** `MarkdownMath` passes `rehype-katex` no options, so `katex.renderToString(value, {displayMode, throwOnError: true})`: `strict` is the default warn, `trust` false, and `macros` a new object on each call. `katex_tree`'s program passes exactly those. `displayMode` follows the delimiter; a test shows it does not change a readable tree, because the only display-sensitive constructs are outside the table.
- **Does a definition in another block reach this one? No.** Not even within a block: each math element is its own KaTeX call with fresh settings. `bookMathRender.test.ts` shows it on the real pipeline (`$\gdef\foo{1}\foo$ and $\foo$` errors on the second), and `test_a_definition_never_reaches_another_parse_in_one_engine` shows that one reused engine behaves the same. So only a definition in the segment itself is refused.
- **The tree hides `\def`**: KaTeX drops its `internal` nodes and `\newcommand` is a macro, so definitions are refused by a closed regex over the source before KaTeX is asked, and `macros` is checked after.
- **Normalization.** `source_render_views.sanitize_source_text` changes only script, embed, `javascript:` and `file://` text; a block it would change is not read (`block_health`). `math_text` is not on this path. `normalizeMathDelimiters` rewrites `\[ \]` to a `$$` fence and `\( \)` to `$`; the reader takes `\[ \]` and leaves `\( \)` unread.
- **Segments were a second disagreement.** The real pipeline showed three shapes the old regex read and the page does not show as one equation, all now no segment: a first line after `$$` is an unshown meta string (`$$ y = 1\n+ 2\n$$` shows only `+ 2`), an inline `$a = 1\n+ 2$` is broken by the list item `+ 2`, and math across a blank line. Code spans are masked as `normalizeMathDelimiters` masks them. `bookMathRenderCorpus.json`'s `blocks` pin each against `MarkdownMath`.

## 3. The translator

`book_math.py` no longer tokenizes anything. Code lines (no comments or docstrings) went **772 → 763**, with `katex_tree.py` adding 95. Gone: the tokenizer, `_TEXT_ARG`, the regex over the left-hand side, and the refusals of forms TeX groups differently from tokens.

- KaTeX's list is flat with a script on the node before it, so `(x)^2` is `(`, `x`, `)` with a superscript and `12^x` is `1`, then `2` with one. `_items` joins numerals and keeps a script on its item, and that is the only place scripts are decided: on an operator, `\text` or a comma it is `syntax`, on a function `function_power` or `log_base`, and a subscript anywhere but a symbol is `subscript`. Nothing can be dropped.
- **A bare brace group is refused**, new with the tree: `{a+b}c` groups for TeX and shows nothing, so the page says `a + bc`. Reading the tree's group would have been a new false `checked`.
- **A numeral directly after a factor is refused**, one rule for `x^10`, `\sqrt16 x`, `x 2`, `1\,000`, `\frac{1}{2}3`.
- **Mathematical refusals are kept as rules over nodes:** `application` (now also with a script: `b^2(1-a)`), factorial, derivative, `sin^2 x`, log bases, `3\frac{1}{2}`, `ambiguous_slash`, `cases` coverage. New in the same spirit: `|a|b|c|` (two groupings).
- **The left-hand side** is the book's substring up to KaTeX's location of `=`, kept only when KaTeX reads that substring alone as exactly the left of this parse, and only from a label allowlist of nodes (`\color` and `\bf` swallow the `=` and are `not_equation`; `\href`, `\phantom`, `\raisebox`, a large kern are `unsupported_command`). A left-hand side of only spaces is `not_equation`.
- **Fail closed:** missing engine, wrong engine digest, changed KaTeX file: `engine_unavailable`, the sandbox is not asked. Work, memory or stack cap, or Python's recursion limit on a very deep tree: `too_long`.
- **New closed reasons,** worded in `SOURCE_CHECK_COPY`: `macro_definition`, `not_rendered`, `engine_unavailable`. A new test fails when a reason has no words.
- `\dfrac` and `\tfrac` stay `unsupported_command`: KaTeX wraps them in a style node, so stage record Deviation 5 still holds.

## 4. The shared test

- **Independent meaning.** `tests/katex_meaning.py` reads the MathML KaTeX builds (never the tree `book_math` translates) into a grammar `Node`, and both are evaluated by the grammar's evaluator at four points.
- **Corpus, both lanes.** `bookMathRenderCorpus.json`: read forms, refused forms with reasons, `not_rendered`, whole segments, blocks. Vitest sends each through the real `MarkdownMath` (`renderToStaticMarkup`) and pins the MathML; pytest pins that the sealed engine gives the same MathML, the reader's result, and the meaning.
- **Generated.** `test_whatever_reads_means_what_katex_renders` (3,000 book-style strings in the spellings books use, braces or none) and `test_whatever_reads_from_token_soup_…` (4,000). A wider hunt in scratch: **60,000 strings, 22,675 read, 0 disagreements**.
- **The differential is not vacuous.** Mutating the translator over 3,000 strings: dropping a subscript 457 disagreements, reading brace groups as groups 53, swapping a fraction 391, dropping a closer's superscript 298; unmutated 0.
- **Astra's two and F1's `\sqrt16 x`** are in the corpus and at source-check level.

## 5. A3 and A4 at class level

- **Plain writer:** `^` groups to the right (a power on the left keeps its parentheses); a scientific literal as a base is grouped; `piecewise` is written in the grammar's own form (`piecewise((x < 0, a), b)`), since `a if b; c otherwise` could not say where it ends inside a product.
- **TeX writer:** a scientific literal is grouped wherever a product would be; a fraction and `cases` are grouped as a base; a sum or an integral is grouped inside anything tighter than a sum, because it takes everything after it.
- **Templates:** a bound readout's body is grouped (`\int_{0}^{1} \left(x + 1\right)\,dx`, `of (x + 1) dx`).
- **Property tests:** 1,500 generated trees: the plain output parsed back through the figure grammar has the tree's value, and the TeX output parses in the page's KaTeX and renders the same meaning. Every other code-owned template (marker, shade, highlight, integral, sum, every panel's rendering, endpoints like `-1e-7`) parses in KaTeX. Against the old writers these tests fail. The TS twin `derivedWords`/`numberTex` only writes bounds in scripts and text and takes its body from Python, so it needed no change; `figureLabels.test.tsx` still pins it.

## 6. Coverage (§12), re-measured

Code only, counts only, under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, on fresh `learnloop.db.copies.backup_database` copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/*/state.sqlite` under the gitignored `fixtures-local/rw5c-katex-coverage/`, upgraded under `UPGRADE_SCRATCH_COPY`. No model client, no socket, $0.

| Vault | Readings | Blocks | Blocks with LaTeX | Health ok / not | Segments | Read |
|---|---|---|---|---|---|---|
| `linear_algebra` | 4 | 1074 | 194 | 194 / 0 | 402 | 50 |
| `probability` | 4 | 579 | 164 | 163 / 1 | 258 | 25 |
| `arxiv_v2` | 12 | 4717 | 57 | 57 / 0 | 235 | 16 |
| **Total** | 20 | 6370 | 415 | 414 / 1 | **895** | **91** |

Of the 320 segments that state a relation (895 minus 575 `not_equation`), **91 read (28%)**, against the earlier 92 of 319.

**Against the previous reader on the same text:** 91 read by both with **identical trees**, 0 read only by the new one, 1 read only by the old (now `relation`: a relation beside its `=` that the old split's list lacked). **All 91 agree with KaTeX's MathML.** So the structural fix cost one equation.

**Refusals by reason, and the commands in those segments** (a segment counts once for each distinct command outside the table; counts only, and a command is TeX's vocabulary, not book text):

| Reason | Segments | Commands in them |
|---|---|---|
| `unsupported_command` | 56 | `\dots` 20, `\mathbf` 15, `\hat` 12, `\partial` 12, `\oplus` 7, `\cdots` 6, `\in` 6, `\infty` 5, `\bigcup` 4, `\underline` 2, `\ldots` 2, `\bigcap` 2 |
| `multiple_relations` | 43 | `\hat` 11, `\partial` 10, `\cap` 7, `\cup` 7, `\mathbf` 4, `\binom` 4, `\in` 3, `\infty` 2, `\dots`, `\cdots`, `\to`, `\lim` 1 each |
| `relation` | 34 | `\neq` 6, `\approx` 5, `\cap` 4, `\mathbf` 3, `\choose` 2, `\cup` 2, `\iff`, `\binom`, `\leftarrow` 1 each |
| `syntax` | 30 | `\in` 8, `\mathbf` 8, `\brace` 1 (the rest use only table commands) |
| `set` | 19 | `\in` 10, `\mathbf` 9, `\cap` 9, `\cup` 6, `\triangle` 1 |
| `application` | 16 | `\cap` 1, `\cup` 1 (the rest use only table commands) |
| `binom` | 10 | `\binom` 10, `\sum` 4, `\dots` 3 |
| `sum` | 7 | `\sum` 7, `\bigcup` 4, `\dots` 3, `\binom` 2, `\infty` 2, `\cap` 2 |
| `subscript` | 4 | none |
| `not_rendered` | 3 | `\$` 3, `\in` 2, `\mathbf` 2 |
| `factorial` | 2 | `\binom` 2 |
| `limit` | 2 | `\to` 2, `\lim` 2, `\mathbf` 2, `\infty` 2 |
| `derivative` | 2 | `\partial` 2 |
| `too_long` | 1 | none |

The largest shift from the first reader is `syntax` 70 → 30 and `unsupported_command` 26 → 56: with no tokenizer, a command outside the table is now named as that rather than falling through a parse. If P2 wants rows from this, `\mathbf` and `\hat` (a label, on either side) are the largest.

## Gate

Owner rule 2026-10-17: the full suite, the whole durability lane and the whole vitest run are the landing's. Every test command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one at a time, `TMPDIR` outside the worktree. Scripts outside pytest ran under `env -i` with empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No live calls, no real sockets, no model client anywhere in this stage.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `lint-imports --no-cache` | **42 kept, 0 broken** |
| targeted pytest, 152 files (list below) | **3685 passed, 6 skipped** (an earlier run of the same list: 3 failed, each fixed: `\dfrac`'s corpus row twice, and the sidecar start importing the engine) |
| `npm install`, `npm run typecheck` | ok |
| vitest: `bookMathRender.test.ts`, `figureLabels.test.tsx`, `FigureInline`, `figures/sketch`, `src/render` | **10 files, 258 passed** |
| `npm run frontend:build` | ok |
| `apps/learnloop-tauri/sketch-engine/build.py --check` | both reproduced (sketch `7fc76715…` unchanged, book-math `f2b6894c…`) |
| `module_generate.py`, `module_validate.py`, `desktop_generate.py`, `desktop_validate.py` | pass (1154 module notes, 309 + 6 desktop notes) |

Not run, by the brief: no migration and no DB code changed, so no durability lane; nothing under `src-tauri` changed, so no `cargo check`; the schema did not change, so no DB reference.

**Pytest files:** `test_activity_contract_extensions`, `test_ad1_migration`, `test_ad23_contract`, `test_approach_maps_schema`, `test_architecture`, `test_assessment_contracts`, `test_authoring_contract`, `test_batch3_landing`, `test_blind_grading_contract`, `test_cli_attempt`, `test_cli_generate_practice`, `test_cli_help_snapshot`, `test_cli_ingest`, `test_cli_propose`, `test_codex_output_schema`, `test_codex_tool_lockdown`, `test_contract_commissioning`, `test_contract_frontier_coverage`, `test_contract_reachability`, `test_controller_snapshot`, `test_coordinated_migrations`, `test_deferred_regrade`, `test_desktop_rpc_contract`, `test_diagnosis_contract`, `test_document_ir`, `test_evsi_single_family_unbounded`, `test_figure_grammar`, `test_figure_label_wording`, `test_figure_offers`, `test_figure_panels`, `test_figure_predictions`, `test_figure_prefetch_migration`, `test_figure_property`, `test_figure_region`, `test_figure_requests_migration`, `test_figure_revisions`, `test_figure_rich_contract`, `test_figure_rich_failed_correction_durable`, `test_figure_rich_job`, `test_figure_rich_rereview_fixes`, `test_figure_rich_review_fixes`, `test_figure_rich_rpc`, `test_figures_codex_review`, `test_figures_final_round`, `test_figures_fix_round2`, `test_figures_fix_round3`, `test_figures_fix_round4`, `test_figures_fix_round5`, `test_figures_help_codex_review`, `test_figures_help`, `test_figures_migration`, `test_figures_prefetch_boundary`, `test_figures_prefetch`, `test_figures_prefetch_review_fixes`, `test_figures_rpc`, `test_figures_rw5b_fix_round2`, `test_figures_rw5b_review`, `test_figures_scope_redesign`, `test_figures_show_me_codex_review`, `test_figures_show_me`, `test_figures_switch_off`, `test_figure_verification`, `test_followups_batch5_lesson`, `test_followups_batch6_power_probe_cache`, `test_followups_batch6_prefetch_decided_once`, `test_followups_batch6_prefetch_next_section`, `test_followups_batch6_prefetch_plan_wait`, `test_followups_batch6_review_fixes`, `test_followups_batch6_verify_fixes`, `test_followups_batch7_prefetch_capped_resume`, `test_followups_batch7_prefetch_link_served`, `test_followups_nov2_figure_provenance`, `test_glm_ocr`, `test_goal_contracts`, `test_graph_correction`, `test_help_assist_figures_migration`, `test_help_assists_schema`, `test_help_assist_work_md_migration`, `test_hint_contracts`, `test_hypothesis_reference_contract`, `test_ingest_fetchers`, `test_ingest_m3`, `test_judge_routes`, `test_learner_claim_application_migration`, `test_learner_claim_superseded_migration`, `test_learner_data_relax_2`, `test_learner_note_source_kind_migration`, `test_library_asks_migration`, `test_manim_figure_checks`, `test_manim_sandbox_hostile`, `test_mobile_allowlist`, `test_model_call_receipt_owners`, `test_module_catalog_inventory`, `test_notes_never_read`, `test_plan_first_transport_offer_grants`, `test_plan_first_transport_offer_grants_r5`, `test_plan_first_transport_paid_roles`, `test_public_tip_guards`, `test_reader_ca1_as_printed`, `test_reader_ca1_astra_codex_review`, `test_reader_ca1_astra_redesign`, `test_reader_ca1_astra_rereview`, `test_reader_ca1_codex_review`, `test_reader_ca2_fix_orchestrator`, `test_reader_ca2_one_ask`, `test_reader_intentions`, `test_reader_qualified_span_keys`, `test_reader_rw3b_migration`, `test_reader_rw5d_p4a_figures_follow`, `test_reader_rw5d_p4b_teacher_visuals`, `test_reader_rw7a_migration`, `test_reader_source_identity_guard`, `test_reader_tutor_retrieval`, `test_reader_tutor_switch_off`, `test_reading_paths`, `test_regrade_contract_replay`, `test_regrade_contract_successor`, `test_regrade_contract_upgrade`, `test_retrieval_spaces_migration`, `test_router_reader_activity`, `test_rw2d_receipts_migration`, `test_rw5c_book_math`, `test_rw5c_display_twins`, `test_rw5c_judgments`, `test_rw5c_katex_tree`, `test_rw5c_labels`, `test_rw5c_migration`, `test_rw5c_never_evidence`, `test_rw5c_recheck`, `test_rw5c_source_check`, `test_rw5c_switch_off`, `test_section_coverage_migration`, `test_settings_store`, `test_sidecar_contract`, `test_sidecar_serializer_snapshot`, `test_sidecar_teach_back`, `test_sidecar_tutor_qa`, `test_sketch_engine`, `test_sketch_hostile`, `test_sketch_parity`, `test_sketch_sandbox_review`, `test_sketch_service`, `test_sketch_verify`, `test_source_layer`, `test_sqlite_file_copies`, `test_t1_batch_origin_migration`, `test_table_roles`, `test_teach_back_generation`, `test_teacher_te1b_suggestions`, `test_teacher_te1_successor`, `test_tracked_fixture_databases`, `test_tui_feedback`.

## Open questions

- **An `equation` or `math` block with no delimiters** is read whole (§5.2), and the page shows it as plain markdown, not KaTeX. The text is the same symbols, so no false meaning was found, and it was left as the spec has it. If the owner wants the claim only where the page typesets, it is one line in `segments`.
- **`\( … \)` is not read**, though the page renders it. A refusal, so not a defect; an easy P2 row if the coverage report shows them.
