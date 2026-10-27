# AD guard offer receipts: Codex review (2026-10-27)

Branch `fix/ad-guard-offer-receipts`, worktree `learnanything-dl2`. The review covered `5c6a0834f..6f256daac` on
gpt-6.1-sol. Codex job: `20261027-102834-TuL62U`. The stage record is `ad-guard-offer-receipts.md`. That file has
been corrected where the review showed its claims did not hold.

No source change in this step. No model call, no spend. The CLI ran only on fresh `copy_tree_with_databases`
copies of this worktree's `fixtures-local/owner-copies-20261027/*`, under `env -i` with existing empty `HOME`,
`CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and `LEARNLOOP_AI_PROVIDER=manual`.

## Review

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Restored live selection ships under existing algorithm tags | **reproduced; successor rejected.** The per-vault rollback is pinned by a new test, the two wrong claims are corrected, and the in-place change goes to the owner at the checkpoint (open question 1) | `0e6013b6c` | `tests/test_ad_guard_offer_receipts.py::test_the_fix_changes_serving_on_the_affected_shape_and_the_switches_restore_the_refusal_state`. Reasons below |
| — | — | Claim: "the incumbent-serves fallback is not a specified state" | **accepted, corrected** | `0e6013b6c` | Stage record §5. The fallback is the specified *response to a denial* (A8 round 2, D25, owner 2026-10-21). What is unspecified is a denial of a read the rules exist to make |
| — | — | Claim: "all three owner copies pass doctor" | **accepted, corrected** | `0e6013b6c` | Stage record verdict and §6. Doctor fails on all three copies (1, 47 and 48 errors). A new baseline run shows these are the same content codes and counts as on the un-upgraded copies, so the upgrade adds no doctor error (below) |

### F1: reproduction

The finding is confirmed. On the affected shape, the stage changes what is served under the same tags.

The new test builds that shape: a vault at the AD tag that holds an earlier answer picked from a published offer,
plus a hard slot that AD substitutes when it can. It serves the plan three ways:

- **Base behaviour (simulated).** `scheduler_offer_receipts` is taken out of `protected_tables.ROLES`, which was
  the only reason for the denial on the serving path. Every operation's first denial is that table, refused as
  "an unclassified table". AD makes no draw, and the incumbent serves the slot.
- **The fix, default switches.** Zero denials. AD draws (an `ad_selections` row) and serves a different first
  item. This is the change F1 names.
- **The fix, the vault's six AD2+AD3 switches false** (`successor.SWITCHES`). The served steps and the plan
  records match the refusal run field for field, and AD makes no draw.

### F1: why no successor

1. **The predecessor is a refusal, not an algorithm.** Before the fix, the same vault refused every AD operation
   that reads field's rows:
   - serving, the dose offer, commissioning and readiness all failed closed;
   - `ad report` and `rebuild-derived-state` crashed with `ViewDenied`;
   - the mvp-0.31 → mvp-0.35 upgrade chain stopped at mvp-0.32, inside its own rebuild.

   A switch that "restores the predecessor exactly" would have to restore that crash. A version-gated registry
   would then block the owner's probability vault from ever reaching the successor tag. The finding's other
   remedy, gating only the serving operations below a new tag, would keep a known registry defect running on
   purpose at mvp-0.30..0.35 so that a refusal can be reproduced.
2. **Persisted meaning does not change.** This is the playbook's step-1 test, and the rebuild-equivalence
   precedent (its F4, successor mvp-0.34) turned on exactly this question. There, a projection that rebuilt
   before rebuilt differently. Here:
   - every vault that rebuilt before rebuilds row-identically (stage record §5: linear_algebra and arxiv_v2,
     every `DERIVED` table);
   - the golden fixture does not move;
   - no default, fingerprint, schema or migration changes;
   - on the affected vault no AD row was ever written under the denial, so no recorded history contradicts the
     specified behaviour.
3. **The standing ruling covers what is left.** The serving change itself falls under the owner's standing
   ruling of 2026-10-12/13, applied in `plan-determinism-codex-review.md` F2 and `ux-phase1.md`: live changes go
   behind kill switches, not successors. The kill switches already exist and are per vault: AD23's six switches,
   pinned against mvp-0.29 by `test_ad23_successor.py` and `test_ad2_serving.py`.
   - Codex objected that disabling AD "globally" also disables AD that worked on unaffected histories. These
     switches live in each vault's own `learnloop.toml`. Of the owner's vaults, only probability holds the shape.
     The new test pins that, on that shape, the switches serve exactly what the refusal served.
   - The AD1 receipts (`forecast_receipts`) were also poisoned on that vault and have their own switch.
4. **It is not an in-place amendment.** The playbook requires an owner decision for an amendment, meaning a
   change to what a version specifies. AD23 (mvp-0.30) specifies that AD reads field's rows through the view
   with zero denials; that is its contract test. The fix brings the code back into line with that
   specification. It does not change the specification.

Because the playbook reserves in-place exceptions to the owner, the decision is still put to the owner at the
checkpoint (open question 1). The plan-determinism F2 ruling did the same.

### Doctor baseline (added in this step)

Doctor ran on fresh copies of the three pristine owner copies, without upgrading them (`doctor --json`; exit 1
each; error codes counted, no learner text):

| | linear_algebra | arxiv_v2 | probability |
|---|---|---|---|
| before the upgrade (this step) | `layout:missing_directory` 1, `sqlite:migrations_missing` 1 | `criterion:unknown_dependency` 46, `layout:missing_directory` 1, `sqlite:migrations_missing` 1 | `criterion:unknown_dependency` 46, `yaml:invalid` 2, `sqlite:migrations_missing` 1 |
| after the upgrade (stage record §6) | `layout:missing_directory` 1 | `criterion:unknown_dependency` 46, `layout:missing_directory` 1 | `criterion:unknown_dependency` 46, `yaml:invalid` 2 |

The upgrade clears `sqlite:migrations_missing` and adds nothing.

## Gate (this step; the full suite runs once, at landing)

- `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2`.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest:
  `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6` over the six
  files listed below. Result: **99 passed, 3 skipped** in 137 s. The skips are the owner-vault-gated cases of
  `test_ad23_successor.py`.
- Also run alone: `tests/test_ad_guard_offer_receipts.py`, 5 passed.
- Not needed, because nothing in these areas changed in this step:
  - no source, migration, schema or DB code, so no durability lane and no DB reference scripts;
  - no frontend change, so no vitest or build;
  - no `src-tauri` change, so no cargo check.

Test files run in this step:

- `tests/test_ad_guard_offer_receipts.py` (changed)
- `tests/test_ad_guard_reachable_reads.py`
- `tests/test_ad_protected_tables.py`
- `tests/test_ad_guard.py`
- `tests/test_ad2_serving.py`
- `tests/test_ad23_successor.py`

The stage's wider targeted run (66 files) is recorded in the stage record, §7 and §8.

## Open questions for the owner

1. **The in-place fix (F1).** On a vault holding an answer picked from a published offer (of yours, only
   probability), AD has been unavailable since mvp-0.30. This fix makes it serve under the existing tags.
   - Accept the in-place fix, as recorded here.
   - Or ask for a tag. If so, it would be folded into the next successor at its landing, not minted alone.
   - To keep the incumbent-only state on that vault meanwhile, set the six AD2+AD3 switches (and
     `forecast_receipts`, if wanted) to false in its `learnloop.toml`.
