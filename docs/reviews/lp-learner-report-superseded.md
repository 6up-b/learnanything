# Replaced learner claims kept (successor mvp-0.36)

Stage `lp-learner-report-superseded`, branch `lp/learner-report-superseded`
(worktree `learnanything-ad1`), base main `5c6a0834f`. The successor of the
Medium recorded at the rebuild-equivalence landing
(`docs/reviews/rebuild-equivalence-fix.md`; the strict xfail
`test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`).

## The defect

A learner report on an LO (a `too_easy` retirement, a rung-variant request
easier/harder) writes an LO-scoped claim and re-anchors the LO's mastery at
once. A second report of the same source on the same LO replaced the first
through `Repository.delete_learner_claims` (the replace seam), i.e. deleted
it. Its live re-anchor had already moved mastery, so replay, which applies
claims at their own point since mvp-0.33, could not apply a claim that was
gone: rebuild != live (Δmean -0.269 on `lo_diag`, one attempt then two
`too_easy` retirements). Every upgrade rebuilds, so a vault carries the
difference from then on.

## The design (the smaller one)

One nullable column and a version gate on the seam's write; no new table.

* **Migration 225** (`225_learner_claim_superseded_by.sql`):
  `learner_claims.superseded_by TEXT CHECK (superseded_by IS NULL OR
  superseded_by <> id)`, the id of the claim that replaced this one. NULL on
  every existing row. Classified as `metadata` in
  `adaptive_difficulty/column_classes.py`; `learner_claims` stays RAW_LEDGER
  (no new table, so no table_roles change).
* **The seam** is one repository method,
  `Repository.replace_learner_claim(claim, *, keep_replaced, clock)`: with
  `keep_replaced` it inserts the new claim and marks the in-force rows of the
  same `(source, scope_type[, scope_id])` `superseded_by` it, in one
  transaction; without it, it is exactly the predecessor's delete-then-insert.
  All three seam callers use it: `item_authoring._apply_difficulty_report`
  (learner_report), `rung_variants.request_rung_variant`
  (rung_variant_request), `learner_profile.seed_global_learner_claim`
  (init_wizard, global; the sidecar's `set_learner_profile` passes the
  vault's gate, bootstrap keeps the default since a new vault has no claim to
  replace). `keep_replaced = mastery.replaced_claims_kept(vault)` = version in
  `SUPERSEDED_CLAIMS_VERSIONS`.
* **Live readers are unchanged**: `Repository.learner_claims()` returns only
  rows with no `superseded_by` (filtered in Python, so a database attached
  below 225 still reads), which is exactly the set the predecessor's delete
  left. The three raw-SQL readers filter the same way: the AD replay's claim
  events (`adaptive_difficulty/replay.py`, column-guarded), the router card's
  self-reports (`daily_plan/router_card.py`), and the field's frozen priors
  (`field/priors.py`).
* **Replay** (`substrate/replay._ClaimStream`) reads every covering claim,
  replaced ones included (`covering_claims(..., include_superseded=True)`),
  places each at its own point (its recorded `applied_after_attempts`, else
  `(created_at, id)`), and re-anchors each re-anchoring one there, as live
  did. At any point the claims in force are the claims made by then minus
  those whose replacing claim was also made by then (`mastery._in_force`):
  the seed before the first attempt, each zero-evidence re-seed, and the
  re-review F8 variance retention (each anchor reads the claims in force at
  its own point, so a replaced anchor still counts the variance it left) all
  read that. The replacing claim is always made after the claim it replaces
  (its stamp, and its ULID within the same second), so it sorts after it.
  Live (`claims_made is None`) reads the claims in force, unchanged.

Below the tag nothing writes `superseded_by`, so replay reads exactly what it
read before at every older version (the strict xfail stays xfail there).

## Successor mvp-0.36

