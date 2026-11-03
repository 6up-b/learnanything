# Reader RW5c P1, KaTeX tree: Codex review record

Review on `gpt-6.1-sol`, job `20261102-225331-8e48uQ`, of the stage in `reader-rw5c-p1-katex.md`. One finding.

## Findings

| Id | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Hidden Markdown equations can certify a curve that contradicts the page | fixed | `677db66481`, `47e8b002ea` | `test_rw5c_source_check.py::test_an_equation_the_page_does_not_show_never_certifies_the_curve` (9 forms), `bookMathRender.test.ts` (corpus and a 1,500-block generator against the real `MarkdownMath`) |

## F1

**Reproduced first.** On `b2f3a7b536`, through the real KaTeX reader and the real sandbox on a synthetic vault, a figure defining `f = x` was `checked` against each of nine blocks whose page shows only `f(x)=2x`: a reference definition, a link title, a double-backtick span, indented code, an unreferenced footnote, an image's alt text, an HTML attribute, an HTML comment, struck-through math. All nine tests failed with `outcome='checked'`; the other nine (a figure of `2*x` is checked against the shown equation) passed. All eighteen pass now.

**The fix is the class, not the nine forms.** This is the third round on "our reader of the source disagrees with the page", and the second on segments, so per the stuck-loop rule it is structural, the same move as KaTeX's tree:

- `apps/learnloop-tauri/src/render/markdownPipeline.ts` holds `normalizeMathDelimiters` and the remark plugins, and `MarkdownMath` imports them from there.
- `src/render/pageMathSegments.ts` runs `unified`, `remark-parse`, those plugins and `remark-rehype` with react-markdown's options, to the tree `rehype-katex` walks. A candidate is a `code` element with `math-inline` or `math-display`, its text is what the page gives KaTeX, and `display` is how the page renders it. Offsets come from the parser's positions, through a map the normalizer now returns, as code points.
- `sketch-engine/markdown/build.mjs` bundles that with esbuild to `page-markdown.js`: 168,618 bytes of ASCII text from 62 packages at `package-lock.json`'s versions, with their licences in `markdown/LICENSES.txt`. `remark-parse`, `remark-rehype` and `unified` are now named devDependencies (the lock's packages did not move).
- `katex_tree.Trees.page_math` runs it in the same sealed engine as KaTeX; `book_math.segments` holds no Markdown or delimiter regex any more. If it cannot run or goes over a cap: `engine_unavailable` or `too_long`, no fallback.
- `CERTIFICATION_VERSION` is 4 and `READER_VERSION` is `book-math-v4+katex-0.16.47+markdown-29fd5be75b4e`, so a stored version-3 `checked` is neither delivered nor skipped by a recheck.

**Page text.** `read_candidates` now finds segments on `sanitize_source_text`'s output, which is what the page gets, and still refuses a block it changes.

**Held to the page.**

- `bookMathRenderCorpus.json`'s `blocks` grew from 13 to 36; each runs through the real `MarkdownMath`, through `pageMathSegments`, and in pytest through the sealed engine under QuickJS.
- A seeded generator in vitest wraps equations in 30 Markdown contexts, nested, for 1,500 blocks: the exact text of every element the page renders equals the reader's. Struck-through math and a ```` ```math ```` fence are shown and on purpose not read, so the corpus pins those and the generator leaves them out.
- A vitest rebuilds the bundle and compares bytes, licences and lock; pytest pins digest, package versions, one copy of each package, and a changed file failing closed. `test_a_katex_or_markdown_bump_…` fails until `CERTIFICATION_VERSION` moves with the bundle.

**Three behaviours moved, on purpose.**

1. **An `Equation` block without delimiters holds no candidate.** The page shows it as plain text through Markdown (`MarkdownMath` knows no block types), so nothing KaTeX shows backs the reading: `x^ab` would read as `x^a b` under text showing `x^ab`. Coverage: 6 such blocks, 0 read. Spec §5.2 records it.
2. **`\(…\)` is read**, because the page renders it. The earlier "left unread" was the regex's limit, not a decision. Coverage: none gained.
3. **Struck-through math and a `math` fence are refused**: the first because no book states an equation it strikes out, the second to keep one shape of candidate.

**The engine's work budget moved, the one thing beyond the finding's text.** Under a sketch's 16 ticks a call, the pipeline ran out at about 700 characters: 14 of 414 blocks with math, holding 7 of the readable equations, would have been `too_long`. So the book-math variant is rebuilt with `-DSK_TICKS_PER_CALL=512u` (`KT.BOOK_MATH_TICKS_PER_CALL`, a `keep` bound). The reasoning: this budget exists so a model's sketch keeps a frame, and this engine runs only pinned programs over book text at check time. Memory cap, stack, serialize ticks, deny-all WASI and wasmtime's backstops are unchanged.

