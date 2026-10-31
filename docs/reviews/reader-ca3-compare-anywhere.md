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

## Landing onto main (2026-10-31)

Landed in `learnanything-merge2` on `reader/ca3-compare-anywhere` (stage tip `d7850780b`, base `1bcde2096`) by
merging `main` `6d8f02f3d`: the Oct 27 follow-ups, the docs-only RW5c design spec, the cold-retry successor
mvp-0.38 and Reader CA5a. Main was neither fast-forwarded nor pushed. No migration and no successor: CA3 stays
display and retrieval at every version.

### Commits and conflicts

| Commit | What |
|---|---|
| `4267e5ab7` | `--no-ff` merge of `main` `6d8f02f3d`. **Conflicts:** `useLibraryAsk.ts`. CA3's one-request `runCompare(key, request)` is kept. CA5a's pins compare is renamed `runPinsCompare` and is what CA5a's `run` reaches through its ref; while scope is on it goes through CA3's `pins` door, otherwise it is RW4a's/RW4d's call. `run` takes CA5a's `intent`, then CA3's `extra` state, and CA3's `compareFrom` and `askBox` states carry `intent: ask`. Other conflicts: `api/client.ts` (CA5a's RPCs, CA3's tutor signature); the as-built notes in `ux_reader_compare_ask_v1.md` (both kept); `template.py`, every default snapshot mvp-0.9 … mvp-0.37, where both notes are kept and mvp-0.38 gains CA3's line. **All 29 fingerprints** (mvp-0.9 … mvp-0.38) were recomputed with `defaults_fingerprint_for_version`, the template `.pyc` was cleared, and a recheck found 0 mismatches. The switch-off contract pins (`test_compare_keep_switch_off.py`, `test_reader_tutor_switch_off.py`, `test_reading_paths.py`) now turn off or strip **both** CA3's and CA5a's additions, as `test_figures_switch_off.py` already did. In the mobile allowlist both CA5a's and CA3's RPCs are desktop-only. 432 generated reference notes were taken from main and regenerated in the next commit. `ReaderScreen.tsx`, `LibraryAnswer.tsx`, `dto.ts`, the parameter registry and `schema.py` auto-merged. |
| `0d97773d6` | DB/config reference regenerated on the merge. The hand-written counts in `Configuration.md` and `Database.md` move to **1071 effective leaves in 75 sections** (main's 1067 + CA3's 4). `db_validate_reference.py`: **errors []**; `validate_vault.py` passes (1163 notes). |
| `f81ce3d0b` | Interaction (i) in the frontend and the interaction tests (below). |

`git diff main` lists no binary, no tracked database and nothing under `fixtures-local/`; `.gitignore` is unchanged.

### Interactions with CA5a

**(i) Compare on a found section.** With CA3 on, `ReaderScreen.compareFoundSection` now sends CA3's one request
through the selection door: `compareFrom({door: "selection", question: <section title>, anchorSpanIds: [the
passage in view in this section, else its first], sourceIds: [the hit's book], openSourceId})`. No library answer
is asked first. CA3's door refuses pins without an ask, so the hit's book finds its own passage by discovery,
narrowed to that book, instead of being pinned. A retry after a failure reruns that request as it was (anchor and
book kept). With CA3 off, CA5a's library-ask path is unchanged: an ask anchored on the section, both passages
pinned. Its retry and personalization chip keep the pins (F5/F8), and if the hook's `compareWith` runs while CA3
is on, its comparison goes through CA3's `pins` door with the same pins. New vitest tests:
`findSectionReader.test.tsx` (CA3 on: the request shape, no library ask, no notes; **mutation-checked**, it
fails with the branch disabled) and `libraryAskJobs.test.tsx` (CA3 on: a failed ask's retry and the chip keep
the pins through the `pins` door; a failed comparison's `retryCompare` reruns the same request, for both the
pins door and the find-section selection door).

