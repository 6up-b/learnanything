# Rebuild equivalence fix: Codex review and fix round (2026-10-25)

Branch `fix/rebuild-equivalence`, worktree `learnanything-ad1`. The stage record is
[`rebuild-equivalence-fix.md`](rebuild-equivalence-fix.md). The Codex review is codex-job
`20261025-175513-ifDYkE`. Every finding was reproduced first; the three that hold are fixed, and F2 is
rejected for this stage with its reproduction pinned as a strict xfail.

## Review

### Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Direct replay publishes incomplete vault-wide evidence | **fixed** | `fe25c1d23` | `tests/test_rebuild_equivalence_review.py::test_an_interrupted_integration_backfill_replay_publishes_nothing`, `::test_a_retry_after_an_interrupted_direct_replay_keeps_the_lifecycle` (durability lane; both failed first) |
| F2 | Medium | The new boundary assumes ID order equals commit order | **rejected** (out of scope; pinned) | `fe25c1d23` (the pin) | Pre-existing replay fold order; the fix needs a migration and a new ledger order everywhere. `::test_two_same_second_attempts_committed_in_reverse_id_order_rebuild_to_live` is a strict xfail. Reason below. |
| F3 | Medium | The golden test permits a non-idempotent rebuild | **fixed** | `c8a138009` | `tests/test_mvp017_route_check_replay.py::test_the_bounded_replay_corrects_the_copy_in_one_rebuild_and_then_changes_nothing` (failed first with the reconciliation disabled) |
| F4 | Medium | Historical projections change without a version boundary or kill switch | **fixed** | `c8a138009`, `9e32dff95` | The successor `mvp-0.34` behind `replay.ledger_bounded`; `tests/test_mvp017_route_check_replay.py::test_an_mvp017_vault_replays_its_grades_exactly` is the golden test again (`changed == []`); seven F4 tests in `tests/test_rebuild_equivalence_review.py` |

### F1 (High): fixed

**Reproduction.**
- The fixture: a vault at the latest tag with interleaved attempts on `lo_svd_definition` and `lo_diag`.
  A retired item with attempts is closed by a primary load.
- `apply_integration_backfill_and_recalibrate` replays `lo_svd_definition` with no enclosing
  transaction. A wrapper around `replay_existing_attempt` read the database from a second connection
  before the second attempt, then raised.
- Before the fix, that reader saw the reset LO with only its first attempt replayed. It saw the
  vault-wide canonical cache folded through that attempt, so `lo_diag`'s later evidence was gone. The
  failure left both, plus the retired item reopened, published.
- A direct `replay_learning_object` failed the same way. Its retry then snapshotted the item as active.

**Fix.** `replay_learning_object` runs in ONE `Repository.atomic()` transaction, from its first read
to its closing projection: the inactive-item snapshot, the reset, every attempt, the lifecycle
restoration, the misconception pass and the whole-ledger projection.
- Inside the umbrella rebuild or a regrade, it is a savepoint of the caller's transaction, so nothing
  changes for them.
- Under WAL another connection keeps reading the last committed state throughout, and an
  interruption rolls back to it, lifecycle flags included.
- File: `src/learnloop/substrate/replay.py`. The body moved to `_replay_learning_object`.

### F2 (Medium): rejected for this stage, pinned

**Reproduction.** The test gives two attempts on one item ids chosen out of order. B (the later id)
commits first; A (the earlier id) commits in the same second (a frozen clock). Live folds B then A.
Replay folds A then B. The rebuilt mastery differs from live, and the strict xfail records that.

**Why it is rejected here.**
1. **It is not this stage's boundary.** Replay's fold order, `list_attempts_by_learning_object` and
   the canonical observation ledger have all ordered by `(created_at, id)` since before this stage. So
   even the base code folds A then B: the mastery update order already differs from live in this case.
   - The bound makes each replayed attempt read exactly the attempts the replay has already folded.
     That is the only bound consistent with that fold order.
   - Before the fix, both attempts read each other.
   - The finding's case is a property of the ledger order, not of the bound.
