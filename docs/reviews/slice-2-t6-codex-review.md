# Slice 2 T6: Codex review fixes

Branch `slice-2/t6`, worktree `learnanything-t6`. The review covered the T6
commits up to `ea1b0a12` (stage review: `docs/reviews/slice-2-t6.md`). This
file records the fix step: each finding was reproduced first, then fixed (or
rejected with a reason), and the gate was rerun.

## Review

### How the findings were reproduced

- **F1** with the reviewer's script on the unfixed code: `ext_ps/s3` ("Solution
  to Problem 3: … 2 and 3") was the tutor's first span, cited, with
  `withheld_answer_overlap = 0`.
- **A HEAD-compatible repro file** (13 tests, only APIs the unfixed branch has:
  F1, F2, F3, F4 ×2, F6, F7, F8, F9, F10, F13, F14, and the reader byte-identity
  claim) run against an export of `ea1b0a12`: **13 failed**. The same file run
  against the fixed tree: **13 passed**. The permanent tests below cover the
  same scenarios (and more).
- **F5, F11, F12** are reproduced by reading the code: B4's decision had no
  provisional status, `verify.py` duplicated `rerank_pool` line for line, and
  `reader.span_learning_objects` had no Tauri command and nothing rendered
  `suggested_learning_objects`.

### Findings

Code fixes are in `6bf712bd` (its title omits F5, whose provisional status is
in the same commit); regenerated DB/configuration references in `e38f1e51`.

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | The practice/feedback tutor retrieves and cites the item's own worked solution | fixed | `6bf712bd` | `test_source_retrieval_guards.py`: `test_the_items_own_solution_never_reaches_the_tutor` (the review's repro: problem set, `exercise` link, answer "2 and 3"), `test_short_answers_are_measured_in_source_spans`, `test_a_teaching_span_stating_a_short_answer_is_withheld`, `test_the_practice_question_is_never_the_retrieval_query`, `test_practice_and_feedback_drop_exercise_and_solution_blocks`, `test_a_cited_span_overlapping_the_expected_answer_is_debited_as_a_reveal`, `test_linked_spans_without_retrieval_are_not_debited` |
| F2 | Medium | Dense retrieval switches itself off for the whole library after any import | fixed | `6bf712bd` | `test_source_retrieval_search.py::test_a_new_import_leaves_meaning_search_on_for_the_embedded_sources` |
| F3 | Medium | "Enter also searches by meaning" shown when Enter cannot; meaning-only basis mislabelled | fixed | `6bf712bd` | `test_the_typing_search_says_whether_enter_would_search_by_meaning`, `test_sidecar_source_retrieval.py::test_library_search_rpc_ranks_by_keyword_and_says_so`, `searchBasis.test.ts` (4 tests) |
| F4 | Medium | Retrieval before the question row, unbounded, rewrite on Codex by default | fixed | `6bf712bd` | `test_source_retrieval_tutor.py`: `test_the_question_row_is_written_before_retrieval`, `test_an_interrupted_retrieval_keeps_the_question`, `test_a_slow_verification_runs_out_of_time_and_the_tutor_keeps_its_linked_spans`, `test_no_paid_step_starts_after_the_time_box`, `test_the_tutor_does_not_rewrite_questions_by_default` |
| F5 | Medium | B4's decision cannot credit page images by construction | fixed (recorded provisional; the image-label pass is P4's close condition, not built here) | `6bf712bd` | `test_source_retrieval_suites.py::test_b4_compares_page_images_with_text_chunks_and_decides_conservatively` asserts `decision.status == "provisional"`, the bias and the close condition; stage review §5.2 relabelled |
| F6 | Low | Exam spans leak when the exam's current revision is not the pinned one | fixed | `6bf712bd` | `test_an_exam_reimport_is_excluded_whatever_revision_the_set_pins`, `test_a_unit_override_is_resolved_in_every_extraction_by_label` |
| F7 | Low | Assessment links with non-block locators exclude nothing | fixed | `6bf712bd` | `test_an_assessment_link_that_names_no_block_excludes_its_whole_extraction` (heading path, time range, arXiv label, opaque), `test_an_assessment_link_without_an_extraction_excludes_its_sources_extractions` |
| F8 | Low | Rewrite and query embedding paid for before checking verification can run | fixed | `6bf712bd` | `test_nothing_is_paid_for_when_verification_cannot_run` |
| F9 | Low | `sources search --deep` has no `--dry-run` or caps | fixed | `6bf712bd` | `test_source_retrieval_cli.py::test_deep_search_has_a_dry_run_and_caps`, `test_deep_search_caps_bound_the_paid_steps` |
| F10 | Low | `tutor_spans` (up to 8) bypasses the 4-citation bound | fixed | `6bf712bd` | `test_at_most_four_spans_reach_the_tutor` (schema `le=4` and the clamp) |
| F11 | Low | The verification rerank is a parallel copy of `rerank_pool` | fixed | `6bf712bd` | `test_tutor_verification_and_the_practice_rerank_share_one_listwise_judge`; the 69 practice-index tests pass unchanged |
| F12 | Low | The nearest-LO suggestion is not visible in the app | fixed | `6bf712bd` | `AskOverlay.suggestion.test.tsx` (3 tests); Tauri passthrough added (`cargo check` could not run, see Gate) |
| F13 | Low | Non-reader questions don't record which spans the tutor saw | fixed | `6bf712bd` | `test_the_manifest_records_the_span_keys_the_tutor_saw` |
| F14 | Low | The FTS index is tied to the implicit rowid of a composite-key table | fixed | `6bf712bd`, `e38f1e51` | `test_source_block_fts.py::test_a_delete_never_removes_another_blocks_index_row` (renumbered rowid, doctor drift, replayer repair) |
| C1 | claim | "The UI never claims a meaning search that did not run" | fixed with F3 | `6bf712bd` | as F3 |
| C2 | claim | Kill switch "tested for the Quick Add selection" | fixed (test added) | `6bf712bd` | `test_quick_add_with_retrieval_off_plans_exactly_as_before` |
| C3 | claim | Kill switch byte identity per consumer | fixed | `6bf712bd` | `scope_basis` and `suggested_learning_objects` are absent with the switch off: `test_quick_add_with_retrieval_off_plans_exactly_as_before`, `test_with_retrieval_off_reader_answers_carry_no_suggestion_field` |
| C4 | claim | "A candidate that reproduces the expected answer is withheld" | fixed with F1 | `6bf712bd` | `test_a_teaching_span_stating_a_short_answer_is_withheld` |
| C5 | claim | "Only verified spans reach the tutor" (verification promotes the solution) | fixed with F1 | `6bf712bd` | the solution never reaches the verifier (role, role-hint and answer filters); prompt `source_span_verify.v2` also forbids picking a passage that answers the practice question |

