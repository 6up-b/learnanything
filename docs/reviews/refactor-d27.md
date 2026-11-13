# D-27: the A8 contract and `facet_uncertainty` (diagnosis)

Ledger row D-27. Branch `refactor/d27-ad-contract`, base `3cfd8ce6ec`. Nothing in production or in the tests changed; the strict xfail stays. Synthetic vaults only.

## Verdict

The test is wrong (answer 5b). `facet_uncertainty` is the incumbent's per-learning-object diagnostic state, written by the attempt pipeline from every answer, protected ones included. It differs between the copies because copy A holds attempts on protected items that copy B never has, exactly as `facet_recall_state` and `facet_capability_evidence` do. The contract's carve-out list (`OUT_OF_SCOPE`) names those two and was never told about the table that mvp-0.59 started writing. Adaptive difficulty cannot read the table, so no protected material reaches AD's outputs through it.

## 1. Reproduction and violations

`pytest --runxfail` on the test, in a 5G scope through an empty-home env wrapper, `AD23_CONTRACT_DIFF` set. The test appends every violation to that file (`tests/test_ad23_contract.py:210-213`). Exactly three violations, all in one row (`.writes.facet_uncertainty[0]`, the contract's "new rows of every table" comparison, `tests/ad23_contract_helpers.py:1203-1206`):

- `[0][3]` `hypothesis_marginal`: protected `{"facet_absent:recall":0.99999938,"facet_solid:recall":6.2e-07}`, absent `{...0.65,...0.35}`
- `[0][4]` `uncertainty`: 9.46e-06 vs 0.6474
- `[0][5]` `status`: `resolved` vs `resolving`

No other table, prompt, figure or sentinel differs. The same row's `apply_pub` twin does not appear because the final `_run` attempts touch `recall` only.

## 2. Writers

Every row is written by `attempts.complete_self_graded_attempt` -> `apply_attempt` -> `_apply_attempt_in_transaction` (attempts.py:3319, `write_facet_uncertainty=canonical_facet_uncertainty_on(vault)`) -> `_persist_attempt_application` (attempts.py:3972) -> `Repository.record_attempt_outcome` -> `_upsert_facet_uncertainty_state` (repositories.py:5969). The update is computed by `build_facet_uncertainty_updates` (attempts.py:4929), the posterior of each attempt being the next attempt's prior (attempts.py:4350-4361). I traced every upsert with a scratch plugin (`{SCRATCH}/plug/d27trace.py`, untracked).

- Shared base (`_base`, `ad23_contract_helpers.py:134,177`): two attempts on `lo_m1` at 09:00 and 21:00 on Oct 10 put `recall` and `apply_pub` at 0.966 then 0.9977 `facet_absent`, status `resolved`. Both copies inherit this.
- Copy A only, in `_protect`: attempts on `pi_shared` (a held-out current item), at lines 445, 446, 447 (all `correct=False`), `pi_hist` (472), and `_protect_r11` (538). These push `recall` from 0.99977 to 0.99999999 `facet_absent`, `last_evidence_at` 2026-10-12T08:35.
- Both copies, in `_run` (`ad23_contract_helpers.py:1028`): the harness serves two items and answers them (the `_attempt` call at line 1028), at 09:33 and 09:37. Copy A's posterior starts from 0.99999999 and ends 0.9999993 (`resolved`). Copy B's starts from 0.9977 and, with the harness's answers, ends 0.65 (`resolving`).

So the differing input is evidence from attempts on protected items (and the copy-A-only learner state that follows from them), carried in the prior of the next attempt. The writer reads no protected content (no item text, no span, no object that exists only in A): it reads the facet ids of the answered item and the grade.

## 3. Switch off and mvp-0.58

Scratch plugin `{SCRATCH}/plug/d27var.py` wraps the test's `ad23_vault` builder (nothing committed).

- `[facet_diagnostic] canonical_belief_fixes = false` at the head: the contract passes, no uncertainty row is written.
- A vault created at `mvp-0.58`: passes, no row written.

`facet_belief_fixes_on` (learner/facet_state_reader.py:59-71) is false below the tag or with the switch off, and `canonical_facet_uncertainty_on` (:74-80) then gates the write off. So mvp-0.59's D-5 introduced the difference; the same dependence on protected attempts held for the incumbent's other state tables all along.

## 4. Can AD read the table?

No.

- `facet_uncertainty` is in neither `protected_tables._ROLES` nor `column_classes._CLASSES` (grep of both: no hit). The guard's rule for an unlisted table is to refuse: `read_verdict` returns "an unclassified table" when `ROLES.get(table)` is None (protected_tables.py:747-754), and `test_ad_guard.py::test_an_unclassified_table_is_refused_in_every_scope` pins it in every scope. So the guard denies it, fail closed.
- No AD module imports a reader of it: grep of `src/learnloop/adaptive_difficulty` for `facet_uncertainty`, `facet_state_reader`, `facet_diagnostics`, `followups`, `goal_projection`, `valuation`, `reader_followups`, `promotions`, `question_signal` finds nothing. The readers are the follow-up slate, the goal projection, the tutor and the instructional valuation, all incumbent.
- The contract fails only because it compares the new rows of every table but `OUT_OF_SCOPE`'s (helpers.py:1203-1206). `facet_uncertainty` is not in `AD_DERIVED` (helpers.py:47), so the "DERIVED tables whole" comparison is not what catches it; the new-rows comparison is. The role change COMPAT -> DERIVED (table_roles.py:272) has no part in it.

## 5. Which side is wrong

(b), the test. `OUT_OF_SCOPE` (helpers.py:53-62) exists for "the incumbent's own answer pipeline, writing from the incumbent's state (which counts the protected answers by design)". `facet_recall_state` and `facet_capability_evidence` are there for the same reason, and `facet_uncertainty` is the same kind of row: a per-learner posterior that must count the learner's every answer, protected ones included, or the incumbent's own follow-up diagnosis would forget an exam answer. A8 forbids protected material from shaping what AD produces, and the evidence says AD cannot see this table. The strict xfail is accurate for the test as it stands, so it is the fail-first of the fix below.

Evidence for it beyond the trace: adding the entry to `OUT_OF_SCOPE` in a scratch plugin (`{SCRATCH}/plug/d27fix.py`, no tracked change) makes the whole contract pass under `--runxfail` (1 passed).

Unsure of: whether the owner wants the diagnostic layer protected from exam answers (production reading (a)). That would be a design change to the incumbent: the facet-belief successor deliberately feeds it every answer (refactor-dfb.md D-5, "the facet's uncertainty row opens on" the attribution), and the same would then hold for `facet_recall_state`, which A8 already carves out. I judge it not intended.

## Proposed fix (not made)

Smallest: in `tests/ad23_contract_helpers.py`, add to `OUT_OF_SCOPE`

    "facet_uncertainty": _INCUMBENT_ANSWER + " (per-LO diagnostic posterior, DERIVED since mvp-0.59; the guard refuses it inside an AD operation as an unclassified table)",

and drop the strict xfail on the test (`tests/test_ad23_contract.py:164-166`), so the `[default]` case is a plain pass. Optional hardening, a production-side change: classify `facet_uncertainty` as `DENIED` in `protected_tables._ROLES` with a `column_classes` entry (the two registries must match, `test_ad_protected_tables.py:105`); it changes nothing today (the guard already refuses the table) and makes the denial explicit instead of resting on the table being unlisted. The step that fixes it should run `test_ad_protected_tables`, `test_ad_guard`, `test_ad23_contract` and the pins.

## Not verified

The two scratch variants ran the one contract test only, not the rest of AD's tests at `mvp-0.58`. I did not exercise the live-vault upgrade path, nor check whether a non-synthetic vault's AD reads anything derived from `facet_uncertainty` through a table that is classified (the grep covers direct reads and imports; a classified table that the writer's `_persist_attempt_application` also feeds from the same transaction was not enumerated).