`SUPERSEDED_CLAIMS_ALGORITHM_VERSION = "mvp-0.36"`, appended to
`SUCCESSOR_CHAIN` after Reader CA2's mvp-0.35 (one constant; the upgrade, the
CLI and the gates read it). `SUPERSEDED_CLAIMS_VERSIONS` is the gate.
Defaults snapshot `mvp-0.36` recorded (no default changes; only the version
string moves the fingerprint). Upgrade `learnloop upgrade --to mvp-0.36` (the
bare upgrade's default now): `learnloop.superseded_claims_upgrade`, the same
journalled activation as mvp-0.33 to mvp-0.35 (one `BEGIN IMMEDIATE`,
manifest, `activate_p0_projection`, registry refresh, journal, publication
last; the chain's completion is now this module's, installed by the CLI and
the sidecar, handing earlier journals down the chain). It accepts mvp-0.35
and mvp-0.9 to mvp-0.34 through the chain.

**No kill switch** (decision for the owner's checkpoint, see open questions):
no live decision changes; a replaced row is read by replay only; switching
replay back would only restore a known rebuild/live divergence. The
playbook's kill-switch rule (mvp-0.27) is for changes to what is served or
admitted; this changes what replay can derive.

**What the activation moves: nothing.** A claim the predecessor replaced was
deleted and cannot be recovered, and no row is `superseded_by` at activation,
so the activation's rebuild derives what the predecessor's derived (tested:
only the row label differs). What changes is every later rebuild of an LO
whose claim is replaced from the tag on.

## Tests

* `tests/test_rebuild_equivalence.py::test_a_second_learner_report_on_an_lo_after_an_attempt_rebuilds_to_live`:
  strict xfail kept at mvp-0.33, mvp-0.34 and mvp-0.35; passes at mvp-0.36
  (and the latest).
* `tests/test_learner_report_superseded.py` (new):
  * the seam: a second report keeps the first as a replaced row no live reader
    reads; below the tag (mvp-0.33, mvp-0.35) the seam still deletes; a
    rung-variant request replaces only its own source on its own LO (0/0/0);
    two reports before any attempt seed from the latest with the variance each
    left (0/0/0, rebuild == live); the field's frozen priors read the same with
    the replaced row kept as with it deleted;
  * the starting level: an LO first practised under the bootstrap level
    rebuilds to live after the level changes (replay reads the replaced
    claim);
  * **property**: 24 seeded random histories of attempts (independent, hinted,
    primed, "I don't know"), `too_easy` retirements, rung-variant requests in
    both directions and tutor gap declarations, each history with at least
    one replaced learner_report or rung-variant claim (asserted; a closing
    replacement is added when the random part has none), then a primary load:
    shadow rebuild 0/0/0, and an applied rebuild (twice) leaves mastery exactly
    as live. The same generator at mvp-0.35 fails on all 24 seeds (checked once
    by hand, not committed), so the property is not vacuous;
  * the chain: one constant after mvp-0.35 and the latest, snapshot; upgrade
    from mvp-0.9, 0.30, 0.33, 0.34, 0.35; the bare upgrade targets it; refusal
    of mvp-0.8 and of a second upgrade; the activation derives what the
    predecessor derived; a real death after the publication (forked process),
    every opener completes an interrupted activation, every attach refuses
    without a completer, the upgrade completes its own journal, a failure after
    the rename leaves the predecessor, an mvp-0.35 journal is handed down, a
    torn journal is removed.
* `tests/test_learner_claim_superseded_migration.py` (new): 225 adds the
  column and nothing else; the head fixture holds 225 in rollback mode;
  durability lane.
* Head fixture renamed `migration_head_224` -> `migration_head_225`, rebuilt
  from the tracked sanitized copy with only 225 applied (README section);
  every hard-coded path and head pin updated (tests, `scripts/`, the two DB
  reference scripts, `SCHEMA_HEAD = 225`).

## Found here, not fixed (separate class)

`test_a_global_claim_made_after_materialization_rebuilds_to_live` (strict
xfail at mvp-0.35 and mvp-0.36): a claim that never re-anchors (an
init-wizard starting level, a manual claim) made after an LO's mastery row
was materialized (every LO is materialized at the vault's first sync) leaves
the live row as it was, while replay seeds the LO from the claims in force at
its first attempt, and an attempt-free LO from the claims in force at
rebuild time. Pre-existing and independent of the replace seam (one claim,
no replacement, reproduces it). It is why the property test does not change
the starting level; the starting-level test asserts only the LO practised
before the change. Fixing it needs the materialization point (or a
re-anchor for global claims), a separate successor.

## Gate (this stage; the full suite runs once at landing)

See the stage result for the exact commands and counts.
