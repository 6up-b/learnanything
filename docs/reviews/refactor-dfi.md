# Arc D bug fixes, part 2: ingest and proposals (D-9, D-10, D-11, D-12)

Branch `refactor/d-fixes-ingest`, based on `16a9e3fd48` (main `e9a7733612`, the bug ledger, with K3.5 and D2b
part 1 merged). Ledger rows D-9 to D-12 of `docs/reviews/refactor-bug-ledger.md`, one commit each, then this record.

Rules held: each fix starts from a test that fails on the base; no learner scoring change, no successor, no
`algorithm_version` change, no migration, no config default; no live model call. `tests/test_identity_pins.py` did not
move (no `--write`).

| Row | Commit | Fail-first tests |
| --- | --- | --- |
| D-9 | `887dc67f8a` | `test_source_append::test_a_retry_after_an_append_gate_failure_pays_for_a_fresh_answer`, `test_source_set_synthesis::test_a_fresh_synthesis_after_a_gate_failure_pays_for_a_fresh_answer` |
| D-10 | `611673f094` | `test_apply_recovery::test_an_undo_with_a_pending_intent_is_refused`, `…::test_the_sidecar_reject_names_the_outstanding_intent`, `…::test_the_book_cards_undo_is_refused_before_it_changes_anything` |
| D-11 | `f135b7ef82` | `test_apply_recovery::test_a_registry_save_of_the_text_already_there_writes_nothing`, `…::test_a_target_hashed_without_the_prefix_is_still_read` |
| D-12 | `847ba880fb` | `tests/test_cli_append_units.py` (6 tests, 5 red) |

Red runs: each test was written and run against the unchanged sources before its fix (the tests were the only edit in
the tree), then green after.

## D-9: a gate rejection drops the answer it judged

