# Reader CA3: compare from anywhere (stage `reader-ca3-compare-anywhere`)

Branch `reader/ca3-compare-anywhere` (worktree `learnanything-merge2`), base `main` at
`1bcde2096` (migration head 226, latest algorithm mvp-0.37). Spec:
`docs/specs/ux_reader_compare_ask_v1.md` §4 (all), §9 X1 and X2, §11 K12, §12.2 (the
`reader.library_compare` and `compare_sources` requests and the `compare_scope` task), §13's
CA3 row and its kill switch, §15 Q13 and Q15 (owner decisions 2026-10-25).

**No migration. No successor. No paid call was made** (every model in the tests is a fake;
nothing outside pytest called a route). Comparisons stay display and retrieval: no scoring,
scheduling, projection, serving or replay path reads anything CA3 writes (a `library_asks`
row, `judgment_ledger` rows of task `compare_scope`, model-call receipts, the salience-only
`compare_opened` event with its door). The successor ruling of §13 holds unchanged.

## 1. What was built

### One request, four doors (§4.1, K12, C1)

`reader.library_compare` takes one request shape from every door:

| Field | Meaning |
|---|---|
| `door` | `selection` · `ask_box` · `tutor_offer` · `library_answer` · `refine` · `pins` |
| `askId` | a library answer's ask (or the comparison's own row, for chips and refine); absent: the door opens its comparison's row |
| `question` | the comparison's words, for a door with no ask (never accepted together with `askId`) |
| `extractionId`, `anchorSpanIds` | the anchor: the passage the comparison is about |
| `sourceIds` | the books named or chosen: they only narrow |
| `pinnedSpanKeys` | pins (optional; `pins` needs two, as today) |
| `openSourceId`, `requestedPerspectives`, `workbenchSessionId` | as today |
| `toolCallId` | the tutor's offer this comparison answers (kept on the row's manifest) |

The frontend builds every door's payload through one function (`comparePayload`, same keys
whatever the door). The policy is never the client's: a door with no ask opens its
comparison's own `library_asks` row (`LA.open_comparison`: no retrieval, `entry = "reader"`,
`manifest.comparison_only`, `manifest.door`, the caller the server derives from the open
book and the workbench session), and every follow-up is bound by that row's caller as any
ask's is (RW4a's F4). Held-out material and an exam-material anchor are refused before a
row is opened or anything is read.

| Door | What the learner does | Request |
|---|---|---|
| Selection verb | the palette's Transfer *how do my other books treat this?* (next to *where else is this explained?*, Q15 keeps both), or words in the intent box the router sends there | `selection`, question = the typed words or the selection, anchor = the selection, no books named: every other book |
| Ask box | `Ctrl+Shift+F` in the Reader, *⇧↵ ask your library* on the library page | `reader.compare_scope` first; a comparison runs at once as `ask_box` with the named books and the topic; a library question is today's answer |
| Tutor's offer | *how do your books treat this?* under a Reader answer | `tutor_offer`, question = the tutor's request, anchor = the passage the question was asked on, `toolCallId`; the offer then reads *compared beside the book ▸* |
| Library answer | *compare these books ▸* (new), or pins and *compare pinned* (kept) | `library_answer` with the answer's books, no pins; or `pins` |

The comparison lands in the comparing posture through today's table (`CompareTable`, one row
per source; the anchor's book first, headed *your passage*). CA4 redraws it by point and
shares this request.

### `compare_sources` (§12.2; sources spec §9.4, its as-built note)

- `anchor_span_keys`: the anchor passes the pins' filters (exam material, the scope, an
  answer-reproducing passage in practice); one that fails is listed under *left out* with
  its reason. One that passes is its book's passage without a verification call (the
  learner chose it), compared first (`entry.anchor = true`), and its book is not searched
  again.
