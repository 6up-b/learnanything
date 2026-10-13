# Route check in the grader: one grading call

Stage `route-check-in-grader`, branch `grading/route-check-in-grader`,
worktree `learnanything-merge4`, base `e238fa07a` (main at mvp-0.17,
migrations to 186).

**Owner decision (2026-10-13).** The separate proofs-and-explanations route
check of mvp-0.17 is redundant machinery. It made three moves:

1. an LLM read the item's kind;
2. an independent call re-derived the learner's route on
   `ai.routing.proof_check`;
3. a deterministic gate applied the result.

Fold it into the grader's prompt: one grading call, keep the protective core,
and delete as much code and config as the playbook allows.

**Commits.**

| Commit | What |
|---|---|
| `21aa4e733` | mvp-0.17 replay fixture and its exact-replay test, passing on the base code |
| `f2aa47537` | the change |
| `44d3c340b` | regenerated DB/config reference |
| (this commit) | the playbook note and this record |

## What was deleted

Counts are `git diff --numstat e238fa07a f2aa47537`.

| Where | Lines |
|---|---:|
| `src/` in total | +792 / −1,822 (net **−1,030**) |
| `tests/` in total (the change commit) | +1,187 / −1,567 (net −380) |
| `src/learnloop/attempts/proof_check.py`, deleted | −1,286 |
| `tests/test_proof_route_check.py`, deleted (replaced by `tests/test_route_rules_in_grader.py`, 589 lines) | −1,187 |
| `cli/app.py`: the `attempt` command's route-check planning, admission and dry-run estimate, reverted to its pre-mvp-0.17 form (its help is byte-identical to before mvp-0.17) | +28 / −110 |
| `attempts/attempts.py`: `checked_run`, the checker calibration suffix, judgment and clarification plumbing, `GradingCallPlan.proof_check` | +29 / −71 |
| `attempts/regrade.py`: the regrade's check, `kept_hold_run`, the route-check judgment | +11 / −46 |
| `attempts/grading_admission.py`: reverted to pre-mvp-0.17 (no `route=`/`client=`) | +11 / −23 |
| `diagnosis/grading_hardcases.py`: checker and item-kind roles, (grader, checker) pairs | +120 / −187 |
| `ai/routing.py` (the `proof_check` task and its two operations) and `offline_review/spend.py` (the `proof_check` spend route) | −7 and −3 |

**Removed from serving:**

- the item-kind reading call (`ItemKindReading`, `classify_item`, judgment
  task `proof_like_item`);
- the re-derivation call (`ProofRouteCheck`, judgment task
  `proof_route_check`);
- `proof_check_route` and `resolve_check_client`;
- `ai.routing.proof_check`. It is retired, not an error: an old config that
  sets it, or sets `ai.route_output_tokens.proof_check` /
  `ai.route_reasoning_effort.proof_check`, still loads, and the value is
  ignored. `doctor` reports `config:retired_route` for the route key itself;
- the `proof_check` spend route and its dry-run and admission planning;
- the checker calibration suffix (`+proof-route-check-v3:…@<checker>`);
- the restored, disputed and flagged outcomes, the `disputed_fatal` and
  `questioned_unlocated` states and `RESTORED_CRITERION_LABEL`;
- producing the `route_check_disagreement` clarification trigger. Migration
  186 stays: it is append-only, and mvp-0.17's rows stay valid under its
  CHECK.

**Added:**

| Where | Lines | What |
|---|---:|---|
| `attempts/grading_support.py` | +299 / −26 | the rule, the prompt text, and `revalidated_support` moved here from `proof_check.py` |
| `route_rules_upgrade.py` | +133 | the playbook's upgrade function |
| `algorithm_versions.py` | +35 | the successor tag and its version gate |

## What was kept (folded in)

### 1. The rules in the grader's prompt

`grading_support.ROUTE_RULES` is appended after PF-c's reference-policy rules.
The reference policy gains `route_rules = "own-route-v1"`. The grader is told:

- grade every criterion on the learner's own route;
- a criterion phrased in one method is met by any valid method that
  establishes the same fact;
- mark a criterion down only by quoting the failing step verbatim (an
  `error_attribution` naming it, whose `first_divergence` quote comes from the
  answer);