2. **The fix is a new ledger order, which needs a migration.** The ids are allocated before grading,
   and `created_at` has second precision. So the only correct order is a commit sequence allocated
   inside the write transaction. That means:
   - a new `practice_attempts` column (a migration after 221);
   - a backfill rule for historical rows;
   - a new order for the replay fold, the canonical ledger and every bounded read.
   - That changes persisted meaning (its own successor), across modules this stage does not own.
3. **Proportionate protection (owner, 2026-10-24).** The case needs two grades of the same LO in
   flight at once, committing within one second in reverse id order. For one learner, that means the
   desktop and a phone grading at once. The effect is a rebuild-time mastery difference on that pair,
   and the next rebuild is deterministic. No learner-visible harm and no spend.

**What stays.** The strict xfail
`tests/test_rebuild_equivalence_review.py::test_two_same_second_attempts_committed_in_reverse_id_order_rebuild_to_live`
turns red when a commit sequence lands, so the pin is removed with the fix. Open question 1 below
proposes that follow-up.

### F3 (Medium): fixed

**Reproduction.** On the `mvp017_route_check_replay` copy with the bounded replay, rebuild 1 corrects
the three derived tables and appends a causal-hypothesis version. The `recurrence_groups` replayer runs
before learner replay, so `hypothesis_recurrence_state.input_fingerprint` is left one rebuild behind.
Rebuild 2 then changed it. The stage's version of the test skipped that comparison.

**Fix.** `rebuild_all_derived_state` finishes the reconciliation its own learner replay made
necessary (`src/learnloop/substrate/rebuild_orchestrator.py`):
- After the replayer passes, `_reconcile_recurrence_groups` refreshes the recurrence projection. That
  is a no-op unless the input fingerprint moved.
- If the group map that learner replay read changed with it, the passes run again.
- `MAX_RECURRENCE_RECONCILIATION_PASSES = 3` bounds the passes. It is a guardrail labelled `keep`: it
  bounds rebuild cost and is not a model parameter. After the last pass the projection is still
  restamped on its inputs.
- On the fixture the map is empty and unchanged, so the restamp is the whole cost.

**Test.** The rewritten test asserts the following:
- rebuild 1 moves exactly `attempt_surprise`, `learning_object_mastery`,
  `practice_item_quality_state`, `causal_hypotheses` (one appended version) and
  `hypothesis_recurrence_state`;
- the single-attempt LO and every grade stay as written;
- the **immediately following** rebuild changes nothing, the causal-hypothesis versions included (the
  audit compares them without surrogate ids and stamps);
- the ledgers are unchanged.

With `_reconcile_recurrence_groups` stubbed to return `False`, the test failed on
`hypothesis_recurrence_state`. The real function was restored before committing.

### F4 (Medium): fixed

**The decision.**
- The playbook's item 6 requires the same-version rebuild of the golden fixture to reproduce the same
  semantic projection.
- The only recorded in-place amendments are the owner's. The 2026-10-17 eligibility precedent minted a
  successor for an untagged change for the same reason.
- No owner decision in force exempts this change, so the bounded replay is now a successor.

**The successor.** `REPLAY_LEDGER_ALGORITHM_VERSION = "mvp-0.34"` is one constant, built on
`mvp-0.31`. RW7b and the LP claim fixes take `mvp-0.32` and `mvp-0.33`, and the landing chains this
one after them.
- **Gate.** `replay_reads_bounded_ledger(vault)` in `attempts.py`: `REPLAY_LEDGER_VERSIONS` and the
  kill switch `[replay] ledger_bounded` (default `true`). It is the only place
  `replay_ledger_position` is set, so every bound (the windows and both canonical folds) follows it.
- **Below the tag, or with the switch off,** replay reads the whole ledger exactly as before. The
  mvp017 golden test is back to `changed == []`.
- **A live write never reads the switch.** A test pins that the same history writes the same live
  state at `mvp-0.31` and at `mvp-0.34`.
