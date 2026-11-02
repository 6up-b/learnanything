# Follow-ups Nov 2 — Codex review fixes

- **Review:** Codex (gpt-6.1-sol), job `20261102-022506-FK4Cde`, one High, one Medium, two Low. The reviewer could
  not start its targeted tests (`systemd-run --user` refused it); its findings came from reading the source and
  tests.
- **Branch:** `fix/followups-nov2` in `learnanything-ad1`, from the stage head `2359bbf258`.
- **No live or paid call was made.** Every model is a fake. The scripts run outside pytest (the defaults-snapshot
  recompute, the CLI help snapshot writer, the DB/config reference generator and validators) ran under `env -i` with
  an empty, existing `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`. No owner vault, `~/.config/learnloop` or
  tracked fixture vault was opened.

## Review

Each finding was reproduced with a failing test first, then fixed. The fail-first runs used the pre-fix sources
(the source diff was saved, `git checkout -- src`, the tests run, the diff re-applied; no stash).

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Changed priming and scoring ship without an algorithm successor | fixed | 8a939d438b, 675ed08733 | `tests/test_help_fold_attach_successor.py` (19 tests): `test_mvp041_is_one_constant_after_mvp040_and_the_latest` (the tag, the switch, its registry rule, every defaults snapshot recomputed); `test_the_fold_is_gated_by_the_tag_and_the_switch[tag, tag-off, predecessor]` and `test_worked_help_primes_only_at_the_tag_with_the_switch_on[...]` (below the tag or switched off, the rollover hint is not counted, nothing is primed, and nothing attaches in the attempt's own transaction: the predecessor exactly); `test_the_same_session_fold_is_the_same_below_and_at_the_tag`; `test_a_rebuild_changes_no_attempt_and_a_shadow_rebuild_is_zero[on, off, predecessor]`; the upgrade chain (from mvp-0.9, 0.30, 0.39, 0.40; bare upgrade; refusal; an interrupted activation completed by the next CLI command; an earlier link's journal handed down). Before the fix the tag did not exist, and the gate tests' predecessor cases counted and primed. |
| F2 | Medium | Retraction can permanently discard a gap whose note remains linked | fixed | 7257e7227d | `tests/test_followups_nov2_note_gap_unlinked.py::test_a_note_linked_while_the_retraction_runs_keeps_its_gap`: a second connection (`sqlite3`, 0.2 s timeout) writes the newly linked note's gap between the retraction's read of the links and its read of the gaps. Before the fix the gap got an `unlinked` reversal. After the fix the second write waits for the retraction's transaction ("database is locked"), lands after it, and the next sweep leaves the gap alone. Also passes with `--durable-sqlite` (WAL and `synchronous=FULL`). |
| F3 | Low | Legacy learner-informed figures still fail open | fixed | 75f2d7fdfb | `tests/test_followups_nov2_figure_provenance.py`: `test_a_marked_quick_figure_with_no_record_is_withheld` (a `+learner-v1` row with no record and no intent carrying one is withheld from listing and delivery; it was shown before the fix); `test_an_unmarked_quick_figure_with_no_record_keeps_the_no_learner_state_reading` (pin); `test_a_press_of_the_same_input_records_the_marked_rows_dependencies` (the press reuses the row with no author call, records its own read's inputs on it, the figure goes out again, and it is withheld once those inputs are protected; failed before the fix). |
| F4 | Low | Queued rich revisions do not inherit dependencies before author calls | fixed | 75f2d7fdfb | `tests/test_followups_nov2_figure_provenance.py`: `test_a_queued_rich_revision_never_sends_a_program_whose_learner_inputs_became_protected` (a revision queued with the switch off; its base's inputs become protected before it runs; the job fails `exam_material` with no rich-author call; before the fix the earlier program was sent and the revision stored); `test_a_queued_rich_revision_stops_when_an_inherited_input_becomes_protected_while_it_runs` (protected during the render: the gate's hold stops it before the store); `test_a_rich_revision_with_nothing_inherited_carries_no_record` (switch-off pin: no key in the payload). |

The review's "Claims that don't hold" are all accepted. The stage record (`docs/reviews/followups-nov2.md`) now
says **Successor: mvp-0.41** for (b). It records the revised decision on legacy marked quick rows (F3) and closes
that open question. F2 and F4 fix the other two claims.

### What changed

- **F1, successor `HELP_FOLD_ATTACH_ALGORITHM_VERSION = "mvp-0.41"`** (one constant, on top of mvp-0.40; kill switch
  `hints.fold_follows_attach`, default true). The playbook's 2026-10-17 rule applies: a change to which new attempts
  are primed is a successor even when replay is unchanged.
  - The gate is `hint_fold.fold_follows_attach(vault)`: the tag or later, with the switch on. The sidecar's two
    submit paths pass it to `_server_hint_fold` as `any_session`. `ServerHintFold.any_session` carries it to the
    attempt's transactional refold.
  - `help_assists._fold_rows(any_session=False)` is the predecessor's definition clause for clause: the key's rows in
    this session, or the keyless window. `any_session=True` (keyed only) reads the key alone.
  - `hint_fold.attach_keyed` attaches nothing unless the fold has `any_session`. Below the tag the keyed rows are
    H0's attach's, after the commit, as before.
  - Replay never folds, so it never reads the switch.
  - Plumbing, following the cold-retry/C1 precedent:
    - `learnloop.help_fold_attach_upgrade`: the next journalled chain link, from mvp-0.40 or from mvp-0.9 onwards.
    - `learnloop upgrade --to mvp-0.41`, which is also the bare upgrade's default.
    - The CLI and sidecar openers complete an interrupted activation through the new link.
    - Also updated: the `activation_journal` docstring, the pyproject module list, the `HintsConfig` field and
      docstring, and the `parameter_registry` rule (structural/operational).
    - Every defaults snapshot was recomputed (`defaults_fingerprint_for_version`; only the new key moves them) and
      `mvp-0.41`'s was added.
    - The DB/config reference was regenerated (1112 effective leaves; prose counts in `Database.md` and
      `Configuration.md`).
    - The CLI help snapshot changed only in the `upgrade` help.
    - Chain pins moved to mvp-0.41 in 34 test files.
  - **Renumbering:** built as mvp-0.41 while teacher TE1 + C4 is landing as mvp-0.41 too. Whichever lands second
    renumbers. It is one constant, plus the snapshot key, the CLI help, and the test pins that name it.
  - The existing (b) tests (`tests/test_followups_nov2_help_fold.py`) now run at the tag; their store-level calls
    pass `any_session=True`, plus a predecessor assertion. `tests/test_hint_h2b_fix3.py::test_r1_f10_...` goes back
    to its predecessor assertions, because its basic vault (mvp-0.6) is below the tag.
- **F2:** in `jobs.retract_unlinked_notes`, `learner_note_ids`, the gap and reversal reads and the inserts now run
  inside one `repository.atomic()` (`BEGIN IMMEDIATE` on the pinned connection). Switched off, it still reads and
  writes nothing.
- **F3:** `service.learner_state_withheld` withholds a lineage row whose prompt version carries `+learner-v1`
  (`R.LEARNER_SUFFIX`) when neither its report nor its rich intent records the inputs (`LEARNER_STATE_UNRECORDED`).
  Unmarked rows keep the no-learner-state reading.
  - **Dependencies established:** when a press reuses such a row (`_reusable`, both reuse points of the build), the
    input hash matched, and that hash names the state's hash. So the press's own read is the same state, and
    `_establish_learner_inputs` records its inputs on the row. The new store writer is
    `figures.record_learner_inputs`: `json_set` only where the key is absent. `interactive_figures` is WORKFLOW.
  - From then on the row is checked like any other.
  - This resolves the dead end the stage record worried about (a press rebuilding into the same reuse key and
    showing "withheld").
- **F4:** `_rich_revision` puts `inherited_learner_state_inputs` into the job payload (`RICH.INHERITED_LEARNER_INPUTS_KEY`).
  - It holds every record along the base's lineage (`service.inherited_learner_inputs`, from the shared `_lineage`
    walk): reports, rich intents, and `None` for a marked row with no record, which fails closed.
  - `run_rich_job` checks it at admission, in the gate's hold (before every request and before the store) and in
    `_recovered`, including a revision with no learner state of its own.
  - With nothing inherited the payload has no key: exactly as before.

