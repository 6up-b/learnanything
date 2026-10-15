# Chat frontend C1a, narrowed: the Codex review and its fixes

**Stage:** `mcp-c1a-narrow`, branch `mcp/c1-read-context` (worktree `learnanything-mcp`).
**Reviewed:** `34527fa13..9d9e80b28`, the narrow stage (code `3bdc89da7`, record `9d9e80b28`; see
[mcp-c1a-narrow.md](mcp-c1a-narrow.md)). **Codex job:** `20261015-013013-6suEC4` (two Medium findings, one
Low). **Fixed in:** `b603273bd`. Main is `a9356f986` (mvp-0.24). It was not merged here; convergence with
R2a's `LearnerStateCardV1` happens at landing.

## Findings

| ID | Severity | Title | Verdict | Commit | Test (fails on `9d9e80b28`, passes after) |
|---|---|---|---|---|---|
| F1 | Medium | A raw-ID lookup still confirms a withheld generated title | **fixed** | `b603273bd` | `test_a_raw_generated_id_cannot_confirm_a_guessed_title` (`learning_context` and `find_sources`) |
| F2 | Medium | The provenance hook accepts answers that fail the answer guard | **fixed** | `b603273bd` | `test_a_recorded_input_answer_that_states_its_key_releases_nothing`, `test_a_recorded_provenance_releases_nothing_unless_complete_and_safe[answer_states_a_key]` |
| F3 | Low | Concurrent first starts can replace the alias key | **fixed** | `b603273bd` | `test_a_second_first_start_keeps_the_alias_key_already_installed`, `test_simultaneous_first_starts_agree_on_one_alias_key` |

All the new tests are in `tests/test_mcp_c1a_narrow.py`. No finding was rejected. There was no High finding.

### Reproduction (fail first)

The tests were written first and run against the unfixed tree. All failed. Before the gate, they were run again
with `9d9e80b28`'s `src/` and `migrations/` (from `git archive`) placed first on the import path
(`-o pythonpath=…`). **5 of 5 failed**, each on its leak or race assertion. The old module was confirmed to be
the one imported.

- **F1.** `generated_world` creates `lo_ltg_legacy_key_8841_…_<hash>` from the unpinned `att_legacy`. The test
  derives the raw id from the guessed title, as `text_gaps.actions.creation_ids` does (`slug` and the source's
  hash), and a wrong guess (`8842`). On `9d9e80b28`, `learning_context(learning_object_ids=[right])` returned
  the topic's traces, beliefs, groups and retention risks under its alias, with `learning_object_count` 1. The
  wrong guess returned nothing, with the id in `unknown_ids`.
  **The same channel was open in `find_sources`.** Its `_scope` accepted any id in the vault, so a correct
  guess was missing from `unknown_learning_object_ids` and a wrong one was listed. This was confirmed on its
  own: with only the `learning_context` half of the fix in place, the `find_sources` assertion still failed
  (`[]` against `['<guess>']`). It was fixed under F1 because it is the same defect in the same stage's tool
  surface.
- **F2.** `att_keyed` is a pinned, unprotected answer on `pi_own`, and its text states `pi_own`'s contract
  key. Its trace showed `withheld: it states the answer key`. A complete record naming `att_own` and
  `att_keyed` still released a misconception statement that states no key, as a `RecordedText`.
- **F3.** In the stale-read replay, A installs a key, then B's first read reports "missing". On `9d9e80b28`,
  B made a second key and replaced A's file. In the race, four threads started together and produced **four
  different keys**.

## What changed

- **F1: only the alias names a withheld topic.** In `resolve_scope`, a requested id that is not an alias is
  accepted only when `TextGuard.searchable` allows it. `searchable` is the predicate that already kept a
  topic search off a withheld name. A withheld generated topic's raw id resolves to nothing, and the response
  is exactly the one for an id the vault does not have. `find_sources` (both the live path and the dry run)
  now reads its named ids through the same `resolve_scope` with a `TextGuard`
  (`remote.sources._named_los`). It also accepts the alias that `learning_context` shows, which it did not do
  before. The server passes the vault's alias key to both paths. Authored ids, and a generated id whose name a
  record releases, are accepted as before.
