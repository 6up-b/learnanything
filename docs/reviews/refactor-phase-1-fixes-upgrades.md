# Phase 1 fix round, group FR-A: upgrades and the version floor

Rows U1-U8, T1 and T5 of `docs/reviews/refactor-phase-1-review.md`, on branch `refactor/p1-fixes-upgrades` from main
`e231d7fb59`. One commit per row, test and fix together; every fix starts from a test that fails at the base.

## U1: the publication sets the setting and reads it back

**Reproduced.** `tests/test_upgrades.py::test_the_publication_changes_the_setting_not_the_same_text_elsewhere`
(both decoys: a comment `# algorithm_version = "mvp-0.58"`, and a `[notes]` table holding the same line, each placed
before `[algorithms]`). At the base both fail the same way: `upgrade()` reports `upgraded=True`, commits the mvp-0.59
rebuild and removes its journal, and the parsed config still names `mvp-0.58` (`assert 'mvp-0.58' == 'mvp-0.59'`).
The new stage `renamed without the tag` of `test_a_failure_before_the_commit_leaves_the_predecessor_readable_and_no_journal`
(a publication whose rename lands a file still naming the predecessor) showed `DID NOT RAISE` at the base: nothing read
the tag back.

**Fix.** `ops/upgrades.rewrite_algorithm_version` sets `[algorithms] algorithm_version` through tomlkit (the writer the
Settings tab already uses; `settings_store.updated_config_text` is `apply_config_updates`'s parse-and-set step, split
out so the upgrade keeps its own durable write), so comments and layout stay and a comment or another table is never
the one changed. Its `from_version` check parses the config (`published_algorithm_version`, the same `load_config`
openers use) instead of matching text. After the publication, inside the transaction, the activation reads the tag
back from the renamed file; anything but the target raises `UnpublishedTag`, which takes the existing failure path:
the predecessor's label is restored (now written whatever the file names, since the read-back can be what failed), the
journal removed, the transaction rolled back.

**Callers and siblings checked.**
- `publish_algorithm_version` / `rewrite_algorithm_version` callers: `_activate_as_writer` (publication and the
  restore), and tests (`tests/test_upgrades.py`, `tests/test_batch3_landing.py`, `tests/followups_nov2_help_fold_helpers.py`,
  `tests/test_route_rules_in_grader.py`): all pass a `from_version` the config names under `[algorithms]`; unchanged.
- Init: `config/template.default_config_text` substitutes the placeholder `@ALGORITHM_VERSION@`, which occurs once in
  a template the code owns; sound.
- Settings saves (`settings_store.apply_config_updates`, sidecar settings/hints/first-run handlers): tomlkit, keyed
  by path; none sets `algorithm_version`; sound.
- Other text writers of the line: `learner/recall_calibration._fresh_calibration_vault`,
  `curriculum/golden_path_fixture._pin_algorithm_version` and `tests/helpers._set_algorithm_version_at` rewrite by
  regex, but only a config just written from the template (one occurrence, no comment naming the key); left as they
  are.

**Not verified.** A real power loss between the rename and the read-back (the read-back is inside the transaction, so a
death there is the existing "death after the publication" case the journal covers).

## U3: a journal that cannot be read is not torn

**Reproduced.** `tests/test_upgrades.py::test_a_journal_that_cannot_be_read_is_kept_and_the_vault_is_not_opened`: the
interrupted state (journal written, config naming the successor, predecessor's database), then the journal's mode set
to 0 (a real permission error; the directory still allows unlinking). At the base `open_vault_repository` did not
raise: `_read_journal` took the `PermissionError` for a torn journal, deleted it, and the vault opened under the
successor's label over the predecessor's database (the test's later `chmod` hit `FileNotFoundError`).

**Fix.** One reader, `activation_journal.read`: `None` when the file is gone, `"torn"` only when its bytes were read
and are not a whole record (malformed JSON, undecodable bytes, missing keys), and any other `OSError` raises
`InterruptedActivation` naming the file and keeps it. The opener's floor pre-check (`activation_journal.complete`) and
the completion (`upgrades.complete_interrupted_activation`) both read through it, so neither treats a read error as
torn. `upgrade()` returns the refusal as a problem (`learnloop upgrade` exits 1 naming the journal) instead of a
traceback. Once the file is readable again the next opener completes the activation (asserted).

**Callers and siblings checked.**
- `upgrades._read_journal` (removed; its one caller now uses `activation_journal.read`) and `activation_journal._link`
  (removed, same) were the two readers that decided; both had the defect (`_link` sent the read error on to the
  completer, which then deleted the file).
- `activation_journal.message` swallows `OSError` only to choose the message's wording; it decides nothing. Sound.
- `pending`, `refuse_if_interrupted`, `remote/runtime.py`, `learnloop_mobile/host.py`, `vault/repository.py` and
  `upgrades._upgrade` test existence only and refuse; sound.
- Other "torn" readers (`adaptive_difficulty/denial_log.py`, the contextual-embeddings adapters) are append logs
  whose torn tail is a line, not a recovery record; not this question.

**Not verified.** An I/O error other than a permission error (the test uses `chmod 0`; the code treats every
`OSError` but `FileNotFoundError` the same). Running as root skips the test.