## Gate (this fix step; the full suite runs once in the landing gate)

Every pytest run was inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`, `-n 6` at most,
one at a time, with `TMPDIR` outside the worktree.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **40 kept, 0 broken** (after the last source change) |
| Fail-first on the pre-fix sources | F2: the interleaving test failed (the gap got `unlinked`). F3/F4: 5 of the 7 new tests failed and 2 passed (the unmarked-row pin and the second F3 reading), and the existing 9 passed. F1: the tag did not exist, and the predecessor cases are the old behaviour the (b) commit had replaced. |
| Figure lane (34 files: every `tests/test_figure*.py`, `tests/test_learner_data_relax*.py`, `tests/test_followups_nov2*.py`), after F3/F4 | **665 passed** |
| Chain and contract lane (81 files naming `SUCCESSOR_CHAIN`, `LATEST_ALGORITHM_VERSION`, `mvp-0.40/41`, `DEFAULTS_SNAPSHOT_BY_ALGORITHM`, `classify_config_path` or `parameter_registry`, plus `test_cli_help_snapshot`, `test_config_refactor`, `test_architecture`), after F1 | first run 1512 passed, **23 failed** (all chain pins that name the latest, tuple slices and the CLI help snapshot, as expected), 12 skipped, 6 xfailed. The 23 files plus `test_hint_h2b_fix3.py` and the successor test after the fixes: **457 passed**, 6 skipped, 3 xfailed |
| Hint and notes lane (177 more files naming `help_assists`, `hint_fold`, `hints_used`/`hintsUsed`, `request_hint`, `submit_dont_know`, `_server_hint_fold`, `retract_unlinked_notes`, `enqueue_learner_notes`, `notes.decide` or `learner_text_gap_reversals`), behind `flock /tmp/learnloop-fullsuite.lock` | **4462 passed, 1 failed**, 26 skipped, 2 xfailed. The failure was `test_hint_telemetry.py::test_the_report_cli_reads_the_vault_read_only`, which pins the `[hints]` section as configured and gains `fold_follows_attach`. Updated and rerun: **64 passed** |
| Durability: `--durable-sqlite` on `test_followups_nov2_note_gap_unlinked.py` and `test_learner_gap_unlinked_migration.py` (F2's transaction under WAL and `synchronous=FULL`) | **11 passed** |
| Contract tests: coordinated migrations, desktop RPC contract, mobile allowlist, public-tip guards, registry audit, sidecar serializer snapshot, SQLite file copies, table roles, tracked fixture databases | **383 passed** |
| Final run of the new and touched files: the three `test_followups_nov2_*` files, `test_learner_gap_unlinked_migration`, `test_help_fold_attach_successor`, `test_hint_telemetry`, `test_hint_h2b_fix3`, `test_cli_help_snapshot`, `test_config_refactor`, `test_architecture` | **196 passed** |
| DB/config reference: `db_generate_reference.py` then `db_validate_reference.py` (new config leaf; no schema change) | errors `[]` (after the prose leaf counts moved to 1112) |
| `validate_vault.py`, `desktop_validate.py` | pass (1377 notes; 305/305 TS + 6/6 Rust) |
| `module_validate.py` | fails with 1311 "missing expected note" issues across the whole package (the module catalog is not regenerated per stage). Unchanged by this step apart from one more module; left to the landing's documentation pass |
| Frontend, cargo | not run: no `apps/` change |

All 295 test files run in this step are listed in `docs/reviews/followups-nov2-codex-review.targeted-tests.txt`.

**One deviation:** one run started by mistake. A zsh glob that matched no files left an empty pytest argument list,
so pytest began collecting the whole suite (`-n 6`, inside the 5G scope). It was stopped within ten minutes, before
any result. No count from it is used, and the figure lane was rerun with an explicit file list.

Not run here (owner rule): the full suite, the whole durability lane, the whole vitest run.

## Open items for the landing

- **Renumbering mvp-0.41.** If teacher TE1 + C4 lands first as mvp-0.41, this successor becomes mvp-0.42 on top of
  it. That means: the constant; the upgrade module's predecessor (TE1's upgrade, whose completion it then hands down
  to); the snapshot key and its comment; the CLI help text and snapshot; and the test pins that name "mvp-0.41"
  (the successor test, the help-fold tests' tag, and the chain pins).
- **RW5d P3 (landing in parallel).** It replaces `_fold_rows`'s kind predicate with `HINT_EQUIVALENT_KINDS_SQL`. Both
  branches of the `any_session` split carry the same predicate line, so P3's constant goes into both. The predecessor
  branch must keep `'hint'` only if P3 itself is gated; otherwise P3's kinds apply in both, as P3 decides.