No finding was rejected.

### What changed, finding by finding

**F1 (High).** Three independent guards, plus accounting:
1. *The query.* In every tutor context the retrieval query is the learner's
   question alone: `item.prompt` is never appended, and the rewrite (now off
   by default, F4) gets no context. The verifier still sees the practice
   question, so it can tell what "here" means; prompt `source_span_verify.v2`
   tells it never to pick a passage that states the practice question's answer,
   works it out or solves the same problem.
2. *The scope.* `corpus.teaching_exclusions` drops every source-set member, or
   unit override, whose role lacks `semantic_contract` authority
   (`role_authority`: `problem_set`, `exam`, `notes`, unknown), in every tutor
   context, which is what the old semantic-authority links could cite. In
   practice and feedback contexts `teaching_scope(..., item_bound=True)` also
   drops blocks hinted `exercise` or `solution`. Marker hints only a solution's
   lead line ("Solution:", 7 such blocks in the probability copy), so a
   `solution` hint opens a region that takes the following unhinted prose,
   equation, table and figure blocks up to the next section header or
   structural hint, at most 20 blocks (`db.stores.source_block_fts.role_hint_spans`).
3. *The answer.* `tutor_qa.span_answer_overlap` is `answer_leak_overlap` plus
   the short answers it returns 0 for: an expected answer with fewer than three
   content tokens counts as fully exposed when its normalized tokens appear in
   order in the span (`2/13`, `0.154`, `2 and 3`). A lone token must contain a
   digit and have two characters (a lone `3` or `yes` is in every passage by
   accident; that residue is left to the verifier). Spans that leak are withheld
   in practice and feedback contexts, before the verifier sees them.