| Measure (carson, wasmtime) | Result |
|---|---|
| `build.py --check` | `reproduced sketch-engine: 7fc76715…` (unchanged, so no stored sketch re-verifies), `reproduced book-math: 880bf1c8…` |
| Load KaTeX and the bundle | about 35 ms after compile; with compile 140 ms |
| A block | about 1 ms |
| 6,000 characters with 82 math elements | 88 ms, fits |
| 12,000 characters, 5,000 `> `, 20,000 `[`, 20,000 `*a ` | `too_long`, 170–260 ms, engine reads on |
| Longest block with math in the coverage corpus (5,879) | fits; no block hit a cap |

## Coverage (§12), re-measured

Code only, counts only, under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`, on the upgraded copies already under the gitignored `fixtures-local/rw5c-katex-coverage/`, opened read-only. No model client, no socket, $0.

| Vault | Blocks | Blocks with math | Health ok / not | Segments | Read |
|---|---|---|---|---|---|
| `linear_algebra` | 1074 | 194 | 194 / 0 | 398 | 46 |
| `probability` | 579 | 164 | 163 / 1 | 253 | 25 |
| `arxiv_v2` | 4717 | 57 | 57 / 0 | 235 | 16 |
| **Total** | 6370 | 415 | 414 / 1 | **886** | **87** |

Before this fix: 895 segments, 91 read. **All 4 lost are in blocks holding `$$a$$$$b$$`, which the page shows as one element KaTeX refuses, in red.** The old regex read them as two good equations, so these were real false readings in the owner's own books, and F1's class reached further than the review's examples. `not_rendered` goes 3 → 12 for the same reason. Nothing else was lost or gained, and all 87 agree with KaTeX's MathML.

## Gate

Every test command in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, pytest at `-n 6`, vitest at `--maxWorkers=4`, one at a time, `TMPDIR` outside the worktree. Scripts outside pytest under `env -i` with empty, existing homes. No live calls, no model client, no spend. No migration, no schema change, nothing under `src-tauri`. Full suite, whole durability lane and whole vitest are the landing's.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | **42 kept, 0 broken** |
| targeted pytest, 153 files (list below) | **3736 passed, 6 skipped** |
| `npm install`, `npm run typecheck` | ok |
| vitest: `bookMathRender.test.ts`, `figureLabels.test.tsx`, `FigureInline`, `figures/sketch`, `src/render`, `ItemPresentation.test.tsx` | **11 files, 324 passed** |
| `npm run frontend:build` | built |
| `sketch-engine/markdown/build.mjs --check` (also in vitest) | reproduced `29fd5be7…` |
| `sketch-engine/build.py --check` | both reproduced |
| `desktop_generate`, `module_generate`, `desktop_validate`, `module_validate` | regenerated (311 TS notes, 1154 module notes); valid, with `desktop_validate`'s inventory pins moved for the two new files (311 sources, 300 entry-reachable, 7 vitest-support) |

**Targeted pytest files:**

```
tests/test_activity_contract_extensions.py tests/test_ad1_migration.py tests/test_ad23_contract.py 
tests/test_approach_maps_schema.py tests/test_architecture.py tests/test_assessment_contracts.py 
tests/test_authoring_contract.py tests/test_batch3_landing.py tests/test_blind_grading_contract.py 
tests/test_cli_attempt.py tests/test_cli_generate_practice.py tests/test_cli_help_snapshot.py 
tests/test_cli_ingest.py tests/test_cli_propose.py tests/test_codex_output_schema.py 
tests/test_codex_tool_lockdown.py tests/test_contract_commissioning.py 
tests/test_contract_frontier_coverage.py tests/test_contract_reachability.py 
tests/test_controller_snapshot.py tests/test_coordinated_migrations.py tests/test_deferred_regrade.py 
tests/test_desktop_rpc_contract.py tests/test_diagnosis_contract.py tests/test_document_ir.py 
tests/test_evsi_single_family_unbounded.py tests/test_figure_grammar.py tests/test_figure_label_wording.py 
tests/test_figure_offers.py tests/test_figure_panels.py tests/test_figure_predictions.py 
tests/test_figure_prefetch_migration.py tests/test_figure_property.py tests/test_figure_region.py 
tests/test_figure_requests_migration.py tests/test_figure_revisions.py tests/test_figure_rich_contract.py 
tests/test_figure_rich_failed_correction_durable.py tests/test_figure_rich_job.py 
tests/test_figure_rich_rereview_fixes.py tests/test_figure_rich_review_fixes.py tests/test_figure_rich_rpc.py 
tests/test_figures_codex_review.py tests/test_figures_final_round.py tests/test_figures_fix_round2.py 
tests/test_figures_fix_round3.py tests/test_figures_fix_round4.py tests/test_figures_fix_round5.py 
tests/test_figures_help_codex_review.py tests/test_figures_help.py tests/test_figures_migration.py 
tests/test_figures_prefetch_boundary.py tests/test_figures_prefetch.py 
tests/test_figures_prefetch_review_fixes.py tests/test_figures_rpc.py tests/test_figures_rw5b_fix_round2.py 
tests/test_figures_rw5b_review.py tests/test_figures_scope_redesign.py 
tests/test_figures_show_me_codex_review.py tests/test_figures_show_me.py tests/test_figures_switch_off.py 
tests/test_figure_verification.py tests/test_followups_batch5_lesson.py 
tests/test_followups_batch6_power_probe_cache.py tests/test_followups_batch6_prefetch_decided_once.py 
tests/test_followups_batch6_prefetch_next_section.py tests/test_followups_batch6_prefetch_plan_wait.py 
tests/test_followups_batch6_review_fixes.py tests/test_followups_batch6_verify_fixes.py 
tests/test_followups_batch7_prefetch_capped_resume.py tests/test_followups_batch7_prefetch_link_served.py 
tests/test_followups_nov2_figure_provenance.py tests/test_glm_ocr.py tests/test_goal_contracts.py 
tests/test_graph_correction.py tests/test_help_assist_figures_migration.py tests/test_help_assists_schema.py 
tests/test_help_assist_work_md_migration.py tests/test_hint_contracts.py 
tests/test_hypothesis_reference_contract.py tests/test_ingest_fetchers.py tests/test_ingest_m3.py 
tests/test_judge_routes.py tests/test_learner_claim_application_migration.py 
tests/test_learner_claim_superseded_migration.py tests/test_learner_data_relax_2.py 
tests/test_learner_note_source_kind_migration.py tests/test_library_asks_migration.py 
tests/test_manim_figure_checks.py tests/test_manim_sandbox_hostile.py tests/test_mobile_allowlist.py 
tests/test_model_call_receipt_owners.py tests/test_module_catalog_inventory.py tests/test_notes_never_read.py 
tests/test_plan_first_transport_offer_grants.py tests/test_plan_first_transport_offer_grants_r5.py 
tests/test_plan_first_transport_paid_roles.py tests/test_public_tip_guards.py 
tests/test_reader_ca1_as_printed.py tests/test_reader_ca1_astra_codex_review.py 
tests/test_reader_ca1_astra_redesign.py tests/test_reader_ca1_astra_rereview.py 
tests/test_reader_ca1_codex_review.py tests/test_reader_ca2_fix_orchestrator.py 
tests/test_reader_ca2_one_ask.py tests/test_reader_intentions.py tests/test_reader_qualified_span_keys.py 
tests/test_reader_rw3b_migration.py tests/test_reader_rw5d_p4a_figures_follow.py 
tests/test_reader_rw5d_p4b_teacher_visuals.py tests/test_reader_rw7a_migration.py 
tests/test_reader_source_identity_guard.py tests/test_reader_tutor_retrieval.py 
tests/test_reader_tutor_switch_off.py tests/test_reading_paths.py tests/test_regrade_contract_replay.py 
tests/test_regrade_contract_successor.py tests/test_regrade_contract_upgrade.py 
tests/test_retrieval_spaces_migration.py tests/test_router_reader_activity.py 
tests/test_rw2d_receipts_migration.py tests/test_rw5c_book_math.py tests/test_rw5c_display_twins.py 
tests/test_rw5c_judgments.py tests/test_rw5c_katex_tree.py tests/test_rw5c_labels.py 
tests/test_rw5c_migration.py tests/test_rw5c_never_evidence.py tests/test_rw5c_recheck.py 
tests/test_rw5c_source_check.py tests/test_rw5c_switch_off.py tests/test_section_coverage_migration.py 
tests/test_settings_store.py tests/test_sidecar_contract.py tests/test_sidecar_serializer_snapshot.py 
tests/test_sidecar_teach_back.py tests/test_sidecar_tutor_qa.py tests/test_sketch_engine.py 
tests/test_sketch_hostile.py tests/test_sketch_parity.py tests/test_sketch_sandbox_review.py 
tests/test_sketch_service.py tests/test_sketch_verify.py tests/test_source_layer.py 
tests/test_sqlite_file_copies.py tests/test_t1_batch_origin_migration.py tests/test_table_roles.py 
tests/test_teach_back_generation.py tests/test_teacher_te1b_suggestions.py 
tests/test_teacher_te1_successor.py tests/test_tracked_fixture_databases.py tests/test_tui_feedback.py 
tests/test_desktop_activation_audit.py
```