**Problem.** K3.4 checkpointed the append call before its output check, so a retry never re-paid. But a gate failure
is a verdict on the answer, and the checkpoint replayed that answer into the same rejection at zero cost while the job
stayed `retryable` and the card offered Retry (K3.4's own open item).

**Bootstrap had the same issue.** A probe showed it: two `create_study_map` runs over a candidate the closure gate
rejects made one model call between them. The card's Retry (`retry_build`) first runs the zero-model repair of the
preserved candidate, which is right; if that fails, its fresh `retry_synthesis` read the saved shard result
(`synthesis_shard_results`) and the pass checkpoints and rebuilt the same candidate, and the next Retry repaired
again, in a loop that never paid for a new answer. Fixed here too.

**Red.** Append: after the gate failure both append checkpoints were still saved (`assert 2 == 0`), and the retry
replayed them. Bootstrap: `(shards, passes) == (1, 1)`, expected `(0, 0)`.

**Change.**

| File | What |
| --- | --- |
| `content/synthesis/source_append.py` | `_AppendCall` records the checkpoint key of each call it serves (the first call and its span round, fresh or reused) and gains `discard_answers()`; `_append`'s typed-failure arm calls it for `append_gate_failed` only. `budget_exceeded` and `append_input_over_ceiling` keep theirs: a raised budget reuses the paid answer, as K3.4 intended (its test still passes unchanged) |
| `content/synthesis/source_set_synthesis.py` | `_SavedAnswers` (shard keys and pass keys) filled by `_run_synthesis` (every shard key, every base pass key, every pass `run_pass` serves); `create_study_map`'s arm calls `discard` for `synthesis_gate_failed`. The preserved candidate (`synthesis_runs.candidate_output`) is untouched, so the zero-model repair works as before (`test_auto_repair_drops_criterion_id_dependencies` passes) |
| `db/repositories.py` | `discard_synthesis_shard_result(shard_key)` |
| `db/stores/model_calls.py` | `discard_model_checkpoint`'s docstring names the second reason |
| `content/pipeline/jobs.py` | the append arm's comment says what a retry now does |
| `tests/test_source_append.py` | K3.4's `test_a_retry_after_an_append_gate_failure_makes_no_model_call` asserted the bug; it is replaced by the D-9 test (a span round, then a rejected answer: no append checkpoint left, the retry pays for its first call and completes) |

`synthesis_shard_results` is `RAW_LEDGER` ("captured provider output"); a row is deleted only when the gates reject
the candidate it fed, which is the case its own docstring already argues for ("checkpoint AFTER the output-budget
check so an oversized shard is regenerated on retry rather than reused into the same failure"). No trigger guards the
table. One limit, in `_SavedAnswers`' docstring: a shard reused from `synthesis_shard_results` does not recompute its
span round's key, so that span-round checkpoint stays; its base pass is dropped, so the retry's fresh base answer
makes its own span requests (the old key is reached again only if the fresh answer asks for exactly the same spans).

A real gate failure caused by the vault rather than the answer (fixed by an edit before the retry) now re-pays; that is
the cost of a fresh answer and the row's chosen fix.

## D-10: an undo is refused while an apply intent is outstanding

**Red.** `reject_applied_items` and `reject_items` did not raise over a pending intent; the sidecar's
`reject_proposal_items` returned a result, not an error (`KeyError: 'error'`); the card's `undo_questions` did not
raise.

**Change.** `patches.refuse_while_an_apply_is_outstanding(repository, action=...)` is the one check;
`OutstandingApplyIntentError` takes `action` for its message ("Refusing to undo: ..."). `apply_accepted_items` calls it
as before; `reject_applied_items` calls it under the vault lock before reverting anything, so the inbox's reject and
delete and the CLI `reject` (which already prints any `PatchApplicationError`) are refused. `undo_source_questions`
calls it first, before it moves the book's generation or cancels its builds (refused later, the generation would have
moved with nothing reverted). The sidecar maps it through one function, `handlers/proposals.apply_intent_outstanding`
(the accept's mapping, extracted): `reject_proposal_items`, `delete_proposal_item` and `source_action`'s
`undo_questions` return `apply_intent_outstanding` with `details.intents`. A reject of only pending items is refused
too, as an accept is: those items may be the outstanding intent's own. Doctor's conflicted message and
`apply_protocol`'s module docstring now say accepts and undos.

## D-11: one `post_hash` form, and the readers take both

**Red.** A registry save of the text already in `facets.yaml` replaced the file (one `os.replace`); a target recorded
with a bare hex digest was reported as a conflict at its own pre-image.

**Change.** `apply_protocol.text_hash(text)` is the writers' one form (`sha256:` + hex); `write_registry_text` and
doctor's content fixes use it. `target_conflicts` and `materialize_targets` compare through `_holds(found, recorded)`,
which reads a recorded hash with or without the prefix. Readers checked: those two are the only readers of
`post_hash`/`pre_hash` (`grep` over `src/`: recovery, `complete`/`keep_files` and the accept all go through them; doctor
and the maintenance feed only report a conflict's stored hashes). Every persisted apply intent has carried the prefix
since ING M5 (`d9ad588c62`, `_diff_targets`), and `write_registry_text`'s targets are never persisted, so no stored
intent lacks it; the both-forms read is the guard the row asked for.

## D-12: the CLI append sends only what no kept synthesis sent

**Can the CLI know the new units? Yes, with evidence.** K3.2's planner knows its chapters; the CLI has no planner, but
every completed synthesis run's manifest records what it sent. Backup-API copies of the three backup vaults'
databases (`~/learnloop-backups/20261109-copy`, `backup_database` into the gitignored `fixtures-local/dfi/`, deleted
afterwards), counts only:

| | runs | each completed run's manifest |
| --- | --- | --- |
| `arxiv_v2` | 1 bootstrap completed | `source_set_id`, `unit_inventory_versions` non-empty |
| `linear_algebra` | 1 bootstrap completed, 1 append failed | the same; the append's scope holds `new_revision_ids` |
| `probability` | 1 bootstrap completed, 1 append completed, 1 append failed | the same |

So the filter is derived, not required: no CLI user has to name a scope, and `--new-revision` keeps its meaning.

**Red.** `test_the_cli_append_sends_only_the_member_no_synthesis_has_sent`: the append sent `rev_text`'s
`chapter_symmetry` (the bootstrap's book) beside `rev_alt`. `test_a_partly_sent_member_sends_only_its_new_units`:
it sent `rev_text`, `rev_alt` and `u_a` beside `u_b`. `test_with_nothing_new_…`: a second model call. The rejection and
pending tests: the whole set again. `test_a_named_revision_is_sent_whole_as_before` passes on both (a guard). The
rejection test was then narrowed to the derivation (below, D-16), so the final file fails collection on the base (it
imports `units_not_yet_sent`).

**Change.**

| File | What |
| --- | --- |
| `db/repositories.py` | `completed_synthesis_manifests(source_set_id)`: each completed run's manifest with its `proposal_id` |
| `content/synthesis/source_append.py` | `_sent_units`: per revision, the units each kept run sent: a bootstrap every unit in `unit_inventory_versions`, an append its scope's `new_revision_ids` (only the units its `new_unit_ids` lists for a revision it names). Kept: completed, and its proposal not wholly rejected (a pending proposal counts, as K3.2's planner counts a chapter once it builds it). `units_not_yet_sent(root, set_id)`: a revision none of whose units was sent is named whole with no filter (so the manifest is what an explicit `--new-revision` gives, and a finished run is reused); a partly sent one is narrowed to its unsent units; a wholly sent one is left out. Read-only (`Repository.attach(..., read_only=True)`) |
| `cli/app.py` | append mode without `--new-revision` uses it, for the dry run too; with nothing new it sends nothing, says so and exits 0 (`--json`: `{"version": 1, "nothingNew": true, "message": ...}`). Help text of `--new-revision` and the docstring say so |

A merged unit an earlier append sent under a member's id counts as unsent, so at worst it is sent again. A unit
counts as sent whatever its inventory version, the reading K3.3 chose ("any row for the unit"). The CLI surface is
unchanged (only help text; `tests/cli_surface.json` pins parameters, not help), so no snapshot `--write`.

## New ledger row

- **D-16** (due at arc D's close): a synthesis whose completed run's proposal was wholly rejected is reused when the
  same manifest comes again. Found writing D-12's rejection test: after rejecting an append's whole proposal, rerunning
  the same append (with or without `--new-revision`) makes no model call and returns the rejected proposal
  (`reused=True`). Bootstrap's completed-run cache has the same shape (unverified); whether the book card's Undo then
  "build them again" meets it is unverified. Fix sketch: a wholly rejected run is not reused, and its answers are
  dropped (D-9's discard) so the rerun pays for a fresh one.

## Vault

`Workflows/Import Canonical Sources.md` (a rejected answer's checkpoints are dropped), `Workflows/Doctor Migrations
and Recovery.md` (accepts and undos wait) and `Workflows/Build a Study Map.md` (what an append sends) were edited by
hand. The generated reference notes were regenerated once after the source commits (`_scripts/generate_all.py`,
`3eb9a21efd`: 89 generated notes, mostly line anchors and the new test file's imports); a second run changed nothing.

## Gates

- Targeted tests on `3eb9a21efd`: `scripts/affected_tests.py --files` over the changed paths without
  `db/repositories.py` (which selects the whole suite through `tests/conftest.py`; as K3.5 did), plus every added or
  edited test file and `test_identity_pins`, `test_retired_config_identities`, `test_architecture`,
  `test_test_layout`, `test_effective_defaults_golden`, `test_cli_help_snapshot`: 1,287 of 1,405 test files,
  `-m "not arc_close"`, 13 chunks of about 100 at `-n 4` under the 5 GB cap behind the full-suite lock:
  19,879 passed, 0 failed (skips and xfails as on main).
- `lint-imports --no-cache`: 42 kept. `ruff check`: clean.
- The four vault validators pass (`db_validate_reference.py`, `module_validate.py`, `desktop_validate.py`,
  `validate_vault.py`); `scripts/check_gate_partition.py`: 30,991 collected, landing 30,931 + arc_close 60.
- No full suite (the orchestrator's landing gate).

## Open items

- D-16 (above).
- D-9's span-round limit for a reused shard (above).
- **Process.** D-9's three `source_append.py` hunks went in through a short exact-pattern Python script rather than
  the Edit tool (each replacement asserted to match once); every other source and test edit used the Edit tool. Two
  throwaway probe tests (`tests/test_zz_dfi_probe.py`) were written with a heredoc and deleted, never committed.