- **F2: one (b) predicate.** `TextGuard._answer_reason(attempt, text)` applies (b)'s checks in order:
  protection, readable keys, no key that its item is known to have had, and exactly one pinned contract.
  `answer()` renders with it. `_unsafe` now applies it to every answer the record names, together with the
  entry's own answers, using the text the attempt records. A failure is named as the reason for the text
  written from that answer: `KEY_WITHHELD_BEHIND` ("an answer it was written from states the answer key") or,
  as before, `REVISION_UNKNOWN_BEHIND`.
  `test_answers_and_diagnoses_are_filtered_against_the_key_they_were_graded_by` now expects
  `KEY_WITHHELD_BEHIND`, because `att_edited`'s own answer restates the key and the record names it. A new
  part of that test keeps coverage of the output filter against the historical key: the record names safe
  answers plus `pi_edited`, and the statement still restates the key.
- **F3: one maker of the key.** `ensure_alias_key` reads first, which is the fast path. When the key is
  missing it takes an advisory `flock` on `.learnloop/mcp/.alias-key.lock` (0600, inside the directory's `*`
  `.gitignore`), reads again under the lock, and only then writes the key, through a temporary file and
  `os.replace`. A start that read "missing" while another start was making the key gets that key. A holder
  that dies releases the lock. On non-POSIX hosts there is no lock; the app targets POSIX, as `vault_lock`
  does.
- **Docs.** Spec §4.6 table and §4.7 now say the raw id is answered as unknown in both tools, and that the key
  is made once under a lock. The module docstrings say the same.

No persisted meaning changed: there is no migration, no new table, and no change to replay, grading, scoring,
scheduling, embeddings or spend. The output schema, the CLI and the configuration are unchanged.

## Manual run (backup-API copies, read-only, no model, no network)

The run used `fixtures-local/c1a-manual/{linear_algebra,probability}`, the backup-API copies made by the
earlier rounds. `LEARNLOOP_CONFIG_DIR` pointed at an empty directory, every `*_API_KEY` was blanked, and the
runtime was attached with `load_environment=False`. On each copy the run called `learning_context` (the whole
learner, 30 traces), three authored ids by raw id, and a guessed `lo_ltg_` id. It also called `views.today`,
`views.progress` and the `find_sources` dry run (`plan_passages`) with the authored ids, all at a fixed `now`.
"Before" is `9d9e80b28`'s source on the import path and "after" is `b603273bd`. Outputs are in
`fixtures-local/c1a-narrow-review-manual/{before,after}.json`.

| Vault | Result |
|---|---|
| linear_algebra (0 generated topics; 30 traces, 2 open hypotheses, 7 retention risks, 21 topics) | **Identical** before and after (0 differing fields). The authored ids were accepted (count 3, no unknown ids), the guessed id was unknown, and `plan_passages` reported no unknown ids. Database SHA-256 unchanged. `learning_context` took 371 ms before and 377 ms after |
| probability (0 generated topics; 2 traces, 1 retention risk, 18 topics) | **Identical** (0 differing fields). Database unchanged. 42 ms before and after |

Neither copy has a generated topic or a write-time record, so F1 and F2 cannot change their output. The run
shows that the fixes take nothing away from authored topics. **Paid calls: 0. Cost: $0.**

## Gate

Run on `b603273bd` with TMPDIR set to the worktree's `fixtures-local/tmp`. The logs are
`fixtures-local/c1a-narrow-review-fullsuite.log` and `c1a-narrow-review-durability.log`; each starts with the
commit it ran on. This gate supersedes the one in [mcp-c1a-narrow.md](mcp-c1a-narrow.md).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | **21 kept, 0 broken** |
| `git diff --check` | clean |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10767 passed, 1 failed**, 16 warnings (14:08; 15:43 including the wait for the lock). The narrow stage had 10763 passed; this fix adds 5 tests, so 10768 were collected. The failure, `test_reading_request_sweep.py::test_d_work_the_cli_finishes_leaves_the_request_due_for_the_sweep`, is a timing check on the reading-sweep thread under machine load (`_source_work_active` still true just after the CLI run). Run alone, `tests/test_reading_request_sweep.py` passed **3 of 3 times (14 passed each)**. Nothing it imports was changed here |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10668 deselected (1:48) |
| The C1a tests alone (`test_mcp_c1a_narrow`, `test_mcp_c1a_review`, `test_mcp_tools`, `test_mcp_runtime`, `test_mcp_http`, `test_mcp_cli`) | **129 passed**: the narrow stage's 124 plus 5 new |
| `find_sources` neighbours (`test_exam_protection`, `test_prescription_passages`, `test_tools_cli`, `test_tutor_tool_requests`, `test_retrieval_interventions_write_points`, `test_facet_locks_landing`) | **49 passed** |
| DB reference generate/validate, CLI help snapshot, config references | not applicable: the schema, the CLI and the configuration did not change |
| npm / cargo | not applicable: nothing under `apps/learnloop-tauri` changed |
| Paid calls | none ($0) |