**(ii) Withheld and exam material, on both paths** (`tests/test_reader_ca3_landing_ca5a.py`, on C0a's coverage
vault):
- CA5a's peek and CA3's anchor without pins both refuse the held-out unit and the exam paper (`withheld` /
  `exam_material`), before anything is read. No ask row is opened, no service call is made and no exposure row
  is written.
- After a section is marked held out *after* the search, both paths refuse it.
- A held-out counterpart in the hit's own book on the very topic is never compared: CA3's narrowed request
  leaves it out, and CA5a's path (CA3 off), which pins it, is refused whole (`comparison_withheld`, RW4d's
  withholding). The only exposure rows written are the allowed peek's.

All three tests passed first time; nothing needed fixing.

**(iii) The switch matrix** (`reader_compare.scope_enabled` x `reader.correspondence.enabled`, all four): the
contract has `libraryAsk.compareScope` and the palette has `compare_books` exactly when scope is on, and
`correspondence` is `{enabled, findSection}` exactly when correspondence is on. With both of those removed, the
four contracts are identical.

### Regeneration

- DB/config reference: regenerated and validated as above. Defaults fingerprints: all 29 recomputed.
- The CLI help snapshot, sidecar serializer snapshot, desktop RPC contract, mobile allowlist (CA3's and CA5a's
  new RPCs desktop-only) and the Settings disclosure of `ai.routing.compare_scope` (`ai/disclosures.py`) all
  pass as merged. Nothing else needed regenerating.
- Targeted run after the merge (205 files: everything naming the snapshots, fingerprints, parameter registry,
  `METHOD_REGISTRY`, CLI help, either switch, the compare and tutor RPCs or the reference validator, plus the
  CA3, CA5a, library-ask, compare and section-coverage files; `-n 6`, 5G scope): **4127 passed**, 39 skipped,
  3 xfailed (19 min 24 s).