- `source_ids`: only narrow. A book outside the caller's scope is refused
  (`scope_refused`) before anything is read or paid for. With named books, only those (and
  the anchor's) are verified and compared; the other in-scope books with a keyword passage
  on the question are listed under *also discussed in (not compared)*, unchecked and never
  sent to a model (Q13).
- Without either argument the call, its manifest and its stored comparison are exactly
  today's (pinned).

### `compare_scope`, the Decider task (§4.3, §4.4, §12.2)

`src/learnloop/source_retrieval/compare_scope.py`, route `ai.routing.compare_scope`
(decider-only: unset is the code-default `openrouter_decider` profile, never a chat fallback
and never `LEARNLOOP_AI_PROVIDER`; added to `DECIDER_TASKS` and disclosed in Settings'
decision models). One request of typed questions over the books the caller's comparison may
read (titles and file names; a source that is exam material whole is never listed):

- `intent`: ask box `compare` | `ask`; refine box `books` | `views`;
- `book:<ref>`: one yes/no per book (a multi-select);
- `topic` (ask box): a choice over the contiguous spans of the learner's own words (plus
  "all of the words"), so the topic is always the learner's words with the book names and the
  asking words left out, never model text;
- `unmatched`: a span naming a book that is not in the list, or none (*"Hoffman" isn't in
  your library*);
- `change` (refine box): add | only | remove.