- when it cannot verify a different route, say so (evidence plus
  `unverified_criterion_ids`) rather than mark it down.

It keeps reporting `route_check.divergent_route`, with
`route_check.rederivation_md` restating the route step by step.

The rules apply to every graded item that has PF-c's reference policy. No
classification is needed.

### 2. One deterministic rule over the grader's output only

`grading_support.apply_route_rule` runs inside `request_blind_grading_run`,
right after PF-c's gate.

- **When it applies.** The route is one the grader reads as divergent, the
  conclusion is not `differs_from_reference`, and the grade has no fatal
  error. Then every criterion below full points that no attribution in force
  locates is **unlocated**.
  - "Locates" means a quote that occurs verbatim in the answer, ignoring
    case and whitespace.
  - "In force" means not the grader's interpretation.
  - Unlocated is unverified, so unassessed (P1). PF-c's stamp goes on the
    evidence row, under the unassessed interpretation.
- **Fabricated quotes.** A quote that is not in the answer locates nothing.
- **The hold.** When nothing is then assessed and nothing validated the
  answer (no verified final answer), the grade is **held for review**.
  - It keeps the grader's own score and applies no FSRS review.
  - Its review reason is `grade_held_for_review`.
  - It goes through the existing predicate (`outcome_contract.grade_is_held`
    and `learnloop.held_grades`), exactly as mvp-0.17's "unlocated" outcome
    did.
- **What the rule never touches.**
  - The final-answer check outranks it: a conclusion that
    `differs_from_reference` is never unassessed.
  - Fatal errors keep their mark-downs.
  - PF-c's own unverified criteria (a verified final answer) are not this
    rule's.
- **Attributions.** Once the rule unassesses a mark-down, two kinds become
  the grader's interpretation, as PF-c rescopes them:
  - attributions on unverified criteria;
  - attributions that name no criterion and locate nothing. A blank or
    unknown criterion id names no criterion (held-grade-evidence F1).

  So an unlocated claim never keeps the attempt a measured failure.
  `revalidated_support` recomputes `assessed_shortfall` over the validated
  grade, as before.
- **The record.** It is written on the blind record under the key the held
  predicate reads, `grading_support.proof_route_check`:
  - `version = route-rules-in-grader-v1`;
  - `rules = own-route-v1`;
  - `status = checked` (the rule ran over this grade);
  - `applied`, `final_answer_status` and `divergent_route`;
  - `unlocated_criterion_ids` and `unverified_criterion_ids`;
  - `held_for_review` and `assessed_shortfall`.

  PF-c's keys are rewritten over both rules, so every reader treats the
  outcome as PF-c's: `unverified_criterion_ids`,
  `valid_alternative_gate_applied`,
  `valid_alternative_gate = {final_answer, proof_route}` and
  `assessed_shortfall`.

### 3. The held-grade predicate and its readers

They are unchanged. `grade_held_for_review` and `grade_is_held` are
byte-identical in code; only docstrings name the new writer. Holds are still
released the same two ways:

- by a regrade: a record without the hold;
- by an owner adjudication: assessed tier-4 rows.