4. *Reveals.* When retrieval chose the spans, the largest overlap among the
   **cited** spans (the ones the learner can open in the Ask overlay; the
   tutor's prose is scored separately, as before) is debited to `reveal_events`
   as `source_review`, basis `tutor_qa:<context>:cited_source_span`. The kill
   switch path (linked spans) debits nothing new.

**F2.** Option (a) of the fix: `dense.py` decides coverage per extraction and
ranks over the complete ones; status `ready`, `partial` (with the uncovered
block and source counts, and the backfill hint, in the search notes) or
`incomplete`. Coverage is computed without reading vector bytes and cached by
the scope's manifest digest plus a fingerprint of the stored source-block
vectors. A capped ingest-time embed job (option b) was not added: it would
spend owner money on every import, which the default-backfill decision
deliberately avoids. The uncovered count is shown in the reader (F3's label:
"meaning (3 of 4 sources)"), not in doctor: doctor would have to import
`source_retrieval`, which imports `ops`, a cycle the frozen-cycles contract
forbids.

**F3.** The typing response (and the deep one) carries `meaning_search`:
coverage, the embedding switch and a known query-embedding price, all read
without a call. `searchBasisLabel` builds the label from the basis parts that
ranked hits (`keyword`, `meaning`, `rewritten question`, so a meaning-only
deep result reads "· meaning") and shows "Enter also searches by meaning"
only when `meaning_search.status` is `ready` or `partial`.

**F4.**
- `ask_question` inserts the pending question row before retrieval in every
  non-reader context; a failure while building the context marks it `failed`,
  and an interruption (tested with `SystemExit`) leaves it `pending`, never
  absent. The retrieval manifest is written with the answer (or the failure).
- `source_retrieval.retrieval_timeout_seconds` (default 15) time-boxes the
  tutor's retrieval and verification and the deep library search's rewrite and
  query embedding. `PaidCalls.call` gained `deadline`: each attempt's request
  carries the time left as `timeout_seconds` (Codex SDK, Codex HTTP and the
  OpenAI-compatible transports all enforce it), and no attempt starts after it.
  A timed-out verification keeps the linked spans (`verification timed_out`).
- `source_retrieval.tutor_query_rewrite` (default **false**) gates the tutor's
  rewrite; `query_rewrite` now governs only the deep library search.
- Measured on the default-off rewrite with `openai/gpt-4.1-mini` on the
  linear_algebra copy: query embedding 0.82 s, verification 3.1 s, 4.46 s in
  all. **Not measured on Codex** (the unset-route default): the subscription is
  exhausted until 2026-10-18, so the time box is the bound until then.

**F5.** `b4` records `decision.status = "provisional"`, the bias (questions
written from, and both label passes reading, Marker text) and the close
condition: a pass that seeds questions from the rendered page image and labels
(question, page image) pairs with a multimodal judge on the math-heavy pages.
That pass is not built here: the structured-chat transports take text prompts
only, so it needs image input on `StructuredRequest` and the OpenRouter
transport (cross-cutting), then a paid B4 rerun on both copies (about $0.7).
Owner question 1 below.

**F6, F7.** Exclusions resolve by `source_id`: every revision and run of a
member's source. A unit override is matched by unit id in the pinned
extraction and by the pinned unit's label elsewhere (unit ids are positional
`u1…`), including nested units; an override that cannot be resolved excludes
that whole extraction. An assessment link whose locator names no block
(heading path, time range, arXiv label, anything else) excludes its whole
extraction, or its revision's or source's extractions when it names none. The
owner copies have no such links (every `exercise` and
`assessment_alignment` link in the three copies is `block_span_v1`), so this
costs nothing there today.

**F8.** `verify.verification_route` plans the route, applies the skip check and
resolves the client before anything is retrieved; when verification cannot
run the provider returns the linked spans at once (`verification skipped: …` /
`verification unavailable (…)`).

**F9.** `learnloop sources search --deep --dry-run` prints the planned rewrite
(route, billing, tokens, cost, retry) and query embedding (cache-aware, under
the T6 `source_query` record kind) with no call and no write (a read-only
attach that never migrates). `--max-calls` (3), `--max-tokens` (60000) and
`--max-cost-usd` (0.02) put both paid steps under one `SpendBudget`.

**F10.** `tutor_spans` is `le=4`, and `_build_context` clamps provided spans to
`_MAX_CITATION_SPANS`.

**F11.** `practice_index/listwise.py` holds the skip check, request input hash,
per-candidate ledger ids, ledger-served cache, capped call with one retry
(and deadline), pick filtering and append-only verdicts once, parameterized by
a `ListwiseTask` (route task, ledger task and kinds, id prefix, result model,
verdict field, scores, price setting, verdicts whose picks are dropped).
`rerank_pool` and `verify_spans` are thin wrappers; the practice rerank keeps
its statuses, ids and ledger rows (its 69 tests pass unchanged).