- **Not gated, deliberately:**
  - F1's transaction (atomicity, not meaning);
  - F3's reconciliation (a no-op on a fixed-point vault);
  - the stage's lifecycle fix (1b). `practice_item_state.active` is the lifecycle owners' flag, not
    in the attempt ledger, and no version's replay has authority over it. It moves no golden row.
- **Upgrade.** `learnloop.replay_ledger_upgrade.upgrade_to_replay_ledger` takes `mvp-0.31` directly,
  or `mvp-0.9` to `mvp-0.30` through the chain. It refuses anything older.
  - The upgrade changes learner state, so it activates like the regrade-contract successor: one
    `BEGIN IMMEDIATE` transaction under the vault mutation lock, holding the predecessor's manifest, a
    whole-vault rebuild under the tag, the registry refresh, and the durable config publication last.
  - A failure rolls back, and the config still names the predecessor.
  - A process that died after the publication leaves the tag over the predecessor's database. Running
    the upgrade again completes it ("completed the interrupted activation").
  - The CLI's default target is the new tag (`--to mvp-0.34`).
- **Fingerprints.**
  - `DEFAULTS_SNAPSHOT_BY_ALGORITHM` gains `mvp-0.34`.
  - Every earlier snapshot was recomputed, because the effective config gains the key. It is inert
    below the tag, and every entry is annotated.
  - The key is classified in `parameter_registry` (structural / operational kill switch).
  - The config reference was regenerated (1,048 leaves, 71 sections) and validated.
- **Other places updated:**
  - the chain-tail pins in 22 test files;
  - the CLI help snapshot;
  - `pyproject.toml`'s production-module contract (`learnloop.replay_ledger_upgrade`);
  - the mvp017 fixture README;
  - the version table in `Concepts/Algorithm Versions and Reproducibility.md`.

**Tests** (`tests/test_rebuild_equivalence_review.py`):
- the tag is one constant after its predecessor, with its snapshot;
- the switch is on by default and classified;
- a live write is the same below and at the tag;
- below the tag, replay is the predecessor's (and differs from live on the oracle history);
- at the tag, replay equals live, and the switch restores the predecessor's replay exactly;
- the upgrade from the predecessor rebuilds to live, refuses a second time, and chains from `mvp-0.30`.
  It refuses `mvp-0.8`, and the CLI default reaches the tag;
- a failed publication leaves the predecessor's config and database byte-identical, and a died
  activation resumes to live.

### The review's other points

- **"Replay reads the ledger as the live write saw it."** It holds in ledger order. The
  reverse-completion, same-second case is F2: rejected here, pinned, and open question 1.
- **"Nothing between reads the cache."** It now holds for every caller: a per-LO replay is one
  transaction (F1).
- **Rebuild idempotency.** It is now asserted from the first rebuild to the second (F3).
- **No successor.** Withdrawn: the successor is `mvp-0.34` (F4).
- **The stage record.** `rebuild-equivalence-fix.md` carries a pointer above its §3 that its
  no-successor verdict is superseded.

### Open questions

1. **A commit sequence for the attempt ledger (F2's fix)** would be its own stage. It needs:
   - a migration adding a sequence allocated in the write transaction;
   - historical rows numbered in `(created_at, id)` order, so nothing that exists moves;
   - the replay fold, the canonical ledger and the bounded reads ordered by it.
   - This changes persisted meaning, so it is a successor.
   - The strict xfail is waiting for it.
2. **The owner's vaults at activation.** Upgrading to `mvp-0.34` applies the stage record's §3
   corrections once: on the `u31` backups, 8 LOs and 52 due times on linear_algebra, and 1 and 1 on
   probability. That is now a labelled successor activation rather than a silent rebuild change. The
   upgrade note can say so.
3. **Landing.** The tag is built as `mvp-0.34` after `mvp-0.31`. If RW7b (`mvp-0.32`) and the LP claim
   fixes (`mvp-0.33`) land first, the landing changes these:
   - `PREDECESSOR` and its upgrade in `replay_ledger_upgrade.py` (to `mvp-0.33`'s);
   - the chain-tail pins and the `SUCCESSOR_CHAIN[-N]` indices;
   - the snapshot comments.
   - The tag string itself stays.