`record_held_for_review` (replay's record half) moved to `held_grades`.
`HOLD_KEPT_FROM_KEY` and `PRE_HOLD_ROUTE_CHECK_VERSIONS` stay for mvp-0.17's
records. The rule has no separate call that can fail apart from the grade:

- a failed regrade writes nothing, so the hold stays;
- a regrade whose grader again locates nothing holds again.

`kept_hold_run` is gone with the check.

### 4. The hard-case gold set and `learnloop grading hardcases`

Both stay, re-pointed to the grader alone (harness `grading-hardcases-v3`).

- **Roles.** `grader` only, with the production prompt
  (`mvp-2.1-blind-reference-policy+own-route-v1`), under the same R2 arms.
- **The path.** Each route's `gate` is now its production path: PF-c's gate,
  then `apply_route_rule`, reported as `rule = {held, unlocated, unchanged}`.
- **Clients.** It resolves clients on the `grading` route.

A harder gold set can now show whether a second model is ever worth adding
back: compare a route's raw grader with its production path.

## Versioning ruling (playbook)

**Removing the check needs no tag.** mvp-0.17's own kill switch defined
"mvp-0.17 without the check": `proof_check.enabled = false` grades new answers
exactly as mvp-0.16 (`test_the_kill_switch_and_the_predecessor_grade_exactly_as_mvp016`
at the base). Serving that permitted state is within the tag's documented
semantics. An mvp-0.17 vault now grades new answers that way whatever the
switch says.

**No check code is kept for vaults pinned at mvp-0.17.** The playbook needs
their history to stay interpretable and reproducible, and replay reads only
the blind records, the evidence rows and the ledgers. It never reads the
check. The proof:

- `fixtures/mvp017_route_check_replay` is a vault graded at the base with the
  check's own fakes, holding every outcome the check could write;
- it replays exactly on the new code (below);
- the only pieces kept are data-level: the predicate's
  `PRE_HOLD_ROUTE_CHECK_VERSIONS` and `HOLD_KEPT_FROM_KEY`, and migration 186.

The decision is recorded beside the version (`algorithm_versions.py`) and in
the playbook's recorded-decisions paragraph.

**The new rules change grading for new answers, so they ship as a
successor.**

- **The tag.** `ROUTE_RULES_ALGORITHM_VERSION = "mvp-0.18"`, a **placeholder**.
  The sources track takes mvp-0.18/0.19 on main, so it is relabelled at the
  merge. It is appended to `SUCCESSOR_CHAIN`, so `LATEST_ALGORITHM_VERSION`
  and every version set follow. New vaults start there.
- **The gate.** `ROUTE_RULES_VERSIONS`. `PROOF_ROUTE_CHECK_VERSIONS` is
  deleted: nothing runs the check.
- **Kill switch.** `[proof_check] enabled` is kept, as the switch of the new
  rules. Off, new answers grade as mvp-0.17 now does (as mvp-0.16). No new
  config section.
- **Upgrade.** `route_rules_upgrade.upgrade_to_mvp018`:
  - It is chained after `upgrade_to_mvp017` and accepts mvp-0.17, or mvp-0.9
    to mvp-0.16 through the chain.
  - It passes chained notes through (`chained_notes = list(chained.notes or
    [])`).
  - T1's guard stays advisory. Refusal is tested with
    `config="[recurrence]\nrequire_guard = true"`, and the vault stays at
    mvp-0.10.
  - It refuses jumps and prepares the projection before the atomic config
    rename. Nothing is rewritten.
  - `learnloop upgrade --to mvp-0.18` is the default.
- **Calibration identity.** The checker suffix is gone. The new prompt rules
  change the scoring rules, so S1 §4.3 says calibration never pools them with
  the rules-free grader. The blind plan therefore names them, with one static
  suffix and no per-grade computation:
  - prompt: `…+own-route-v1`;
  - calibration identity:
    `grading_prompt_v2_1_blind_reference_policy+own-route-v1`.

  It is the same whatever the rule did to a grade. mvp-0.17's suffixed
  identities stay on its records and replay as written.
- **Defaults.** Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry was recomputed,
  ten in all. Each moves only because the effective config loses
  `ai.routing.proof_check`. mvp-0.18 has its own entry. The template
  `__pycache__` `.pyc` was deleted before and after.
- **No migration.** No new table either (playbook item 5).
- **Regenerated.** The CLI help snapshot (`attempt`, `upgrade`, `grading
  hardcases`). The DB/config reference: schema head 186, 308 table notes,
  763 configuration leaves in 46 sections, and `db_validate_reference.py`
  reports 0 errors.

**Playbook item 7: shadow rebuild.** Run on a backup-API copy of
`linear_algebra` (`fixtures-local/shadow_la`).

1. The copy was upgraded mvp-0.8 → mvp-0.9 → mvp-0.17 (advisory guard
   notes passed through) and rebuilt twice to its fixed point.
2. `learnloop rebuild --shadow` at mvp-0.17 showed 0 changes in facets (79),
   mastery (21) and schedule (99).
3. It was then upgraded to mvp-0.18, and `learnloop rebuild --shadow`:
   - facets: 0 changes;
   - schedule: 0 changes;
   - mastery: 21 rows changed, and the only differing field is
     `algorithm_version` (mvp-0.17 → mvp-0.18), as at every successor.

The live database hash was unchanged by each shadow rebuild. The tracked
`fixtures/linear_algebra/state.sqlite` hash was the same before and after
(copied with the backup API only).

**Playbook item 8.** `test_head_fixture_predecessor_to_successor_path` in
`tests/test_mvp018_upgrade.py`: on a copy of the head fixture set to mvp-0.17,
it runs the upgrade, the foreign-key check, doctor and an idempotent rebuild.

## Test evidence

**Fail-first at the base.** `e238fa07a` was exported to
`fixtures-local/tmp/base_e238fa07a` and run with its own `src`.

- `tests/test_route_rules_in_grader.py` fails at collection: `ImportError:
  cannot import name 'ROUTE_RULES_ALGORITHM_VERSION'`.
- A behavioural probe (the same scenarios at the base's latest, mvp-0.17)
  failed all three tests:
  1. *Exactly one model call on a proof item.* Base:
     `['blind_grading', 'proof_item_classification', 'proof_route_check']`.
  2. *An unlocated mark-down on a divergent route is unassessed using the
     grader's output alone.* Base: with no second model the mark-down stays
     assessed (`attribution_json = None`).
  3. *A fabricated quote counts as unlocated.* Base: the mark-down stays
     assessed.

**New and re-pointed tests (all pass on `f2aa47537`).**

`tests/test_route_rules_in_grader.py` (24 tests, 27 cases). The pure rule:

- an unlocated mark-down on a divergent route is unassessed;
- nothing assessed and nothing validated is held, while one criterion at
  full points, or a verified final answer, is not;
- a fabricated quote, or one only in the grader's interpretation, locates
  nothing;
- a verbatim quote (any case or spacing) keeps the mark-down;
- `differs_from_reference` outranks the rule;
- fatal errors keep their mark-downs;
- the rule reads only a divergent route;
- PF-c's own criteria are not the rule's;
- a whole-answer attribution that locates nothing is rescoped.

Prompt and identity:

- the rules and the `+own-route-v1` identity apply only at mvp-0.18 with the
  switch on, and compose with `+stuck-v1`.

Live door:

- **One model call** and one admission on a proof item. No second client is
  built, and no `proof_like_item` / `proof_route_check` judgment is written.
- Unlocated is unassessed.
- **Held.** The grader's own 0/4, the schedule untouched, no surprise, the
  follow-up suppressed, no diagnosis, and replay keeps it.
- A regrade keeps the hold until the grader validates the route.
- An adjudication releases it.
- A wrong final answer is never unassessed, with PF-c on and off.
- The kill switch and mvp-0.17 grade exactly as mvp-0.16 (same columns, the
  same evidence rows, the base identity, no rules in the prompt).
- The rules' identity is on the record, the raw event, the regrade and
  replay.
- Same-version replay equivalence holds, with no model.

Also:

- the retired route is ignored and reported;
- `learnloop attempt --dry-run` plans one call;
- migration 186 keeps its trigger.

**Replay of an mvp-0.17 vault.** `tests/test_mvp017_route_check_replay.py` (3
tests). It passed on the base (`21aa4e733`) and passes on the new code.

- The fixture holds every outcome: restored; restored plus disputed; a
  `route_check_disagreement` clarification; flagged; unlocated; held; a hold
  kept by a failed regrade check; an adjudicated hold; not proof-like;
  unavailable; a differing final answer.
- A rebuild changes no derived row and no row of `practice_attempts`,
  `grading_evidence`, `blind_grade_records`, `judgment_ledger` or
  `grading_clarifications`. `raw_grade_events` is append-only and gains a
  replay event per grade at every version, so it is compared without its
  surrogate ids.
- Every grade, hold and calibration identity matches `expected.json`.
- Upgrading the copy to mvp-0.18 rewrites no grade and no ledger row.

**Other files.**

- `tests/test_mvp018_upgrade.py` (11) is new.
- These were re-pointed:
  - `tests/test_mvp017_upgrade.py` (10; mvp-0.17 is now a link, not the
    latest);
  - `tests/test_held_grade_evidence.py` (19). Live holds now come from the
    grader alone. The synthetic holds stay mvp-0.17 records, which the
    predicate still reads. F2 now pins "a failed regrade writes nothing and a
    regrade that validates nothing holds again";
  - `tests/test_held_grade_composition.py` (10; renamed from
    `test_proof_check_composition.py`, without the three checker-budget
    tests);
  - `tests/test_grading_hardcases.py` (11; the grader alone, the production
    path, and unlocated, fabricated and verbatim quotes);
  - the earlier upgrade tests, for LATEST = mvp-0.18.

## Live check: the grader alone on the hard cases (OpenRouter)

**Setup.**

- **Where.** Gold set v2 (16 cases, synthetic smoke coverage), production
  arm, two fresh repetitions. The vault was a backup-API copy of the
  `linear_algebra` copy above (`fixtures-local/route-rules-eval`, at
  mvp-0.18). The app loaded its own key; no tracked vault was opened.
- **Judges.**
  - `or_haiku`: `anthropic/claude-haiku-5.5`.
  - `or_luna`: `openai/gpt-6-luna`, `reasoning_effort = low`.
- **Prices and cap.** $0.10 / $0.50 per million input / output tokens; total
  cap $1.

**How it ran.**

1. **Dry run first:** 64 calls, upper bound $0.73, inside the cap.
2. **First live run** (cap $1). Every Haiku request was refused with HTTP 400
   under `response_format = "json_schema"` ("The compiled grammar is too
   large"). Those 72 physical requests were refused, unbilled, and counted as
   failed cases. Luna completed.
3. **Haiku switched to `json_object`**, as in the mvp-0.17 runs. A second dry
   run gave the same plan.
4. **Second live run** (cap $0.90, so both runs stay under $1). Luna was
   served from its checkpoints and only Haiku was sent.

**Spend.** Provider-reported cost from the copy's receipts: **$0.1184 in
total**.

| Run | Billed | Requests |
|---|---:|---:|
| First (Luna, plus the refused Haiku requests) | $0.0243 | 68 |
| Second (Haiku) | $0.0941 | 32 |

All 200 receipts are in the copy.

**Results.** Repetition 0 for the rates; the noise floor is over both
repetitions.

| Route | Grader raw: wrong rejection (cells 1-2) | Grader raw: wrong acceptance (cells 3-4) | Production path (PF-c + rule): wrong rejection | Production path: wrong acceptance | Failed | Changed across repeats |
|---|---|---|---|---|---|---|
| Haiku 5.5 | **0/8** | 0/7 | 0/8 | 0/7 | 1 (3 invalid outputs over 2 reps) | 0/14 |
| GPT-6 Luna | 1/8 | 0/8 | 0/8 (1 unassessed) | 0/8 | 0 | 0/16 |

**Reading it.**

- **The cell-1 determinant case shows the in-prompt rule working for one
  model.** In `la-det-row-reduction-checkable` the `minors` criterion is
  phrased in the reference's method.
  - Under mvp-0.17's prompt every grader marked it down in every arm.
  - Haiku now gives it full credit in both repetitions. The prompt's "a
    criterion phrased in one method is met by any valid method" reached the
    grade.
  - Luna still marks it down in both repetitions. PF-c's gate (the final
    answer verifies) leaves it unassessed, so the production path rejects
    nothing.
- **The rule itself.** It applied once on Haiku (one unquoted mark-down on a
  divergent route, `rule = unlocated`) and changed no outcome. On Luna it
  never applied: neither grader produced an unquoted mark-down on a divergent
  route that PF-c had not already handled.
- **Wrong acceptance stays 0** for both. The rules did not make either grader
  lenient on the flawed or wrong cases.
- **Haiku's failures.** Three invalid outputs under `json_object` on two
  cases (`pr-variance-difference-linearity-claim` in both repetitions,
  `la-singular-matrices-subspace` once). They count as failed, never as
  acceptances. mvp-0.17's runs saw the same class of Haiku failure.
- **What the numbers can show.** On this set the grader alone, through the
  production path, matches the mvp-0.17 gate: 0/8 wrong rejection and 0/8
  wrong acceptance, with intervals up to 0.32. So the set gives no evidence
  that a second model is worth adding back. As before, it cannot rank routes:
  it needs harder and real cases, real traces in cells 3-4 above all.

Reports: `fixtures-local/route-rules-eval-reports/` (JSON and markdown), not
committed.

## Gate

Run on the tree at `44d3c340b` (the code commit `f2aa47537` plus regenerated
reference docs; later commits are docs only), with `TMPDIR` set to the
worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **15 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **9414 passed**, 0 failed (6 min 31 s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **96 passed**, 9318 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: schema head 186, 308 table notes, 763 configuration leaves in 46 sections |
| CLI help snapshot | regenerated (`attempt`, `upgrade`, `grading hardcases`) |

- **Not applicable.** No file under `apps/learnloop-tauri` or `migrations`
  changed, so the npm and cargo steps do not apply. The schema did not
  change.
- **An earlier run.** A full-suite run before the help snapshot was
  regenerated had two failures: the snapshot itself, and the load-sensitive
  `test_sidecar_reader_p3_slice2.py::test_invoke_preset_commit_enqueues_synthesis_and_proposes`.
  Both passed alone, and the gate run above is clean.

## Open questions

1. **Relabel at merge.** mvp-0.18 is a placeholder. When the sources track
   takes mvp-0.18/0.19, the following are relabelled:
   - `ROUTE_RULES_ALGORITHM_VERSION`;
   - the defaults snapshot key;
   - the upgrade's name and its CLI branch;
   - the tests' literal tags;
   - the reference docs.
2. **Kill switch name.** `[proof_check] enabled` is kept as the rules' switch
   to avoid config churn. A clearer name (for example `[route_rules]`) would
   need a config migration of its own.
3. **The calibration identity suffix.** `+own-route-v1` is kept on new grades
   because the prompt's scoring rules changed (S1 §4.3). If the owner meant
   "no suffix at all", the base identity would pool these grades with
   mvp-0.16's.
4. **Haiku 5.5 refuses strict schemas.** OpenRouter refuses the blind
   grader's `json_schema` response format for Haiku 5.5 ("compiled grammar is
   too large"). With `json_object` it sometimes returns invalid output
   instead (3 of 32 here). A vault that routes grading to Haiku through
   OpenRouter would see the same.
5. **Method-phrased criteria.** Luna still marks down a criterion phrased in
   the reference's method, even with the in-prompt rule. PF-c protects the
   checkable case. A proof whose final answer cannot be checked would rely on
   the grader quoting nothing for the rule to apply. Two ways to close the
   gap:
   - phrase rubric criteria by the fact established, not the method;
   - build a gold-set case without a checkable answer.

## Landing onto main

Branch `merge/route-rules-onto-main`, from main `e8d261405` (the sources
track mvp-0.18/0.19 with migrations 187-195, and facet locks with 196-197;
head fixture `fixtures/migration_head_197`). No migration, no paid call.

| Commit | What |
|---|---|
| `1e3b56d76` | a real `--no-ff` merge of `grading/route-check-in-grader` (`745641edc`, unchanged), with the relabel and the composition |
| `f80d34cc1` | regenerated references |
| `5b005a4af` | this section, first part |
| `c8c3caaea` | main `c50dd0bcb` (UX Phase 1, migrations 198-199) merged in (below) |
| `6906db6b4` | references regenerated again |
| (this commit) | the gate and parity |

### Relabel: mvp-0.18 becomes mvp-0.20

Main already uses `mvp-0.18` (`SOURCE_REFERENCE_GATE_ALGORITHM_VERSION`, the
answer-key gate) and `mvp-0.19` (`SOURCE_FIRST_NEEDS_ALGORITHM_VERSION`,
source-first needs). The route rules are chained after them as **mvp-0.20**,
so `LATEST_ALGORITHM_VERSION` is `mvp-0.20` and new vaults start there.

- `ROUTE_RULES_ALGORITHM_VERSION = "mvp-0.20"`, appended to `SUCCESSOR_CHAIN`
  after the two sources tags; `ROUTE_RULES_VERSIONS = {mvp-0.20}`.
- `route_rules_upgrade.upgrade_to_mvp020` accepts `mvp-0.19`, or `mvp-0.9` to
  `mvp-0.18` through `sources_upgrade.upgrade_to_mvp019`. It passes the
  chained notes through (`chained_notes = list(chained.notes or [])`), and a
  refusal already named by an earlier step passes unprefixed (as in
  `sources_upgrade`). T1's guard stays advisory; the refusal test sets
  `config="[recurrence]\nrequire_guard = true"` and the vault stays at
  `mvp-0.10`.
- `learnloop upgrade --to mvp-0.20` is the default; `--to mvp-0.18` and
  `--to mvp-0.19` still reach the sources tags.
- The branch's `tests/test_mvp018_upgrade.py` collided with main's file of the
  same name. It is now `tests/test_mvp020_upgrade.py`; main's file is kept.
- Every route-rules mention of `mvp-0.18` in code, comments, tests, the
  playbook note and the reference generator now says `mvp-0.20`. The sources
  track's own `mvp-0.18` mentions are unchanged. §0-§9 above, and the Codex
  review, describe the branch and keep its placeholder.

### What the deletion means for main's sources tags

mvp-0.17's kill switch defined "mvp-0.17 without the check". `mvp-0.18` and
`mvp-0.19` inherited the check, so they now grade new answers in that state
too, as `mvp-0.16` did. Their own semantics are unchanged: the answer-key gate
and source-first needs. The version-gate tests say so:

- `tests/test_mvp017_upgrade.py`: the route rules are off at `mvp-0.17` to
  `mvp-0.19` and on at `mvp-0.20`;
- `tests/test_mvp018_upgrade.py`: main's test pinned `proof_check_active` at
  `mvp-0.17` to `mvp-0.19`, so it now pins `route_rules_active` false there;
- `tests/test_route_rules_in_grader.py`: the kill-switch equivalence test
  gains a `sources_predecessor` case, `mvp-0.19` graded exactly as `mvp-0.16`.

### Composition

- **Removed symbols.** Main's sources and facet-locks code never imported
  `attempts.proof_check`, `PROOF_ROUTE_CHECK_VERSIONS`,
  `ai.routing.proof_check`, the `proof_check` spend route or the checker
  calibration identity. A grep of `src`, `tests`, `apps` and the reference
  scripts finds no reader left. Every `learnloop` module imports.
- **Removed test file.** Main edited `tests/test_proof_route_check.py` (version
  literals and the head-fixture path), and the branch deleted it. It stays
  deleted. Its migration-186 test lives on in
  `tests/test_route_rules_in_grader.py`, now pointed at
  `fixtures/migration_head_197`.
- **Held-grade readers the sources merge added.** These read the hold only
  through `learnloop.held_grades`, which the branch keeps (adding
  `record_held_for_review`):
  - `substrate/intervention_outcomes.py`;
  - `instructional/valuation.recent_assisted_success`;
  - `instructional/policy.attempt_window_open`.

  A hold written by the own-route rule is excluded from them exactly as an
  mvp-0.17 hold was. Only a docstring changed.
- **`judgment_ledger`.** `own_route_rule` and the legacy `proof_route_check`
  supersession read and supersede only their own task's current row
  (`left_kind = 'attempt'`). The other writers use other tasks:
  - facet locks: `facet_manual_authority`, with `facet_registry_saves`;
  - sources: `attempt_reference_binding` (`left_kind = 'practice_attempt'`)
    and the import's `same_target` pairs.

  In a regrade's publication transaction, `bind_replacement_grade` (C3)
  writes its row and the route verdict follows it. Neither reads the other's
  task. `append_judgment` and the table are unchanged on main.
- **Defaults.** All twelve `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (mvp-0.9
  to mvp-0.20) were recomputed with `defaults_fingerprint_for_version`, from
  the composed defaults (the sources sections, the facet reword confirm,
  minus `ai.routing.proof_check`; after the UX Phase 1 merge, its keys too).
  The template `.pyc` was deleted before and after.
- **Regenerated.**
  - The CLI help snapshot: `attempt`, `upgrade`, `grading hardcases`.
  - The DB/config reference: 318 table notes, 794 configuration leaves in 47
    sections after the UX Phase 1 merge (main's 795, less the retired route;
    317 and 787 before it). `db_validate_reference.py` reports 0 errors and
    `validate_vault.py` passes.
  - The hand-written counts in `Configuration.md` and `Database.md`.
  - `Version Registry.md`, which was still at `mvp-0.17` and head 186 on main,
    now reads `mvp-0.20` and 199.
- **The replay fixture.** `fixtures/mvp017_route_check_replay` stays at
  migration 186. A copy migrates forward to 199 on load, and its exact-replay
  test passes on the composed code. Its README says so.

### Merging UX Phase 1 (main `c50dd0bcb`)

UX Phase 1 landed on main first: migrations 198-199, head fixture
`fixtures/migration_head_199`, and no successor (the reading step is the
`plan.reading_from_furthest` switch). Main was merged in as `c8c3caaea`.

- **Defaults snapshots.** UX Phase 1's template note comes first, then the
  route rules'. All twelve entries (mvp-0.9 to mvp-0.20) were recomputed from
  the composed defaults, and the template `.pyc` was cleared.
- **Removed test file.** Main moved `tests/test_proof_route_check.py` to head
  199; it stays deleted.
- **Head fixture.** The branch's own head paths now name
  `migration_head_199`:
  - `tests/test_route_rules_in_grader.py`, whose max-migration assertion is
    now 199;
  - `tests/test_mvp020_upgrade.py`.
- **`tests/test_reading_step_switch.py`.** It pinned the latest tag as
  mvp-0.19. It now pins the route rules' mvp-0.20, still with no
  reading-step tag.
- **Generated files.** References are main's in the merge and regenerated
  after (`6906db6b4`). The CLI help snapshot is unchanged by `--write`.
- **`apps/`.** It is identical to main's, so the frontend and cargo steps do
  not apply.

### Gate

Run on `6906db6b4` with `TMPDIR` set to the worktree's
`fixtures-local/tmp`, after `uv sync --extra dev --extra mobile` and
`uv pip install pypdfium2`.

| Step | Result |
|---|---|
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,177 passed**, 0 failed (8 min 59 s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,078 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` | **0 errors**: head 199, 318 table notes, 794 leaves in 47 sections |
| `validate_vault.py` | passed |
| Frontend and cargo | not applicable (`apps/` identical to main) |

Phase 1, before main moved, ran a targeted selection of 48 files (797
passed).

### Parity

**Setup.** Backup-API copies of `fixtures/linear_algebra` and
`fixtures/probability` were made in `fixtures-local/route-rules-parity`. The
tracked fixtures are at migration 155 and `mvp-0.8`. Each copy was migrated
to 199 (`migration_coordinator.migrate_vault`) by one of two codes:

- main `c50dd0bcb`'s, exported with `git archive` and run on `PYTHONPATH`;
- the merge's.

On each copy the commands were `learnloop rebuild --shadow --json` and
`learnloop doctor --json`, with `LEARNLOOP_CONFIG_DIR` pointed at an empty
directory.

**Shadow rebuilds match main's.** Minted ids, timestamps and the live
database hash differ; the copies were migrated at different times. Set
aside, the JSON is identical.

| Fixture | Facet | Mastery | Schedule |
|---|---:|---:|---:|
| linear algebra | 22 | 6 | 47 |
| probability | 2 | 1 | 1 |

These are the fixtures' existing drift at `mvp-0.8`, the same as at the UX
Phase 1 landing. `live_database.unchanged` is true on every run.

**Doctor JSON matches main's** once the copy's path is set aside.

| Fixture | Issues | Errors | `criterion:unknown_dependency` |
|---|---:|---:|---:|
| linear algebra | 106 | 1 | none |
| probability | 134 | 49 | 46 |

The exit status is 1 on both sides, as on main.

**Playbook item 7, on the composed code.** A third copy of `linear_algebra`
went through these steps:

1. It was upgraded `mvp-0.8` → `mvp-0.9` → `mvp-0.19` (the advisory guard's
   notes passed through).
2. It was rebuilt twice to its fixed point.
3. `rebuild --shadow` at `mvp-0.19` showed 0 changes in facets, mastery and
   schedule.
4. It was upgraded to `mvp-0.20` (the default target).
5. `rebuild --shadow` showed facets 0 and schedule 0. Mastery showed 21 rows,
   whose only differing field is `algorithm_version` (`mvp-0.19` →
   `mvp-0.20`), as at every successor.

The live database was unchanged by every shadow run, and the tracked
fixtures were only copied: `git status fixtures` is clean.