Pressed only (Enter), never while typing, and only for the ask box and the refine box (the
other doors know their scope, so no reading is paid for). An empty text makes no call. An
unavailable, timed-out, spent-out, tied or failing Decider, or a day at its cap, reads
nothing. Every reading is one `judgment_ledger` row (task `compare_scope`, judge `decider`,
the words only as the input hash); the learner's change of the chips (`×`, *+ add a book*)
and *change* (reword) are `learner_card` rows superseding it, so the reading's error rate
(§14's "named-book readings corrected with change") is measurable without a chore.

RPCs (new, desktop only, pinned in `tests/test_mobile_allowlist.py`, Tauri passthroughs
added): `reader.compare_scope` (a library job; never on the request path) and
`reader.compare_scope_correction`.

### The frontend

- `CompareScope.tsx`: `ScopeLine` (*→ comparing · your passage · [Axler ×] [Strang ×] + add a
  book · on: eigenvalues · change*, and the unmatched line; names, never counts), `AddBook`
  (type-ahead over the library's books, `↵` adds the first match, `Esc` closes),
  `RefineBox` (`/`; books change the chips, a view becomes a requested perspective while
  `reader_compare.keep_enabled` allows them), and `CompareScopeView` (a comparison with no
  library answer: the line, the table, keep, *previous ▸* for the earlier table, the tutor
  about this comparison with `Ctrl+↵` over the compared passages, *practice this ▸*).
- `useLibraryAsk.ts`: `comparePayload`, `askBox`, `compareFrom`, `compareBooks`,
  `compareAll`, `setBooks`, `reword`, `refine`, `retryCompare`; the tutor and *practice
  this* work on a comparison with no ask. The ask box's reading shows *◐ reading which books
  you named…*.
- `LibraryAnswer.tsx`, `LibraryPane.tsx`, `ReaderScreen.tsx`, `TutorOffers.tsx`,
  `TutorAnswer.tsx`: the doors' wiring. While working (the Reader's working posture) the
  tutor's offer keeps today's inline table, since the comparing posture is not shown there.
- Nothing takes focus on landing or animates; the picker and the refine box take the cursor
  only on the learner's own press (K16).

### The kill switch

`[reader_compare] scope_enabled = true` (with `reader_compare.enabled`,
`source_service.compare` and the library answer). Off, exactly today: the RPC validates as
RW4a's/RW4d's pinned request (an ask and two pins; every CA3 field refused as unknown), the
prompt contract has no `libraryAsk.compareScope`, the palette has no `compare_books` and the
intent router's question set is unchanged, `reader.compare_scope*` refuse, and every door is
today's (pinned in pytest and vitest).

The intent router's options gain one action while on, so its routings name their own question
set (`<base>+compare-books`); off, the set (and every routing's input hash) is the one before.

## 2. Parameters (no made-up constants, owner 2026-10-24)

Classified in `src/learnloop/params/parameter_registry.py`:

- `reader_compare.scope_enabled`: a kill switch.
- `reader_compare.scope_timeout_seconds = 4.0` (`keep`: a latency guardrail, the intent box's).
- `reader_compare.scope_max_calls_per_day = 200` (`keep`: a spend guardrail; about $0.0004 a
  request at the listed price, reserved before sending exactly as `reader_intent`'s).

No decision threshold was added: every choice takes its argmax (a tie decides nothing), and a
book is named when P(yes) beats P(no) (the argmax of its two answers). The bounds on the
request (at most 124 books named in one request, a topic read from the first 21 words) come
from the decision API's own limits (128 questions, 255 options): structural, computed from
those constants, not tuned.

The defaults snapshot moves only because the effective config gains the keys and the route:
all 28 `DEFAULTS_SNAPSHOT_BY_ALGORITHM` values were recomputed from the composed defaults
(`defaults_fingerprint_for_version`) with one comment per version. The DB/config reference
was regenerated (1,069 leaves) and validated (`errors: []`).

## 3. Deviations and open points

1. **The Decider unavailable in the ask box.** §4.3 says the comparison then runs over every
   book with the words as the query. Built instead: the ask box answers as today's library
   ask (sources first, cheap) and offers *couldn't read which books you named · compare all
   your books on "…" ▸*, one press away. A down Decider would otherwise turn every library
   question into a paid comparison the learner did not ask for. Owner question below.
2. **The intent box's routed line** stays the router's (*Transfer · how do my other books
   treat this?*); the chips (X1's *your passage · Axler · Lay · on: …*) are on the comparing
   pane's line, shown at once. X1's *change* on a selection-started comparison (reopening the
   intent box) is not built.
3. **The tutor's offer** anchors on the passage the question was asked on (the exchange's
   span), not on one of the answer's citations: it is always in scope as the question's own
   passage, and a citation in another book would move the anchor away from the reader.
4. **Pending** is one line (*◐ finding each book's passages, then lining them up…*), not
   §4.2's two stages with excerpts in a provisional *by book* layout: the job has no progress
   signal today, and that layout belongs to CA4's table.
5. **`MAX_PERSPECTIVES` as a `keep` config key** (§12.2) is CA4's (perspectives as rows); not
   touched here.
6. **No real Decider call** verified the request (launch rule: no live calls). The request is
   built only from the typed question classes, so the API's contract holds by construction; a
   minimal paid check on a backup copy is cheap if the owner wants one before the landing.

## 4. Gate (this step; the full suite runs once at the landing)

All commands inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2`: done.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n 6` over the 83 files below: **1587 passed, 10 skipped,
  3 xfailed** (0 failed).
- Frontend (`apps/learnloop-tauri`): `npm install`; `npm run typecheck`: **clean**;
  `npx vitest run --maxWorkers=4 src/screens/reader src/screens/ReaderScreen`: **87 files,
  814 passed**; `npm run frontend:build`: **built**.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: **finished, no
  errors** (two passthroughs added).
- DB/config reference: `db_generate_reference.py` then `db_validate_reference.py`:
  **`errors: []`** (run under `env -i` with empty HOME/CODEX_HOME/LEARNLOOP_CONFIG_DIR).
- No migration, so no durability lane.
- Not in this gate, for the record: the module and desktop reference validators
  (`module_validate.py`, `desktop_validate.py`) already fail on the base (over 1,100 module
  notes missing; `src/components/pdfSelection/testing/syntheticBook.ts` unclassified), before
  any CA3 file; neither was regenerated here.

Pytest files run (new: `test_reader_ca3_compare_anywhere.py`; changed: `test_judge_routes`,
`test_mobile_allowlist`, `test_reader_intentions`, `test_compare_keep_switch_off`,
`test_rw4_kill_switches`, `test_figures_show_me`, `test_reader_tutor_switch_off`,
`test_reading_paths`, `test_figures_switch_off`):

```
tests/test_reader_ca3_compare_anywhere.py tests/test_judge_routes.py tests/test_mobile_allowlist.py
tests/test_reader_intentions.py tests/test_compare_keep_switch_off.py tests/test_rw4_kill_switches.py
tests/test_figures_show_me.py tests/test_reader_tutor_switch_off.py tests/test_reading_paths.py
tests/test_figures_switch_off.py tests/test_compare_sources.py tests/test_compare_sources_keep.py
tests/test_reader_compare_table.py tests/test_library_ask.py tests/test_library_ask_review.py
tests/test_library_ask_expand.py tests/test_reader_intent.py tests/test_reader_rw1b_final_verify.py
tests/test_reader_rw1b_fix_round4.py tests/test_reader_rw1b_rereview.py tests/test_reader_rw1b_review.py
tests/test_reader_reconstruct.py tests/test_rw4d_rw3b_composition.py tests/test_reader_tutor_offers.py
tests/test_library_exercises.py tests/test_sources_merge_composition.py
tests/test_source_service_spend_envelopes.py tests/test_retrieval_interventions_write_points.py
tests/test_reader_find_sources_callers.py tests/test_tutor_tool_requests.py tests/test_e0_review_round2.py
tests/test_find_sources_intents.py tests/test_tool_registry.py tests/test_tool_results_withhold_answers.py
tests/test_tools_cli.py tests/test_practice_proposal_caller_columns.py tests/test_figure_offers.py
tests/test_figures_rw5b_fix_round2.py tests/test_figures_rw5b_review.py tests/test_figures_show_me_codex_review.py
tests/test_passage_links.py tests/test_plan_first_transport.py tests/test_plan_first_transport_paid_roles.py
tests/test_plan_first_transport_offer_grants.py tests/test_plan_first_transport_offer_grants_r5.py
tests/test_roles_judges.py tests/test_roles_switch_off.py tests/test_source_space_resolver.py
tests/test_decider_client.py tests/test_decider_landing.py tests/test_facet_identity_composition.py
tests/test_figure_predictions.py tests/test_figure_region.py tests/test_figure_revisions.py
tests/test_figures_rpc.py tests/test_help_assists_schema.py tests/test_hint_service.py
tests/test_probability_prep.py tests/test_reader_dialogue.py tests/test_reader_inquiry_kill_switch.py
tests/test_router_r2b_requests.py tests/test_router_r2b_serving.py tests/test_sidecar_reader.py
tests/test_reader_ca1_as_printed.py tests/test_reader_ca2_one_ask.py tests/test_intent_codex_rereview.py
tests/test_ad23_successor.py tests/test_ad23_t1_routes.py tests/test_attempt_content_state_successor.py
tests/test_batch3_landing.py tests/test_config_refactor.py tests/test_registry_audit.py
tests/test_architecture.py tests/test_learner_report_superseded.py tests/test_sidecar_serializer_snapshot.py
tests/test_desktop_rpc_contract.py tests/test_table_roles.py tests/test_coordinated_migrations.py
tests/test_tracked_fixture_databases.py tests/test_cli_help_snapshot.py tests/test_rebuild_equivalence_review.py
tests/test_lp_claim_fixes.py tests/test_teacher_te0_review_fixes.py
```

Vitest: new `src/screens/reader/compareScope.test.tsx` (11 tests: the selection verb, the ask
box's chips and unmatched line, `×` and *+ add a book* with the learner's correction,
*change*, refine and *previous ▸*, a library question and the failed reading's offer,
*compare these books*, the tutor's offer, switch off (ask box and palette), door parity);
changed `libraryAskSwitchOff.test.tsx` (its library-off palette also drops the CA3 verb) and
the shared fixture `src/fixtures/readerIntentContract.ts` (regenerated from the sidecar's
palette; `test_reader_intentions` pins it). The run covered every file under
`src/screens/reader` and `src/screens/ReaderScreen*.test.tsx`.

**For the landing:** the switch-off goldens recorded before CA3
(`compare_keep_switch_off`, `reader_tutor_switch_off`, `figures_switch_off`,
`reading_paths_base_a76c8358a`) now turn CA3 off or strip its two additions
(`libraryAsk.compareScope`, the `compare` palette action), as RW5a's and RW7a's did. CA5a
runs beside this stage in another worktree: expect a merge in `ReaderScreen.tsx`,
`LibraryAnswer.tsx` and the 28 defaults fingerprints (recompute them on the merged tree).

## 5. Owner questions

1. With the Decider unavailable, should the ask box run the paid comparison of every book at
   once (§4.3 as written), or keep the built behaviour (today's library answer plus *compare
   all your books on "…" ▸*, one press)? Recommended: keep the built behaviour.