**F12.** `reader.span_learning_objects` is a Tauri command
(`readerSpanLearningObjects` in the client), and the Ask overlay renders a
reader answer's `suggestedLearningObjects` as "Nearest learning object (a
suggestion, not a source link): …". There is still no picker to promote under
a suggestion (stage review open question 3).

**F13.** The retrieval manifest records `candidate_keys`, `withheld_keys` and
`span_keys` (record ids, never text), plus `time_box_seconds` and `elapsed_ms`.

**F14.** Migration 175 is edited in place (it is unmerged and will be
renumbered at merge): the delete paths match the block's identity as well as
its rowid, so a renumbered rowid can never delete another block's row, and
the SQL header documents the hazard. Deleting by `(extraction_id, span_id)`
alone was not used: both are `UNINDEXED` FTS5 columns, so every deleted block
would scan the whole index, quadratic on a re-extraction. Doctor reports drift
(`sql:source_block_fts_drift`, stale and missing rows) and names the repair
(`learnloop rebuild-derived-state`); the table note names the hazard.
`fixtures/migration_head_175` was rebuilt from the 174 head with the edited
migration (rollback mode, `integrity_check` ok, `foreign_key_check` empty). The
fixtures-local copies keep the old triggers; they are disposable.

### Configuration

`[source_retrieval]` gains `tutor_query_rewrite` (false) and
`retrieval_timeout_seconds` (15, at most 120); `tutor_spans` is at most 4. All
three defaults snapshots were recomputed (recorded in `config/template.py`);
the configuration reference now has 633 leaves.

### Real calls (fixtures-local copy `t6_linear_algebra`, OpenRouter)

Dry run first; the app loaded the key itself.

| Run | Calls | Tokens (in / out) | Billed |
|---|---|---|---|
| Tutor retrieval, practice context, rewrite off (default): query embedding + verification v2 with the per-request timeout | 2 | 41 / 0; 1,290 / 372 | $0.0000004 + $0.0011112 |
| `sources search --deep --dry-run` | 0 | — | $0 (planned $0.0094 worst case) |
| `sources search --deep` with the default caps: rewrite + query embedding | 2 | 291 / 149; 179 / 0 | $0.0003548 + $0.0000018 |
| **Total** | **4** | | **$0.0015** |

Both verify the changed interfaces: OpenRouter accepts the per-request
timeout, and the v2 prompt verified 12 candidates (2 answers, 7 related,
3 unrelated) and picked 4.

### Gate

Run on `e38f1e51` (the fixes plus regenerated references), after
`uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`.

| Check | Result |
|---|---|
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7936 passed**, 0 failed, 0 skipped (231.8 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **84 passed**, 7852 deselected (61.7 s) |
| `npm install`, `npm run typecheck`, `npm test` (apps/learnloop-tauri) | up to date; typecheck clean; 25 files, **109 tests passed** |
| `db_generate_reference.py`, `db_validate_reference.py` | regenerated; validator `errors: []` (schema head 175, 292 table notes, 633 config leaves, 3832 wikilinks) |
| `cargo check --manifest-path src-tauri/Cargo.toml` (not a gate item) | could not run: the machine's `rustc` fails to start (`librustc_driver` symbol lookup error), unrelated to this change; the Rust edit is one `sidecar_passthrough!` line and its registration, copying the neighbouring `reader_search_sources` |

The pytest runs added `-p no:cacheprovider` (no `.pytest_cache` writes); the
selection is unchanged. Since the stage gate: 30 new Python test items
(7906 → 7936; two existing search tests updated in place) and 3 new vitest
tests (106 → 109; the four `searchBasis` tests rewritten).

### Owner questions

1. **Close P4?** Build the image-label pass (image input on the structured-chat
   transport, a multimodal judge, a B4 rerun on both copies, about $0.7), or
   leave page images off with the decision marked provisional.
2. **Tutor latency on Codex.** Unmeasured until the subscription resets
   (2026-10-18). The 15 s time box bounds it; route `source_rerank` to a fast
   metered model if Codex verification usually runs out of time.
3. **Lone-token answers** (`3`, `yes`, a single word) cannot be told apart from
   incidental mentions lexically; for them the verifier's instruction is the
   only guard.
