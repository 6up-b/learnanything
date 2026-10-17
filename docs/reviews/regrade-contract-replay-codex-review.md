# Regrade contracts (mvp-0.26): Codex review and fixes

**Stage:** `regrade-contract-replay`, branch `fix/regrade-contract-replay`, worktree `learnanything-codex-sandbox`.
**Reviewed:** through `8945d7eec` (Codex job `20261016-105608-OKcfWL`). The stage record is [regrade-contract-replay.md](regrade-contract-replay.md).
**Fix commits:** `a636f4f6d` (code, tests, and the amended claims in the stage record and the architecture vault) and `5df25755f` (one comment kept line-neutral, so the configuration reference's source-line citations stay exact), then this record.
**Paid calls:** none. Every test uses fakes. The parity run replays backup-API copies with an empty config directory.

## Review

### Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Failed upgrades leave successor holds active under mvp-0.25 | fixed | `a636f4f6d` | `tests/test_regrade_contract_upgrade.py`: `test_a_failed_activation_leaves_the_predecessor_exactly_as_it_was[after_rebuild, during_activation, after_activation, at_publication]`, `test_a_failed_commit_after_publication_restores_the_predecessors_label`, `test_an_upgrade_interrupted_after_publication_is_resumed`, `test_no_writer_interleaves_between_the_scan_and_the_publication` |
| F2 | Medium | Adjudications allocate revisions before acquiring the write lock | fixed | `a636f4f6d` | `tests/test_regrade_contract_successor.py`: `test_an_adjudication_allocates_its_revision_inside_its_own_transaction[adjudication, regrade]` |
| F3 | Medium | Same-second legacy regrades bypass the unknown-contract hold | fixed | `a636f4f6d` | `tests/test_regrade_contract_successor.py`: `test_a_regrade_in_its_pre_contract_grades_second_is_held_not_read_as_its_only_grade[same_second]` (control: `[a_second_later]`), `test_only_a_grade_no_later_write_replaced_is_an_attempts_only_grade` |

No finding was rejected.

### Fail-first

The new tests were run against the reviewed code: `git archive 8945d7eec src migrations` was placed first on `PYTHONPATH`, and pytest's `pythonpath` was overridden so the worktree's `src` did not shadow it. **11 of the 13 new cases fail there.** The 2 that pass are the controls: the one-second-later regrade, and the existing `test_upgrade_holds_exactly_the_unrecorded_epochs_and_rewrites_no_evidence`, run alongside as a sanity check. The log is `fixtures-local/regrade-contract/failfirst-review.log` (gitignored).

| Case | On `8945d7eec` | After `a636f4f6d` |
|---|---|---|
| F1, failure after the rebuild, during the activation's projection, after it (registry refresh), and at the config rename | The database differs from the predecessor's: learner state was replayed, the holds were recorded, and receipts and registry rows were written. The label stays mvp-0.25. | The whole database (every row of every table) equals the predecessor's, the label is mvp-0.25, and nothing is held. Rerunning the upgrade succeeds. |
| F1, a commit that fails after the publication | No publication happened inside a transaction, so nothing restored the label. | The config named mvp-0.26 and was restored to mvp-0.25. The database equals the predecessor's. |
| F1, a process killed after the publication (a subprocess calls `os._exit` right after the rename) | The database already held the successor's state. | The database equals the predecessor's under the mvp-0.26 label. Doctor reports `sql:derived_state_rebuild_stale`. Rerunning the upgrade completes the activation, and the attempt rows and learner state then equal those of an uninterrupted upgrade. |
| F1, another writer at the scan and at the publication | Both the database write lock and the vault lock were free (`(False, False)`). | Both are held at both points (`(True, True)`), and both are free after the commit. |
| F2, two adjudications interleaved before the transaction | Both took revision 1. The history shows `revision:0, revision:1`, so the first adjudication is lost. | Revisions 1 and 2. The history shows `revision:0, revision:1, revision:2`. |
| F2, an adjudication interleaved with a successor regrade | Revision 1 collided with the regrade's, and the adjudication cited the original's contract (maximum 4). | Revision 2. It cites the regrade's contract (maximum 8): 2 of 8 = 0.25, now and after a rebuild. |
| F3, the same-second legacy regrade, maximum later lowered to 6 | (3, 0.5), not held. | (3, 0.375), held (`grade_contract_unrecorded`). |

### F1: one activation across the database and the config

**Cause.** The upgrade committed its replay, its activation receipt and its registry refresh, each in its own transaction, before the config rename. The held-grade predicate reads `grade_contract_unrecorded` at any label. A rename that failed (or a process that died before it) therefore left the successor's learner state and holds under the predecessor's label. mvp-0.25's replay passes the reason through, so no predecessor rebuild could undo it.

**Fix** (`src/learnloop/regrade_contract_upgrade.py`):

- **One lock and one transaction.** The upgrade runs under the vault mutation lock. One `BEGIN IMMEDIATE` transaction covers:
  - the predecessor's manifest;
  - the scan of the attempts it holds;
  - the replay of exactly their learning objects;
  - the activation projection and its receipt;
  - the registry refresh.
- **The publication is the transaction's last step.** The config is written, fsynced, atomically renamed, and its directory is fsynced. The commit follows, so after a power loss the rename is never older than the commit.
- **A failure before or at the publication** rolls back. The predecessor's database is exactly as it was, and its config still names mvp-0.25.
- **A commit that fails after the publication** rolls back too, and the config is restored to mvp-0.25. If that restore also failed, the vault would be left in the resumable state below.
- **A process that dies between the publication and the commit** leaves the mvp-0.26 label over the untouched mvp-0.25 database. Every earlier successor leaves the same transient state until a rebuild (its learning objects keep the predecessor's stamp), and doctor reports it. The reverse state, successor state under the predecessor's label, can no longer occur.
- **Resume.** `learnloop upgrade --to mvp-0.26` on a vault already at the tag completes an activation that did not commit. It does so only when the predecessor's state is still there: an attempt the successor holds without its recorded hold, or mvp-0.25's rebuild receipt as the latest. It reports `Upgraded vault: mvp-0.26 -> mvp-0.26` with the note "completed the interrupted activation of mvp-0.26". Otherwise it says "vault is already mvp-0.26", as before. Any rebuild at mvp-0.26 completes it too.
- **Concurrent writers.**
  - A regrade or an adjudication on another connection waits for the transaction (`busy_timeout`). It lands before the scan or after the commit, never between them.
  - An item edit or a proposal accept takes the vault lock, so it waits as well, and then loads the published config.
  - As with every upgrade, an app left running keeps the label it loaded until it reloads. A regrade it writes uncited after the commit is held by the next replay at mvp-0.26 (no evidence), never misread.

### F2: the adjudication's reads are inside its transaction

**Cause.** `append_adjudication_evidence_revision` read the live rows, the current epoch, its contract and the next revision before it entered `repository.atomic()`. A writer that committed in between made both writes take the same revision. `ordered_epochs` then merged them, losing the earlier adjudication from feedback's history, and a concurrent regrade left the adjudication scaling by the contract the regrade had superseded.

**Fix** (`src/learnloop/attempts/grade_resolution.py`). The public function now opens the transaction first and runs the whole body inside it: every read it decides on and the publication. The inner scope is a savepoint of that transaction. Below the tag, the written values are unchanged; only their serialization moved.

### F3: "the attempt's only grade" means one write

**Cause.** `only_epoch` asked whether every row of the attempt fell under one epoch key. A revision-less regrade stamped in its pre-contract original's second shares the key `legacy:<created_at>`, so the regrade passed as the attempt's only grade. It was then read against today's item, instead of being held.

**Fix** (`src/learnloop/grading_epochs.py`, `only_grade`, which replaces `only_epoch`; called from `attempts.current_epoch_reading`). One write qualifies when:

- its rows share one key;
- **none is superseded**, since a grade's rows are only ever superseded by a later write;
- **they carry at most one grading run**, since one write has at most one `agent_run_id`, and a joint grade's self-graded tier carries none beside its model tier.

Either sign of a second write disqualifies the compatibility reading, and the epoch is held like any other later uncited epoch. The epoch grouping itself is unchanged, so feedback, the timeline and the projection group as before.

**Owner data.** Neither owner copy has an attempt whose rows all cite no contract, so nothing there changes. In `linear_algebra`, the 6 attempts with a superseded uncited regrade all have a current first grade that cites its contract, so the rule is never consulted for them. The one held attempt was already held.

### The review's other claims and its conformance table

- **"If this step fails … the vault stays at the valid mvp-0.25."** This now holds (F1). The stage record's §3 item 3 states the failure, commit-failure and crash cases.
- **"The number is read and written inside the grading's own `BEGIN IMMEDIATE` transaction."** This now holds for adjudications (F2). The stage record's §2.2 says so.
- **"Two epochs of one attempt never share [a revision]."** This holds for every writer at the tag (F2, plus the regrade, which already read inside its publication).
- **"Every non-first uncited epoch is held rather than divided by today's maximum."** This holds (F3). The stage record's §2.4 states the one-write rule.
- **The working live kill switch** is not a numbered finding. It remains the stage's open question Q1, decided by default (no switch: the earlier writer is the defect, and replay reads what each epoch recorded; rollback is restore-only). The owner can override it at this checkpoint.
- **Migrations and DERIVED ownership:** unchanged. There is no schema change, and migration 207 stays free.
- **Serving and reveal-ledger scope:** unchanged.

### Parity (backup-API copies; no model call)

Fresh copies of `fixtures-local/regrade-contract/orig/{linear_algebra,probability}` were made with `learnloop.db.copies.copy_tree_with_databases` into `fixtures-local/regrade-contract/run2/upgrade/`. `LEARNLOOP_CONFIG_DIR` was an empty directory and `LEARNLOOP_AI_PROVIDER` was unset. Each copy was upgraded `--to mvp-0.9`, then `--to mvp-0.26`, then `--to mvp-0.26` again, with this branch's code.

| Check | linear_algebra | probability |
|---|---|---|
| mvp-0.8 → mvp-0.9 → mvp-0.26 | upgraded; the note names `01KYCM9NYBGYDKGR2GGYQYSV23` | upgraded; no note |
| the held attempt | `01KYCM9N…`: (4, 1.0, held, `grade_contract_unrecorded`), as in the stage record's §7 | none held |
| the third run (`--to mvp-0.26` again) | "vault is already mvp-0.26" (nothing to resume) | "vault is already mvp-0.26" |
| latest receipts | `p0_projection_activation` and `learning_object` at mvp-0.26 | `p0_projection_activation` at mvp-0.26 |
| `agent_runs` / `model_call_receipts` / `grading_evidence`, before → after | 105 / 0 / 115 → 105 / 0 / 115 | 24 / 0 / 4 → 24 / 0 / 4 |

The outcome is the stage record's, value for value. F1 changes how the activation commits, not what it writes, and F3 changes no attempt in either vault. The output is in `fixtures-local/regrade-contract/run2/upgrade.txt`.

## Gate

Run in the worktree on `5df25755f` (the final code), with `TMPDIR=<worktree>/fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`:

| Check | Result |
|---|---|
| `uv run --no-sync pytest tests/test_regrade_contract_{upgrade,successor,replay}.py -n 4` | 63 passed |
| `uv run --no-sync lint-imports --no-cache` | 22 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -n auto` | 12331 passed, 2 xfailed, 0 failed (21 min 8 s, under heavy machine load). The 2 xfails are main's strict ones. The 12 tests beyond the stage gate's 12319 are this fix's new cases. |
| `flock /tmp/learnloop-fullsuite.lock uv run --no-sync pytest -m durability` | 106 passed, 12227 deselected |
| DB and config references | no schema change; the config reference's source-line citations stay exact (`5df25755f`) |
| CLI help snapshot, RPC pins, frontend, `cargo check` | unchanged; not run: nothing under `apps/`, no RPC or CLI surface changed |

No test failed, so no timing test needed a rerun alone. This gate was run again after a Claude Code restart (2026-10-16, about 21:35). The run from before the restart was not recorded. The logs are `fixtures-local/regrade-contract/gate-{full,durability}-resume.log` (gitignored).
