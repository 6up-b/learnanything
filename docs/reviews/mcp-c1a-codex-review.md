# Chat frontend C1a: Codex review and fixes

**Stage:** `mcp-c1a`, branch `mcp/c1-read-context`. **Reviewed:** `9c5c62df9..26dc3da33` (Codex,
job `20261014-090430-VQoAoQ`, verdict "request changes"; Codex edited nothing and ran no gate).
**Fixed in:** `e0fdfef36`. **Spec:** [spec_mcp_frontend_c1.md](../specs/spec_mcp_frontend_c1.md) (§3.3, §4.5,
§4.7 and §5 updated). **Stage record:** [mcp-c1a.md](mcp-c1a.md).

Every finding was reproduced first by a failing test (`tests/test_mcp_c1a_review.py`, plus the planted cases
added to `tests/mcp_world.py`, which `test_no_protected_text_reaches_any_payload` now checks on every tool).
All ten reproduced as described; none was rejected. No migration, config, CLI or frontend change.

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Malformed protection metadata fails open | fixed | `e0fdfef36` | `test_unreadable_source_sets_fail_closed[malformed]`, `[truncated]`; `test_a_vault_that_changes_while_it_loads_fails_closed`; `test_an_unreadable_practice_item_withholds_its_own_answers_only` |
| F2 | High | Recurrence groups disclose text withheld elsewhere | fixed | `e0fdfef36` | `test_a_recurrence_group_rooted_in_a_protected_hypothesis_keeps_no_statement`; `test_no_protected_text_reaches_any_payload` (group `grp_cold` rooted in the cold check's hypothesis) |
| F3 | High | Exam detection omits supported provenance forms | fixed | `e0fdfef36` | `test_exam_items_are_found_by_every_provenance_form` (canonical exercise, `span:` locator, `ext/span` id) |
| F4 | High | Historical answer keys are filtered against the current key | fixed | `e0fdfef36` | `test_answers_and_diagnoses_are_filtered_against_the_key_they_were_graded_by` (key planted in the answer, a hypothesis and a live diagnosis summary) |
| F5 | Medium | Reservations created during retrieval are missed | fixed | `e0fdfef36` | `test_a_check_reserved_while_passages_are_retrieved_withholds_them` (controlled interleaving) |
| F6 | Medium | An unmatched topic returns unrelated learner history | fixed | `e0fdfef36` | `test_an_unmatched_scope_returns_no_learner_history` (unknown topic; unknown ids) |
| F7 | Medium | Unresolved causes disappear unless a named hypothesis exists | fixed | `e0fdfef36` | `test_unresolved_causes_show_without_a_named_hypothesis` |
| F8 | Medium | "Verbatim" passages lose meaningful formatting | fixed | `e0fdfef36` | `test_passages_are_verbatim_with_their_formatting` (indented Python, a Markdown table, display math) |
| F9 | Medium | Paid retrieval lacks the required dry-run estimate | fixed | `e0fdfef36` | `test_find_sources_dry_run_plans_without_a_provider_or_exposure`; `test_a_subscription_route_is_estimated_from_tokens` |
| F10 | Low | Invalid tool calls bypass the promised telemetry | fixed | `e0fdfef36` | `test_calls_the_sdk_rejects_are_recorded_once` |

## What changed, per finding

- **F1.** `learner_context.protection_issues(vault)`: a source-sets file the loader could not read (any
  loader issue on its path), a source-sets file that is empty (a write in progress: the desktop's
  `write_yaml` truncates and rewrites in place), or the loader issue `vault:snapshot_unsettled` make
  `withheld_items` unavailable, so nothing is shown (fail closed). `RemoteRuntime` now fingerprints path,
  size and mtime of every file the loader reads (not count and newest mtime), keeps a load only when the
  fingerprint is identical before and after it and the source-sets file is not caught empty, retries 3
  times 50 ms apart, and otherwise keeps the load marked unsettled and loads again on the next request.
  An item the vault cannot read (a deleted item, or a practice-item file that failed to load) is withheld
  on its own (`Withheld.known_items`, reason "its question could not be checked") rather than darkening
  the vault: the probability copy has one invalid item file and keeps working. In `find_sources`, a
  protecting item missing from the vault is excluded by its database links alone, or, when an item file
  failed to load, the request is refused. `library` marks every source as possibly exam material when
  protection cannot be trusted. Residual: a non-atomic write stalled between two `write` syscalls across a
  whole load and both fingerprints could still be read as a valid, shorter file (practice-item and
  source-set files are normally one syscall after the truncation); the next fingerprint check (at most 2 s)
  reloads it. Making `write_yaml` atomic (temp file and rename) would remove that window. It is desktop
  code, outside C1a, and is a recommended follow-up.
- **F2.** A hypothesis statement is withheld when any answer of its episode (every version), and a group
  statement when any answer behind any member episode, is on a withheld, unknown or unrecorded item, or
  when protection is unavailable.
- **F3.** `withheld_items` classifies items with the shared `exam_material.item_exam_status` (its
  `item_source_keys` / `source_ref_keys` normalization) instead of its own narrower loop.
- **F4.** `learner_context.KeyBook`: every key an item is known to have had (today's YAML key and the
  `expected_answer` of every `assessment_contract_versions` row, the pinned one included), read for
  filtering only and never serialized. Answers, diagnosis summaries, trace hypotheses, open-hypothesis,
  group, misconception and candidate statements are all filtered against it. An answer with no single
  pinned contract on an item whose known keys differ is withheld ("the revision this answer was graded
  against is not recorded"), and so is its diagnosis text. Contracts that cannot be read withhold all
  key-sensitive text. On the linear_algebra copy (55 contract versions over 54 items), no answer was
  withheld for an unknown revision.
- **F5.** `find_passages` runs retrieval (the paid steps) outside any lock. It then opens
  `repository.atomic()` (`BEGIN IMMEDIATE`), reads `withheld_items` again, filters, and records the
  exposure in that same transaction. While it holds the write lock no reservation, cold retry or
  exam-pool write can commit. On the copies the lock was held 109 to 154 ms per call. Residual: the
  desktop's own admission reads exposure (`exposed_items`) and writes the reservation in separate
  transactions (e.g. `diagnosis/remediation.py`), so if both sides interleave there, the check is
  reserved on an exposed item. The exposure row is already committed, so the coldness receipts do not
  count that check as cold; it is wasted, not falsified. This race is the same one the Reader has.
  Making the admission atomic is desktop scope.
- **F6.** `recurrence_groups` returns nothing for an empty resolved scope and always filters by scope.
  The whole-learner request is `matched_by: all` (every active LO). Unknown ids add an `unknowns` line, as
  an unmatched topic already did.
- **F7.** Diagnosed causes and unresolved causes are read by separate functions, each with its own
  failure note.
- **F8.** The block text is returned as stored. Only the character budget cuts it (`truncated: true`, an
  ellipsis), and the cut is no longer right-stripped.
- **F9.** `find_sources(dry_run=true)` → `remote.sources.plan_passages` on a read-only attach. It returns
  the rewrite and its retry and the query embedding (from `plan_library_search` for the same deep search),
  plus the listwise verification at its worst case (16 candidates of 900 characters, plus one truncation
  retry). Each step reports its route, billing, `cost_basis`, tokens and dollars (`estimated_only` and
  marginal 0 on a subscription route such as Codex on the ChatGPT plan, per Slice A §5 rule 6). The
  response also carries the plan's total calls and tokens, the marginal worst-case dollars and the caps.
  No provider is resolved; nothing is retrieved, shown or recorded as read. The call itself is recorded,
  with `summary.dry_run`.
- **F10.** `LearnLoopServer.call_tool` (the SDK's dispatch boundary) records a request that no tool body
  took. That covers arguments that fail the input schema (`invalid_arguments`) and an unknown tool
  (subject `unknown_tool`; the host's name is not stored). A dispatched call marks itself through a context
  variable and is recorded once, by `ToolCalls.run`, as before.

## Claims re-checked

| Claim | Now |
|---|---|
| "No protected text reaches any payload" / G5 on every output | Holds against the planted cases for F1-F4 on every tool (`test_no_protected_text_reaches_any_payload`, the F1 tests) |
| Fail-closed protection | Loader errors, empty files and unsettled snapshots now fail closed, not only an injected exception |
| Passages held for a check are never shown | Protection is read again under the write lock that records exposure (F5); residual desktop-side race above |
| Passages are verbatim | Yes (F8) |
| Every tool call, failures included, is recorded | Yes, including SDK validation failures and unknown tools (F10) |

## Not changed (outside this stage's findings)

- `status` has no daily spend/cap line (review matrix). It was not raised as a finding, so it is left for
  the owner to prioritise.
- Broader C1 parity (`history`, `what_im_working_on`, `read`, `read_note`, `where_from`, search/goal tools)
  and OAuth stay deferred, as the short spec records (C1b, R1).

## Manual run (backup-API copies, no model, no network)

The worktree's `fixtures-local/c1a-manual/{linear_algebra,probability}` copies, made with
`learnloop.db.copies` in the C1a stage, were used. Every model client was refused (`tests.mcp_world.no_model_calls`).
Each tool was called in-process through the SDK client:

| Vault | learning_context (30 traces) | learning_context (topic) | library | find_sources | find_sources dry run | unknown topic | `{"query":"x"}` |
|---|---|---|---|---|---|---|---|
| linear_algebra | 407 ms | 138 ms | 259 ms | 467 ms (write lock 154 ms; 4 passages, 2 held for a check) | 152 ms: 3 calls (rewrite and its retry, verification), 56,771 tokens, `estimated_only`, marginal $0 | every section empty | error, recorded `invalid_arguments` |
| probability | 178 ms | 158 ms | 342 ms | 418 ms (write lock 109 ms; 6 passages) | 179 ms: 1 call (verification), 38,694 tokens, `estimated_only` | every section empty | error, recorded `invalid_arguments` |

linear_algebra still withholds the same 15 exam items (reserved exam pool), 1 probe and 1 cold check as
before the fix, so F3 widened the coverage without changing the classification on real data. The paid
route asked for was `source_query_rewrite`, which received no client. **Paid calls: 0; cost: $0.**

## Gate

Run on `e0fdfef36`, with TMPDIR set to the worktree's `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` (dev carries `mcp==2.3.0`), `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **21 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,688 passed**, 0 failed (9 min 13 s); 10,673 before plus the 15 new review tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,588 deselected (includes the two-process stdio test) |
| The C1a tests alone (`test_mcp_c1a_review`, `test_mcp_tools`, `test_mcp_runtime`, `test_mcp_http`, `test_mcp_cli`) | 49 passed; also 48 of 49 with `--durable-sqlite` (WAL): `test_attach_and_every_view_write_nothing` lists the `-shm`/`-wal` files WAL readers create, and fails identically on the unfixed branch; it is not in the durability lane |
| DB reference generate/validate, CLI help snapshot, config references | not applicable: no schema, CLI or config change |
| npm / cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
| Paid calls | none ($0) |

## Open questions for the owner

- **Q6:** should `write_yaml` become atomic (temp file and rename) on the desktop side, closing F1's
  residual window? This is outside C1a.
- **Q7:** should the desktop's reservation admission (`exposed_items` read, then the reservation write)
  run in one `BEGIN IMMEDIATE` transaction, closing F5's residual race for every surface? This is outside C1a.
- Q1–Q5 from the stage record are unchanged.

## Re-review

**Reviewed:** `26dc3da33..745318191` (the fix commit `e0fdfef36` and its record; Codex, job
`20261014-103130-kyaOce`, verdict "reopened"; Codex edited nothing, ran lint-imports (21 kept) but not the
full suite or the durability lane). **Fixed in:** `8c42bfecf`. **Spec:** §4.5, §4.6 and §4.7 rule 1 updated.

F1, F2 and F3 were confirmed fixed. F4 was reopened, and two new findings were raised. Each of the three was
reproduced first by a failing test in `tests/test_mcp_c1a_review.py`, then fixed; none was rejected. No
migration, config, CLI or frontend change.

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Malformed protection metadata fails open | confirmed fixed by the re-review | `e0fdfef36` | unchanged |
| F2 | High | Recurrence groups disclose text withheld elsewhere | confirmed fixed by the re-review | `e0fdfef36` | unchanged |
| F3 | High | Exam detection omits supported provenance forms | confirmed fixed by the re-review | `e0fdfef36` | unchanged |
| F4 | High | Historical answer keys (reopened: an unpinned answer counted as the current revision when no key change was recorded) | fixed | `8c42bfecf` | `test_an_unpinned_answer_shows_no_text_even_when_no_key_change_is_recorded` |
| F11 | Medium | Dry-run verification understates its advertised worst case | fixed | `8c42bfecf` | `test_the_dry_run_bounds_the_live_verification`; `test_no_character_encodes_wider_than_the_dry_runs_filler` |
| F12 | Low | Combined hypotheses exceed their configured limit | fixed | `8c42bfecf` | `test_open_hypotheses_share_one_limit_and_keep_unresolved_only_causes` |

**Reproduced before the fix:** F4: an older answer on an item whose key was later edited, with no contract,
snapshot or YAML left recording the old key, came back verbatim (`"I wrote: LEGACY KEY 8841 ..."`), and so did
its diagnosis summary, its hypothesis and the recurrence group it roots. F11: with 16 mostly CJK candidates,
a remediation naming a misconception and a synthetic $10 per million metered route, the dry run planned
38,722 tokens for the first call while the live prompt estimated 63,025 (no provider called; the live
request was captured at `judge_listwise`). F12: with a limit of 1 the section returned 2 entries.

### What changed, per finding

- **F4.** Answer and diagnosis text now needs affirmative evidence of the revision it was graded against:
  exactly one live pinned contract on the attempt's own item (`learner_context._pins`, which replaces
  `_pinned_stems` and also supplies the pinned question). Without it the trace shows no answer, no
  diagnosis summary and no trace hypothesis (note: "the question revision this answer was graded against
  is not recorded"; a text that states a known key still says "it states the answer key"). A hypothesis or
  recurrence-group statement is withheld too when any answer behind it is unpinned. `KeyBook.changed`
  (the "no recorded change" shortcut) is gone; the book also reads `practice_item_snapshots` keys, for
  filtering only. Two tests that expected an unpinned answer to show now pin it, as the desktop does when it
  grades (`test_an_unreadable_practice_item_withholds_its_own_answers_only`,
  `test_a_second_process_serves_the_vault_beside_the_desktop_sidecar`). Cost on real data: over all 70
  attempts of the linear_algebra copy, 1 answer is newly withheld (an attempt regraded with no contract on
  its live evidence); 28 still show, 8 are withheld as key-restating, 30 as exam material, 2 for a cold
  check and 1 as a probe. Both probability answers still show.
- **F11.** `source_retrieval.find_sources` now exposes the verification's prompt construction
  (`verification_question`, `verification_context`, `verification_candidates`, `verification_prompt`),
  which `_verify` and `find_sources` use unchanged in behaviour. The dry run renders that same prompt with the
  request's own question and context (the misconception a remediation names, resolved as
  `propose_sources` does; the chat names no facet, excluded span or learner work) over `widest_candidates()`:
  a full pool of 16, every field at its clip limit, every character `"\x01"`, which the prompt's JSON
  encodes in 6 bytes, the most any character costs (checked over every code point of the BMP and the astral
  edges). The retry is the truncation retry at twice the output budget. For a metered route the worst-case
  dollars are also bounded by the verification's own caps, which refuse any attempt past them
  (`worst_case_bounded_by_caps`). In the F11 test the plan is now 136,558 tokens for the first call (live:
  63,025) and $1.69 worst case, bounded by the 169,152-token cap (live worst case: $1.42). On the copies
  (Codex, the owner's subscription), the verification is planned at 136,396 tokens, `estimated_only`,
  marginal $0. Residual: `plan_library_search` (the sources track's planner, shared with the desktop
  library) plans the query embedding of a not-yet-written rewrite as 2,000 ASCII characters; a non-ASCII
  rewrite could cost up to 4 bytes per character, about 6,000 tokens more at the embedding price (under
  $0.001 at qwen3-embedding's price). Left for the sources track (Q8).
- **F12.** `_share_limit` puts diagnosed and unresolved causes under the one `hypotheses` limit. When they
  overflow it, the unresolved causes keep up to half of it (at least one entry), LOs with no diagnosed cause
  shown first, and the diagnosed causes fill the rest, so F7's case (an LO with only unsettled causes) stays
  visible. `_unresolved_causes` no longer cuts on its own.

### Manual run (backup-API copies, no model, no network)

The same `fixtures-local/c1a-manual` copies, every model client refused; tools called in-process through the
SDK client:

| Vault | learning_context (30 traces) | find_sources dry run (alternative) | answers withheld for revision (all attempts) |
|---|---|---|---|
| linear_algebra | 508 ms; 12 of 30 answers shown, no unknowns | 131 ms: 3 calls, 154,471 tokens (verification 136,396), `estimated_only`, marginal $0 | 1 of 70 |
| probability | 83 ms; 2 of 2 shown | 104 ms: same plan | 0 of 2 |

No paid route was asked for. **Paid calls: 0; cost: $0.**

### Gate (re-review)

Run on `8c42bfecf`, with TMPDIR set to the worktree's `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **21 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,692 passed**, 0 failed (9 min 53 s); 10,688 before plus the 4 new re-review tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,592 deselected |
| The C1a tests alone (`test_mcp_c1a_review`, `test_mcp_tools`, `test_mcp_runtime`, `test_mcp_http`, `test_mcp_cli`) | 53 passed |
| The source retrieval and service tests touching the shared verification prompt (16 files, `test_find_sources_intents`, `test_exam_protection`, `test_source_service_spend_envelopes` among them) | 303 passed |
| DB reference generate/validate, CLI help snapshot, config references | not applicable: no schema, CLI or config change |
| npm / cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
| Paid calls | none ($0) |

### Open questions for the owner (re-review)

- **Q8:** `plan_library_search` plans the query embedding of a not-yet-written rewrite as 2,000 ASCII
  characters, so a non-ASCII rewrite can cost up to about 6,000 tokens more than planned (under $0.001 at
  the embedding price). Bound it at 4 bytes per character in the sources track's planner? This is outside C1a.
- Q1-Q7 are unchanged.

## F4 round 3

**Verified:** `4493140a2` (the re-review's fix and record). The verify reopened F4 [High] again: an unpinned
historical answer whose text states a key nothing records any more (`att_legacy`, no contract, no snapshot,
today's YAML edited) was withheld as a trace, but the same key, propagated through its error event, came back
in a recorded misconception's statement and correction, a candidate's statement, and the learner-text gaps
drawn from that answer (their words and their targets). Those sections still used per-field key filters with
no provenance or revision check. **Fixed in:** `3e1725836`, by one rule rather than per-field patches.
**Spec:** §4.6 and §4.7 rule 1 updated.

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F4 | High | Historical answer keys (round 3: answer-derived text outside the traces had no provenance or revision check) | fixed | `3e1725836` | `test_text_drawn_from_an_unpinned_answer_is_withheld_in_every_section`; `test_text_whose_provenance_cannot_be_followed_is_withheld`; `test_every_text_field_of_the_output_is_guarded_or_not_answer_derived`; `test_only_the_renderer_releases_answer_derived_text` |

**Reproduced before the fix (fail-first).** The four tests were run against `4493140a2`'s `learner_context.py`
and `server.py` (with stub names so the test module imports), and all four failed. The reproduction world
plants `att_legacy` and propagates it through an error event into `mc_legacy` (statement and correction) and
`mcand_legacy`; through the gaps drawn from it (`diagnosis`, `stuck_answer`) and a question on its item asked
outside any attempt; through a candidate a gap on it created (`mcand_from_gap`); through a misconception
promoted from a candidate drawn from it (`mc_promoted`); and through a pinned answer's diagnosis whose context
receipt showed it. On the unfixed code the legacy key reached 13 fields: `mc_legacy.statement`,
`mc_legacy.correction`, `mc_promoted.statement`, `mcand_legacy.statement`, `mcand_from_gap.statement`,
`att_own`'s diagnosis summary, and the `learner_text` and `target` of the gaps `gap_legacy_diag`,
`gap_legacy_stuck`, `gap_item_question` (plus `gap_legacy_created.target`). After the fix it reaches none. The
unfixed code also showed a misconception whose error events are not on record, and its schema had open
`dict[str, Any]` entries, so no test could enumerate the text fields.

### What changed

- **One renderer.** `learner_context.AnswerTextGuard.render(text, origin, limit)` is the only place
  answer-derived text is released. It returns a `GuardedText` (a `str` subclass whose constructor takes a
  module-private token), or `None` and the reason. A test checks that the module constructs `GuardedText` only
  inside `render`. Every section calls it: misconception statements and corrections, candidate statements,
  open-hypothesis and recurrence-group statements, trace answers, diagnosis summaries and trace hypotheses,
  gap words, and gap targets (`registry()` resolves the belief and its origin; a topic target is a title in
  `target_topic`, not text).
- **The rule.** `render` follows the text's `Origin` (the answers behind it, the items it is about, its
  topics). It releases the text only when all of the following hold, checked in this order: (1) every answer
  behind it passes the answers' own protection check (`attempt_reason`: exam, reserved, cold-check and probe
  items, exam and probe attempts, unknown items, protection unreadable), and so does every item it is about;
  (2) the keys could be read and the text restates none of its items' keys or its topics' keys; (3) every
  answer behind it was graded against exactly one pinned contract on its own item, and every item it is
  about has such an answer behind it; (4) every link could be followed, and there is at least one link,
  unless the text is about no item at all (a Reader or library question). A withheld text keeps its entry,
  its counts and its status, and its note says why. Three notes are new: `PROVENANCE_MISSING`,
  `PROVENANCE_UNKNOWN` and `REVISION_UNKNOWN_ASKED`.
- **Provenance followed.** The guard follows these links:
  - a misconception: its listed error events, events linked back to it (`error_events.misconception_id`),
    candidates promoted into it, and hypotheses whose evidence names it as promoted;
  - a candidate: its error events, its items, the error hunts that minted or counted it, and the gaps that
    created it (`belief_candidate`);
  - a gap's words: the answer they are, or were asked during; otherwise the item they are about;
  - a hypothesis: its answer and every version of its episode;
  - a diagnosis summary: its answer, plus everything its context receipt says the diagnoser was shown
    (failure, success and history attempts, cited attempts, attempt ids named in the text, the hypotheses and
    recorded beliefs it was given).

  A hypothesis's own error event is followed when it is on record. When it is not, nothing is lost: the
  event belongs to the hypothesis's own answer, and a regrade replaces events with new ids.
- **Keys.** Each text is checked against the keys of every item behind it, plus its topic's keys for
  statements and for words tied to no item. Answers and words about one item use their item's keys, as
  before. Adding the topic's keys to answers was tried and dropped: on the linear_algebra copy it withheld 7
  more of 30 recent answers, all on generic keys of ordinary sibling items ("Vector addition and scalar
  multiplication").
- **The output schema is typed and closed.** `ContextOut` now types every section with `extra="forbid"`
  models, and open hypotheses are a union discriminated on `kind`. `ANSWER_DERIVED_FIELDS` (10 paths) and
  `NON_ANSWER_FIELDS` (88 paths, each with the reason it is not answer-derived) partition the 98 text fields
  of the advertised output schema. The schema test walks that schema, fails on any open object or untyped
  leaf, and checks the partition. It then runs `learning_context` on a world where every answer-derived field
  is released at least once. Every value at an answer-derived path must be a `GuardedText`. No other text
  field may be one or carry planted answer text.
- **Test world.** `tests/mcp_world.py` now records the provenance the pipeline writes. `mc_swap`'s events `e1`
  and `e2` are error events of the pinned `att_own` (before, they were dangling ids). The world's gaps were
  asked during `att_own`, and `gap_open` created `mcand_row`. Under the rule, dangling or absent provenance
  withholds.

### Manual run (backup-API copies, no model, no network)

`learning_context` ran through the SDK client on the `fixtures-local/c1a-manual` copies, with every model
client refused, on the fixed code and on `4493140a2`:

| Vault | 30 traces | answers shown (30 / all) | answers withheld for revision (all) | other sections |
|---|---|---|---|---|
| linear_algebra | 550 ms (unfixed: 526 ms) | 12 / 28 of 70, identical to unfixed | 1 of 70, identical | 1 open hypothesis shown, 1 withheld (a probe), identical; no active misconception, open candidate, open gap or completed diagnosis on the copy |
| probability | 112 ms | 2 / 2 of 2, identical | 0 | none |

On the owner's data the fix withholds nothing that was shown before. Its new checks apply to sections that are
empty on both copies today. **Paid calls: 0; cost: $0.**

### Gate (F4 round 3)

Run on `3e1725836`, with TMPDIR set to the worktree's `fixtures-local/tmp`:

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **21 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,696 passed**, 0 failed (14 min 25 s); 10,692 before plus the 4 F4 round 3 tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,596 deselected (1 min 49 s) |
| The C1a tests alone (`test_mcp_c1a_review`, `test_mcp_tools`, `test_mcp_runtime`, `test_mcp_http`, `test_mcp_cli`) | 57 passed (53 before, plus the 4 F4 round 3 tests) |
| DB reference generate/validate, CLI help snapshot, config references | not applicable: no schema, CLI or config change (the MCP output schema is not a DB or CLI reference) |
| npm / cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
| Paid calls | none ($0) |

### Open questions for the owner (F4 round 3)

- **Q9:** a regrade deletes an attempt's error events and writes new ones with new ids. A recorded
  misconception or candidate whose listed events were replaced then has a link that cannot be followed, and
  its text is withheld (entry and counts kept, `PROVENANCE_MISSING`). Should regrades keep event ids, or
  should re-normalization rewrite the source list? This is desktop scope. No active belief on the copies is
  affected today.
- **Q10:** a tutor question about an item, asked outside any attempt, is withheld: no graded answer
  establishes which revision of the question it was about (`REVISION_UNKNOWN_ASKED`). Should `question_events`
  record the item's contract or snapshot hash when the question is asked, so these can show? This is desktop
  scope.
- Q1-Q8 are unchanged.