### Gate (at `f81ce3d0b`; `env -i` with empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`, `TMPDIR`; logs in `fixtures-local/landing/logs/ca3/`)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`; `lint-imports --no-cache` | **36 kept**, 0 broken |
| full suite (`flock`, 10G/2G scope, `pytest -n 8 --dist worksteal --durations=50 -o faulthandler_timeout=600 --junitxml`) | **22,405 passed, 3 failed**, 89 skipped, 47 xfailed. pytest 2,271.1 s (37:51); wall 37 min 54 s from taking the lock (got it at once). The 3 failures are the installed Codex CLI's launch-check pins: `test_diagnosis_isolation::test_configured_mcp_servers_are_listed_and_disabled` and `test_codex_isolation_mcp_check::test_the_installed_codex_passes_the_launch_check[False/True]`. Its feature list now has `features.prediction_preserve_parent_tools` and `skills.bundled`, after `/usr/lib/node_modules/@openai/codex` was updated on 2026-10-29, two days after CA5a's gate. They are deterministic when run alone. `main`'s tree (`git archive main`) fails the same three, so they come from the environment, not from CA3; CA3 touches no Codex provider file. Not fixed here: the lockdown's expected list is the Codex lockdown's own decision. |
| durability (`-m durability`, flock, 5G scope, `-n 6`) | **176 passed**, 1 skipped (54.6 s; wall 60 s from the lock, which another worktree held for about 10 min first) |
| owner lane (`-m owner_vaults`, 5G, `-n 6`; fresh backup-API copies of `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in `fixtures-local/owner-lane-ca3/`) | 83 passed, **2 failed**, 4 skipped (50.4 s; wall 59 s). The failures are exactly the expected `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and `test_placement_fixture_copies[arxiv_v2]`; the skips are the vaults with no copy. |
| frontend (`apps/learnloop-tauri`) | `npm install` ok; `npm run typecheck` clean; whole vitest (`--maxWorkers=4`, 5G): **225 files, 1981 passed** (43.5 s; wall 44 s); `npm run frontend:build` ok; `cargo check --manifest-path src-tauri/Cargo.toml` ok |

### Smoke on owner copies

The smoke ran on fresh backup-API copies of the same three mvp035 owner copies (`fixtures-local/smoke-ca3-fresh/`).
Each copy was upgraded with `learnloop upgrade --to mvp-0.38` (prints `mvp-0.35 -> mvp-0.38`), then
`rebuild-derived-state`, then the RPCs ran through a real sidecar process (`python -m learnloop_sidecar` over
stdio, cwd outside the checkout).
- Everything ran under `env -i` with an empty `HOME`, `CODEX_HOME` and config dir, `LEARNLOOP_COVERAGE_MODELS=off`
  and AI base URLs at `127.0.0.1:9`, so the Decider and every compare model were unavailable.
- Audit hooks refused non-loopback sockets and process starts, and **logged nothing**.
- Only counts and status or refusal codes were recorded (driver: `fixtures-local/landing/smoke_ca3/smoke.py`).

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| library readings / readable sections / withheld sections | 3 / 49 / 13 | 2 / 11 / 5 | 12 / 20 / 20 |
| contract: `compareScope`, `correspondence`, `compare_books` in the palette | on, on, yes | same | same |
| selection door on one section (anchored on its first passage): status, rows, exposure rows | `too_few_sources`, 1 (the anchor), 1 | same | same |
| ask-box door on another section: `reader.compare_scope` reading | `fallback` / `unavailable`; the *compare all your books on "…"* line is offered | same | same |
| ... then today's library answer (`reader.library_ask`): status, hits | ok, 8 | ok, 8 | ok, 8 |
| ... the one press (`ask_box` door, no books named) | `too_few_sources`, 0 rows | same | same |
| withheld spans as anchors (3 each) | all three are teaching exclusions (exercise-cited / non-teaching roles), none held out: compared as the reading's own passage, `too_few_sources`, 1 row | same | same |
| exam / held-out spans in the copy | none (nothing to probe; covered by (ii) above) | none | none |
| `rebuild --shadow` before / after (mastery/facet/schedule) | 0/0/0 / 0/0/0 | 0/0/0 / 0/0/0 | 0/0/0 / 0/0/0 |
| `model_call_receipts` rows added | 0 | 0 | 0 |

### Owner notes

- Kill switch: `[reader_compare] scope_enabled` (default true). With it off, every door is RW4a's/RW4d's exactly,
  and CA5a's compare on a found section is its library-ask path.
- The `compare_scope` route (`ai.routing.compare_scope`, decider-only) is a **paid Decider call**, made only when
  the learner presses the ask box. It is capped per day (`scope_max_calls_per_day = 200`) and time-boxed
  (`scope_timeout_seconds = 4.0`), and it is disclosed in Settings.
- No upgrade is needed for CA3 itself. The owner vaults' pending `upgrade --to mvp-0.38` (cold-retry) is
  unchanged by it.

### Open items

- **The Decider unavailable** (§4.3 says compare every book at once): the built behaviour is today's library
  answer plus the one-press *compare all your books on "…"* (owner question 1 above).
- **Workbench**: the selection verb defers until the learner leaves the problem, rather than comparing inside the
  workbench.
- **Unstored comparisons** (`passagesId`) are held in sidecar memory. Making them durable needs a migration.
- **The cancelled-bind race with CA3 off** (RW4d's pins) is still there: the fence is enabled only with CA3 on.
- **Not built**: *change* on selection-started comparisons, chips inside the intent box, the two-stage pending
  line.
- **No real `compare_scope` call has been checked** (no live calls at landing).
- **From this landing:**
  - With CA3 on, CA5a's compare on a found section compares the hit's book by discovery, narrowed to that book,
    rather than pinning the hit's own passage, because CA3's doors take no pins without an ask. If the hit's own
    passage must lead, a door-level pin of the counterpart would need its own review.
  - C0a's Library withholds whole sections for any teaching exclusion. Comparisons withhold exam and held-out
    material only (`corpus.exam_exclusions`, by design). So an anchor on an exercise-cited passage of the open
    book is compared, as RW4a pins are.
  - The installed Codex CLI's launch-check pins need updating for its 2026-10-29 feature list. That fails on main
    too and is not CA3's.
