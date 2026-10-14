# Decider migration, Tier 1 (`mvp-0.20`)

**Landed onto main as `mvp-0.22`** (see "Landing onto main" at the end). §1-§6
describe the branch and keep its placeholder `mvp-0.20`; on main, `mvp-0.20`
is the route rules in the grader and `mvp-0.21` value-of-information stopping.

Stage `decider/tier1-migration` (worktree `learnanything-decider`, base
`e8d261405`, the facet-locks landing). Owner-approved 2026-10-13: small
judgments move from LLM judges to the Decider (R0:
`perplexity/pplx-decider-v1.1-27b` on OpenRouter, `ai/providers/decider.py`),
the LLM kept as fallback; D6 (Perplexity's terms accepted; learner text may
go to the Decider). Codex implemented it uncommitted
(job `20261013-151831-P1re2U`); this review checked the diff against the
task, kept its design, finished what it left undone, committed it and ran
the gate.

| Commit | What |
|---|---|
| `3906ee6fb` | The review spend adapter moves to `learnloop.ai.review_spend` (re-exported by `diagnosis.offline_review.spend`) so content, field and ops can admit Decider requests without a diagnosis dependency |
| `4d5f11e03` | `learnloop.decider_judgments`, `ai.routing.tier1_decider`, `[decider_routes]`, the `mvp-0.20` successor and its upgrade, every defaults snapshot |
| `b3dca2b05` | (a) the facet span-support check, its card and its labels |
| `877ad6d3f` | (b) the Tier-1 routes |
| `7cf36ed9c` | (c) `learnloop decider agreement` |
| `4e2f0fb51` | `docs/decider-tier1-migration.md` (caller inventory), the config reference generator, regenerated references |
| `eba905b61` | Gate fix: a partial config without `[decider_routes]` stays on the predecessor path |

No migration, no new table, no new sidecar RPC, no `src-tauri` change. No paid
or network model call was made; every test uses fakes.

## 1. What changed

### 1.1 The shared decision (`learnloop.decider_judgments`)

One helper asks the Decider ONE typed `ChoiceQuestion` per judgment and takes
the **argmax of its probability distribution** (never the response's separate
`choice` field, never a hand-set threshold). The whole distribution is logged
on a `judgment_ledger` row (judge `decider`, the input hash, question set
`tier1-decider-v1`). When the Decider is unavailable, refused for spend or
failing, it returns no choice and ledgers a row whose verdict is the status
(`unavailable` / `refused` / `failed`, never an option of any Tier-1
question); the caller then runs its existing LLM judgment and ledgers that
verdict against the same input (`log_llm`), so the pair is real evidence. A
cancellation (`AIInterrupted`, `SpendCancelled`) propagates; it is never a
fallback.

Decider requests go through the existing spend path (`ReviewSpend.request`,
model-call receipts) at the profile's listed input price, about $0.0004 a
decision, with **no output allowance**: the Decider is exempt from the
output-budget policy. Every LLM fallback keeps its route's shared policy
(`learnloop.ai.output_budget`) and its own receipts.

The Decider is `ai.routing.tier1_decider`, a new Decider-only route (empty:
the code-default `openrouter_decider` profile; never a chat provider, never
`LEARNLOOP_AI_PROVIDER`, never a generic LLM fallback). `router_decider` is
never a Tier-1 judgment (`enabled()` is false for it). Learner-text gaps keep
their `learner_gap_decider` profile and route.

### 1.2 (a) The facet span-support check

At the facet-meaning chokepoint (`authority.check_meaning_write`), a
model-proposed change to a registered facet's meaning (claim, definition,
conditions, applicability, non-goals) whose contributions all cite
explanatory spans now asks the Decider one question over the validated,
in-scope spans (`ResolvedCitation.supports`: never exam or held-out text; each
span once) and the new wording: `supports` / `partly supports` / `does not
support` / `unrelated`.

| Outcome | Result |
|---|---|
| `supports` is the top option | applies, as before; the reword's history row keeps the check |
| `partly supports`, `does not support`, `unrelated` | held for the existing one-tap confirm (code `span_support`); the card says what the check found in plain words and shows longer excerpts (1200 characters) |
| Decider unavailable, refused, failing, or a span that cannot be read | held for the confirm ("could not be checked just now") |
| Exam-only support | refused first, unchanged; the Decider is never asked |
| The owner's Library edit, a confirm, an undo | never checked (only a proposal's apply attaches the check) |

Every model-proposed facet write reaches the check: synthesis, append and
consolidation output is staged as a proposal and judged again at its apply
(`ProposalAuthority.for_proposal`). Labels: the owner's confirm labels the
check `supports`; keeping the current wording, or undoing a reword the check
judged (one it held that the owner confirmed, or one it let apply), labels it
`does not support` (judge `owner`, `label_for` the check). These are the
owner's actions, not adjudicated entailment.

Switch: `decider_routes.facet_span_support` (every version: a content path,
no successor). With the reword confirm itself switched off
(`facet_identity.reword_confirm = false`) there is no card to hold a doubted
reword, so it is refused (fail closed), and the proposal's apply refuses.

### 1.3 (b) The routes moved at `mvp-0.20`

| Judgment (switch) | Typed question | LLM fallback | Notes |
|---|---|---|---|
| Learner-text gap pairs and "needed?" (`learner_gap_judge`) | same / different / unsure per same-prerequisite or same-belief pair (T1's `judge_pairs`, claims and reuse); yes / no / unsure | `learner_gap_judge`, only for the pairs the Decider failed | The Decider is authoritative for prerequisites and beliefs alike; a pair another worker holds defers the reading as before |
| Learner-text gap kind (`learner_gap_kind`) | the existing kind question | the context model's reading kind | The text-gap chooser's authority becomes the Decider; the context model still names the gap; a recorded Tier-1 kind is reused, never paid for twice |
| Misconception match (`misconception_match`) | one option per candidate registry belief plus `new` | the grading route's `misconception_match` | A path with no model client (replay, the worker) makes no call; split diagnosis keeps its own `registry_match` |
| Pattern links in `learnloop diagnose review` (`diagnosis_link_judgment`) | same / different / not_sure per blinded earlier answer | the `diagnosis_judge` batch, only for a link the Decider failed | An imported Decider link marked at `mvp-0.20` joins T1's recurrence groups at the LLM's authority; historical Decider rows never gain authority on replay |
| `learnloop field classify-questions` (`field_question_classification`) | the missing question type, and yes / no per catalog LO and facet, in one request | the configured classifier route (may be unset) | A catalog needing more than 128 questions in one request goes to the classifier |
| Contamination leak verdicts (`contamination_leak_judgment`) | `leak` (contaminated) / `clean` / `unsure` over the same two-text prompt | `contamination_judge` | The verdict is ledgered under the request's checkpoint id |
| Contamination reveal verdicts (`contamination_reveal_judgment`) | the same, with `reveal` | `contamination_judge` | as above |

Not moved: T1's same-cause judge (`same_cause_judge`: live, backlog and
`learnloop embeddings adjudicate`; its existing Decider/LLM pairs are read by
the agreement report), grading, diagnosis, re-derivation, authoring and
generation, the tutor, T6 span verification, and the proof-like item reading
(left alone for the parallel stage deleting it). The full caller inventory is
in `docs/decider-tier1-migration.md`.

### 1.4 (c) The agreement report

`learnloop decider agreement --vault PATH [--review-run DIR ...] --json`
reads `judgment_ledger` only (the vault's, plus any review run's scratch
ledger, where the pattern-link judgments live): no model call, no migration,
no write, no shadow pairing. Per task: the inputs both the Decider and an
LLM-family judge answered (one task, the same two entities in either order,
the same input hash; the latest answer of each), the agreement rate and a
Decider-by-LLM confusion matrix, the Decider's failures and the fallbacks they
handed over, and its calibration (multiclass Brier score and top-probability
bins) where an owner or verifier label exists. Without labels or pairs the
figures are `null`, never zero. T1's same-cause pairs and the pre-`mvp-0.20`
learner-text gap second opinions are included.

## 2. Versioning and switches

`mvp-0.20` is appended to `SUCCESSOR_CHAIN` after `mvp-0.19`
(`DECIDER_TIER1_VERSIONS`); new vaults start at it.
`sources_upgrade.upgrade_to_mvp020` chains through `upgrade_to_mvp019`
(`chained_notes = list(chained.notes or [])`, passed through a refusal too;
T1's guard at `mvp-0.12` advisory unless `recurrence.require_guard = true`).
It is a tag change plus an idempotent rebuild of the same projection
namespace: it changes what is served from now on (gaps created,
misconceptions matched, links), never the meaning of recorded history.

```toml
[decider_routes]            # each true by default
learner_gap_judge = true
learner_gap_kind = true
misconception_match = true
diagnosis_link_judgment = true
field_question_classification = true
contamination_leak_judgment = true
contamination_reveal_judgment = true
facet_span_support = true   # content path: every version
```

A serving switch acts only at `mvp-0.20`; false restores that judgment's
`mvp-0.19` path. Every `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entry was recomputed
(the effective config gains the section and the route); serving below
`mvp-0.20` is unchanged.

Rebuild evidence (playbook item 7): on backup-API copies of
`fixtures/migration_head_197`, one upgraded `mvp-0.18 -> mvp-0.19` and one
`mvp-0.19 -> mvp-0.20`, `learnloop rebuild --shadow` reports the same
learner-state diff field for field except the `algorithm_version` label
(the diff against the fixture's stored projection predates this stage), and
the live database hash is unchanged.

Side effects worth knowing:
- At `mvp-0.20` a contamination report's checkpoint ids include the Decider
  tasks, so a rerun re-judges (with the Decider) pairs the LLM judged before
  the upgrade; a review run's link passes judged by the other judge are
  judged again when the switch moves.
- After the upgrade, `classify-questions` asks the Decider once for questions
  the LLM classified before (the cache is keyed by judge); signals keep the
  first classification, so this costs a capped command's spend only.
- Without an OpenRouter key every cited model reword waits for the owner's
  confirm (the Decider is unavailable).

## 3. What the review changed

Codex's design was kept. Findings, each fixed:

1. **Calibration labels only on held cards.** An undo of a reword the check
   let apply was not labelled, so the agreement report could never calibrate
   the Decider's `supports`. The applied reword's history row now keeps the
   check and its undo labels it `does not support`.
2. **A span cited by two contributions was sent twice** in the question.
   Deduplicated.
3. **Text-gap Decider requests were admitted under `tier1_decider`** although
   served by the `learner_gap_decider` profile; `decide()` takes the caller's
   route and the receipts name the route used.
4. **The Tier-1 kind was paid for again** when a text was read again; the
   predecessor's second opinion reused its ledger row. A recorded Tier-1 kind
   is now reused.
5. **A partial config crashed** (`AttributeError` on `decider_routes`) in
   `classify-questions` (11 failures in the full suite). A config without the
   section stays on the predecessor path.
6. **Upgrade coverage.** `tests/test_mvp020_upgrade.py` now also covers the
   required guard's refusal from `mvp-0.10` (naming the `mvp-0.12` step) and
   the full walk after it, the advisory notes, notes through a refusal,
   idempotence and refusal of older versions, the CLI default and
   `--to mvp-0.20`, and that the judgments move only at the successor.
7. **References.** The config reference generator had no `decider_routes`
   section (it crashed); the switches and the route are described, the
   references regenerated and the prose counts fixed (797 leaves in 48
   sections). The CLI help snapshot was regenerated.

The Tier-1 tests were split by part: `tests/test_tier1_decider.py` (the shared
decision and the routes), `tests/test_facet_span_support.py`,
`tests/test_decider_agreement.py`.

## 4. Tests

Fakes only (`tests/structured_ai.py`, in-process Decider doubles whose
`choice` field disagrees with their argmax). Fail-first coverage per moved
route: the Decider decides; unavailable, failing and refused fall back to the
LLM with both rows ledgered; the switch reproduces the LLM path with no
Decider row; below `mvp-0.20` nothing moves. The span-support check: each
option and unavailability, exam-only refused before any call, Library edits
and synthesis resolvers never checked, the card's verdict and excerpt, the
confirm / keep / undo labels (held and applied), the switch, and the reword
confirm's kill switch. The ledger rows, receipts and the exemption from the
output budget. The agreement report: pairs in either orientation, fallbacks,
explicit and same-question labels, Brier score and bins, nulls, the
read-only CLI with a review run.

## 5. Gate

At `eba905b61`, `TMPDIR` under `fixtures-local/tmp`, `uv sync --extra dev
--extra mobile` plus `pypdfium2`:

- `uv run lint-imports --no-cache`: 17 contracts kept, 0 broken.
- `uv run pytest -n auto` (full suite, under the shared lock): 10057 passed.
  The first run, at `4e2f0fb51`, had 12 failures: 11 in
  `test_interaction_signals.py` (finding 5, fixed in `eba905b61`) and
  `test_sidecar_reader_p3_slice2.py::test_invoke_preset_commit_enqueues_synthesis_and_proposes`,
  timing under the machine's load (it passed alone, then in the full rerun).
- `uv run pytest -m durability`: 99 passed.
- `apps/learnloop-tauri`: `npm install` (up to date), `npm run typecheck`
  clean, `npm test` 54 files / 296 tests passed, `npm run frontend:build`
  built. `src-tauri` unchanged, so no `cargo check`.
- Regenerated: `tests/cli_help_snapshot.json`; the DB/config references
  (`db_generate_reference.py`, then `db_validate_reference.py` with no
  errors). No new sidecar RPC (the mobile allowlist is unchanged).
- `git diff --check` clean. The tracked fixtures were only read through
  backup-API copies under `fixtures-local/`.

## 6. Adversarial review of `e8d261405..356784102` and its fixes

The review's verdict was FINDINGS: 0 High, 6 Medium, 4 Low. Each finding was
reproduced by a test that failed on `356784102` before it was fixed; none was
rejected. Fakes only; no paid or network call.

| # | Finding | Reproduced by (failed first) | Fix | Commit |
|---|---|---|---|---|
| F1 (M) | The span-support check's Decider request (30 s timeout) ran while holding the vault mutation lock, which other writers wait on for 10 s | `test_the_span_check_is_asked_before_the_vault_lock_is_taken`: the Decider saw the `proposal_accept` holder | `apply_accepted_items` stages the acceptance once before the lock (`_ask_span_support`; nothing written but the checks' ledger rows) and keeps each verdict by input hash; under the lock the check only looks verdicts up (`with_span_support(asked=...)`), and one whose input changed meanwhile is `unchecked` and held for the confirm | `397a2bb40` |
| F2 (M) | With `facet_identity.reword_confirm = false` the check refused a cited reword (and the acceptance's closure) the old rule applied, a Decider outage included | `test_reword_confirm_off_applies_a_cited_reword_whatever_the_decider` (unavailable / does not support): `PatchApplicationError` | The check runs only under the reword-confirm policy; the kill switch restores the predecessor rule | `97a994360` |
| F3 (M) | The same-question label fallback scored one reword's span check against another reword's label (endpoints are `facet:<id>`) | `test_span_support_labels_never_leak_to_another_rewords_check`: 2 labels, accuracy 0.5 | For `facet_span_support` and `misconception_match` (`UNNAMED_CONTENT_TASKS`) a label binds only explicitly or on the same input hash | `7b2100493` |
| F4 (M) | `--review-run` double-counted failures and fallbacks: the scratch ledger is a backup copy of the vault's | `test_agreement_counts_each_ledger_row_once_across_a_review_runs_vault_copy` (backup-API scratch copies): `fallbacks 2` | `agreement_report` counts each row once by id | `7b2100493` |
| F5 (M) | Learner text reached the Decider at mvp-0.20 on routes Settings did not disclose; `learner_text_gaps.decider_enabled = false` was ignored | `test_settings_and_eval_judges_disclose_the_tier1_routes` (`KeyError`), `test_the_learner_text_gaps_decider_switch_still_keeps_learner_text_from_the_decider` (the Decider was asked) | `JUDGE_ROUTES` gains `tier1_decider` and `learner_gap_decider` with what is sent and when (Settings, `eval judges` with consumer status); `decider_enabled = false` makes the text-gap switches act as off at every version | `22264ea62` |
| F6 (M) | Contamination with one switch on and the other off: every request's checkpoint changed (paid reveal verdicts bought again), the up-front over-budget check was skipped, the LLM row's `input_hash` changed at every version | `test_contamination_one_routes_switch_restores_its_old_checkpoints_budget_check_and_ledger`: wrong `input_hash` at mvp-0.19, `cached 0` at mvp-0.20 | `decider_profiles` keys only a Decider-first task's requests on the Decider's profile (`judge_settings` is the base's again); the up-front check covers every LLM-first request under the budget it had before; an LLM row keeps the checkpoint hash unless it is a Decider fallback | `1ec841297` |
| F7 (L) | The review run's dry-run estimate, admission and resume binding ignored the Decider; a pass whose LLM fallback failed discarded the links the Decider had answered | `test_a_review_dry_run_plans_and_prices_the_deciders_link_calls` (`KeyError`), `test_a_review_resume_refuses_a_changed_decider_profile` (`complete`), `test_links_the_decider_answered_are_never_paid_for_again_when_the_fallback_failed` (4 calls, not 3) | The plan allows one Decider call per link per pass (the history's error limit per pass) at the listed input price; the dry run and the run register and bind `tier1_decider` from config; `decide(reuse=True)` returns an answer already ledgered for the same input, so an answered link is never asked again (no partial pass is written, so nothing is duplicated) | `79f048335` |
| F8 (L) | A tie for the top probability went to the first option (`supports`, `same`) | `test_a_tied_top_option_is_no_answer_and_hands_over`, `test_a_tied_batch_question_has_no_choice`, `test_a_tied_gap_pair_goes_to_the_llm`, `test_a_tie_between_supports_and_another_option_holds_the_reword` | `decider_judgments.argmax` returns None on a tie; the check is ledgered `tied` (a `FAILURE_VERDICTS` status) and goes where a failure goes (held, or the LLM); a unique top still decides, no cutoff | `ab54325c5` |
| F9 (L) | A pair's mvp-0.19 Decider second opinion (its choice field) was reused as the deciding mvp-0.20 verdict | `test_a_predecessor_second_opinion_is_never_reused_as_the_tier1_verdict`: `same`, not the argmax `unsure` | The Tier-1 pair executor's producer is the model marked `#argmax`; such a pair is asked once more, then reused | `f66d057cc` |
| F10 (L) | A confirm finished by recovery was never labelled; a keep that only closed a stale card was labelled `does not support` | `test_a_confirm_finished_by_recovery_labels_the_check`, `test_keeping_a_card_that_went_stale_is_no_label` | Recovery labels the confirm; a keep labels only when the facet's meaning is still the one the card was held on | `3e1ae05c1` |

Claims in §§1–4 that did not hold, now corrected (code where it was the code,
`docs/decider-tier1-migration.md`, the agreement module and CLI help where it
was the record):

- **T1's same-cause pairs.** T1's same-cause judge (live, backlog, guard,
  `embeddings adjudicate`) asks only the LLM and writes no Decider row, so it
  adds no pair to the agreement report; the only `same_cause` Decider rows are
  a review run's Tier-1 links. §1.3's "its existing Decider/LLM pairs are read
  by the agreement report" and §1.4's "T1's same-cause pairs ... are included"
  are withdrawn.
- **"false restores that judgment's mvp-0.19 path."** Now true for
  contamination with mixed switches and for the LLM row's `input_hash` (F6),
  and for `reword_confirm = false` beside the span check (F2: §1.2's "refused
  (fail closed)" is withdrawn; the check is not asked).
- **"A cancellation propagates; it is never a fallback."** It propagates out
  of the decision and never reaches an LLM fallback; misconception matching
  catches it as it always caught its LLM's cancellation (grading never stops
  on it) and takes the deterministic text match, now pinned by
  `test_a_decider_cancellation_in_misconception_matching_never_reaches_the_llm`.
- **The read-only CLI with a review run.** Now tested with backup-API scratch
  copies (F4).
- **Calibration where a label exists.** Labels no longer cross between checks
  of different wordings (F3).

`docs/decider-tier1-migration.md` records the new behaviour (ties,
cancellations, disclosures, the text gaps' Decider switch, the `#argmax`
producer, reused review links and the run's Decider plan and binding,
contamination's per-task keys, the span check before the lock, labels).

### 6.1 Gate after the fixes

At `36823fcdb` (the fixes, the docs and the regenerated references), `TMPDIR`
under `fixtures-local/tmp`:

- `uv run lint-imports --no-cache`: 17 contracts kept, 0 broken.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: 10078 passed.
- `uv run pytest -m durability`: 99 passed.
- Regenerated: `tests/cli_help_snapshot.json` (the agreement command's help);
  the DB/config references (`db_generate_reference.py`, then
  `db_validate_reference.py` with no errors). No migration, no new table, no
  new sidecar RPC, no `apps/learnloop-tauri` change (so no frontend or cargo
  run): Settings renders the two new disclosures from the existing
  `judges` list.
- `git diff --check` clean. No tracked fixture was opened.

## Landing onto main

Branch `merge/decider-onto-main` (worktree `learnanything-merge2`), from main
`21440c9cf` (value-of-information stopping `mvp-0.21` LATEST, with UX Phase 1,
the route rules in the grader `mvp-0.20` and the EVSI multi-family study;
migration head 201, head fixture `fixtures/migration_head_201`). No migration,
no new table, no new sidecar RPC, no `src-tauri` change. No paid or network
model call; the tracked fixtures were only read through backup-API copies.

| Commit | What |
|---|---|
| `3a6c3fb81` | a real `--no-ff` merge of `decider/tier1-migration` (`b1c7ace3f`, unchanged), with the relabel, two composition fixes, the landing tests, the recomputed snapshots and the regenerated references |
| (this commit) | this section |

### Relabelled

| On the branch | On main |
|---|---|
| `mvp-0.20` (`DECIDER_TIER1_ALGORITHM_VERSION`) | **`mvp-0.22`**, after the route rules' `mvp-0.20` and value-of-information stopping's `mvp-0.21` |
| `sources_upgrade.upgrade_to_mvp020`, chained from `upgrade_to_mvp019` | `decider_upgrade.upgrade_to_mvp022`, chained from `voi_stopping_upgrade.upgrade_to_mvp021`; `sources_upgrade.py` is main's again (it cannot chain upward without an import cycle) |
| `tests/test_mvp020_upgrade.py` (add/add with main's route-rules file) | `tests/test_mvp022_upgrade.py`; main's file kept |
| the upgrade test's `fixtures/migration_head_197` | `fixtures/migration_head_201` |
| `tests/test_proof_route_check.py` (modify/delete: the branch only moved its version pins) | stays deleted |

- **The successor.** `DECIDER_TIER1_ALGORITHM_VERSION = "mvp-0.22"`, appended
  to `SUCCESSOR_CHAIN` after `VOI_STOPPING_ALGORITHM_VERSION`; `LATEST` is
  mvp-0.22 and new vaults start there. The only gate the branch adds is the
  set `DECIDER_TIER1_VERSIONS` = {mvp-0.22} (read by
  `decider_judgments.enabled`, `pipeline._tier1` through it, and the
  recurrence groups' authority for an imported Decider link); no comparison
  is by equality or ordering. Main's own mvp-0.20 (the route rules) and
  mvp-0.21 move no judgment, and a Decider link recorded at either has no
  recurrence authority (`tests/test_decider_landing.py`).
- **The upgrade.** `upgrade_to_mvp022` accepts mvp-0.21, or mvp-0.9 to
  mvp-0.20 through `upgrade_to_mvp021`, passes the chained notes through
  (`chained_notes = list(chained.notes or [])`, a refusal's included, as the
  branch's did) and an earlier step's refusal unprefixed. T1's guard stays
  advisory; the refusal test sets `config="[recurrence]\nrequire_guard = true"`,
  the refusal names the mvp-0.12 step and the vault stays at mvp-0.10; once
  the guard passes the upgrade walks mvp-0.11 to mvp-0.22. `learnloop
  upgrade` defaults to mvp-0.22; `--to mvp-0.22` is new and `--to mvp-0.21`
  still reaches value-of-information stopping.
- **Every mention.** A line-by-line pass over every line the branch added:
  the code and comments (`decider_judgments`, `disclosures`, `agreement`,
  `cli/decider`, `field_classification`, `probability_arms`, the schema,
  misconceptions, the review runner and links, text gaps, field and
  contamination), the tests, `docs/decider-tier1-migration.md`, the reference
  generator's section and field descriptions, `Algorithm Versions and
  Reproducibility.md` (an mvp-0.22 row and the version sets) and `Version
  Registry.md` say mvp-0.22, and "as at mvp-0.19" (a switch's predecessor
  path) says mvp-0.21. Tests that set mvp-0.19 as "below the successor" use
  mvp-0.21, the immediate predecessor. Main's tests that pinned mvp-0.21 as
  the latest (`test_mvp011/013/014/015/016/017/018/020/021_upgrade.py`,
  `test_recurrence_commands.py`, `test_route_rules_in_grader.py`,
  `test_reading_step_switch.py`) pin mvp-0.22.
- **Defaults and references.** All fourteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM`
  entries (mvp-0.9 to mvp-0.22) were recomputed with
  `defaults_fingerprint_for_version` from the composed defaults, the template
  `.pyc` cleared before and after and the file touched; each moves only
  because the effective config gains `[decider_routes]` and
  `ai.routing.tier1_decider` (dormant below mvp-0.22, the span check
  excepted). The CLI help snapshot was rewritten (`decider`, `decider
  agreement`, `upgrade`, the root). The DB/config references were
  regenerated (`db_generate_reference.py`); `db_validate_reference.py`
  reports 0 errors once the prose counts read 813 effective leaves in 49
  sections (main's 804 in 48 plus the branch's nine leaves and one section);
  `validate_vault.py` passed.

### Composition

1. **The deleted route check.** Nothing reads it: main deleted
   `attempts/proof_check.py` and `ai.routing.proof_check`; the branch's only
   references were the `proof_check` output allowance in the spend adapter it
   moved to `ai/review_spend.py` (dropped there, as main dropped it from
   `offline_review/spend.py`), `PROOF_ROUTE_CHECK_VERSIONS` pins in tests
   (main's versions kept) and `tests/test_proof_route_check.py` (deleted).
   The proof-like item reading the branch left alone is gone on main.
   `test_nothing_in_tier1_reads_the_deleted_route_check` scans `src/`.
2. **The facet chokepoint.** Main's facet authority and proposal code are
   unchanged since `e8d261405` (an empty diff over
   `content/facet_identity/` and `content/proposals/`), so the branch's
   `check_meaning_write` and `patches._ask_span_support` merged as reviewed.
   UX Phase 1's automatic builds apply through main's proposal path:
   `bootstrap_synthesis` runs `synthesize_study_map(apply=True,
   apply_gate=auto_apply_allowed)`, which reaches
   `source_set_synthesis._apply_and_wire_goal` and so
   `patches.apply_accepted_items`: the span-support staging asks the Decider
   before `vault_mutation_lock("proposal_accept")`, and no outer vault lock is
   held there (the job runner takes the lock only to claim a lease, and the
   `auto_study_map` lock only while it plans and files the source set, before
   the build is enqueued). Pinned through `_apply_and_wire_goal` itself: the
   Decider is asked once with no lock holder, `supports` applies, any other
   option or a tie holds the card. **Fix:** UX's `keep_local` is read by every
   outbound boundary when its work runs; the span check is a new one, and a
   pending proposal accepted after its book was kept on this computer would
   have sent the book's passage to Perplexity. Now a check whose supporting
   span is from a kept book is not asked: the reword waits for the confirm
   (ledger verdict `unavailable`, `kept_on_this_computer` in its rationale;
   the test failed on the merge before the fix).
3. **Disclosures and consent.** Settings and `learnloop eval judges` disclose
   `tier1_decider` and `learner_gap_decider` as "OpenRouter, which forwards it
   to Perplexity". UX's one-time OK said only that passages and answers go to
   the connected AI. **Fix:** `decider_judgments.connection_note(config)`
   adds one plain sentence to the OK's `whatLeaves` and, as `deciderNote`,
   to the connect view's "What leaves this computer": "With an OpenRouter
   key, LearnLoop also asks Perplexity, through OpenRouter, short questions
   about your answers and questions (whether a mix-up or a gap is one it
   already knows) and about the book passages behind a reworded skill." It
   names only what is on (Tier-1 judgments at mvp-0.22, the learner-text
   gaps' Decider at any version, the span check wherever the reword confirm
   holds), follows a direct-Perplexity route ("With a Perplexity key ..."),
   and is absent when every route is off. No new screen, no separate OK; the
   jargon deny-list passes with it.
4. **Spend.** Every Decider request goes through `ReviewSpend.request` (one
   call, no output allowance, the profile's listed input price) and writes a
   model-call receipt (owner kind: the task); LLM fallbacks keep their own
   envelopes and receipts, subscription routes their uncapped treatment
   (N1 below is the known exception). UX's per-request `MeteredRequestGate`
   and the source service's daily guard are unchanged code. Inside an
   automatic build the gate admits the span check's one physical request like
   any metered request (at the cost-pause price, reserving the build's output
   ceiling because the Decider declares none) and settles it at the reported
   cost; a refusal is the check's `refused`, so the reword waits and the
   build goes on (both pinned with the real `DeciderProviderClient` over a
   fake transport). Decider receipts count in UX's daily guard (every
   metered receipt) and not in the source service's (its own owner kinds).
5. **Output budget.** `learnloop.ai.output_budget` is unchanged on main and
   already names the Decider exempt; the Decider's receipts carry no output
   budget, and each fallback route is admitted under the shared policy
   (`ai.output_tokens`, a route override where set).
6. **Snapshots, CLI help, references:** above.

### Tests added at the landing

`tests/test_decider_landing.py` (17): no route-check reader; the mvp-0.22
gate per version (main's mvp-0.20 and mvp-0.21 move nothing) and the
recurrence authority of links recorded at mvp-0.20 / 0.21 / 0.22; an
automatic build's apply asking the span check before the vault lock
(`supports`, `does not support`, a tie); kept books never sent; the metered
gate admitting and settling, and refusing; the one OK and Settings naming one
recipient (default route, switches off, below mvp-0.22, a direct Perplexity
route); the fallbacks' output policy. `tests/test_mvp022_upgrade.py` (the
branch's upgrade test, relabelled, plus the walk through the route rules).
Frontend: the connect view's sentence (`ConnectAI.test.tsx`, 2) and the
deny-list fixture. `tests/test_ux_phase1_connect_ai.py` expects the sentence.

### Gate

At `3a6c3fb81`, `TMPDIR` under `fixtures-local/tmp`, `uv sync --extra dev
--extra mobile` plus `pypdfium2`:

- `uv run lint-imports --no-cache`: 17 contracts kept, 0 broken.
- `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`: **10544
  passed**, 0 failed (15 min 31 s, load average 8 to 14). No timing-sensitive
  rerun was needed.
- `uv run pytest -m durability`: 99 passed.
- `apps/learnloop-tauri`: `npm install` up to date, `npm run typecheck`
  clean, `npm test` 73 files / 482 tests passed, `npm run frontend:build`
  built. `src-tauri` is unchanged against main, so no `cargo check`.
- `git diff --check` clean; `git status fixtures` clean.

### Parity

**Setup.** Backup-API copies (`copy_tree_with_databases`) of this worktree's
tracked `fixtures/linear_algebra` and `fixtures/probability` (`mvp-0.8`) in
`fixtures-local/decider-parity`. Each copy was migrated by its own code
(`migration_coordinator.migrate_vault`): main `21440c9cf` exported with
`git archive` (its `src` and `migrations`) on `PYTHONPATH`, and the merge's;
46 migrations to 201 on both (the landing adds none). On each copy
`learnloop rebuild --shadow --json` and `learnloop doctor --json`, with
`LEARNLOOP_CONFIG_DIR` an empty directory.

**Shadow rebuilds and doctor match main's exactly** once minted ids,
timestamps and paths are set aside (0 differences on all four outputs):

| Fixture | Facet | Mastery | Schedule | Doctor issues | Errors | `criterion:unknown_dependency` |
|---|---:|---:|---:|---:|---:|---:|
| linear algebra | 22 | 6 | 47 | 106 | 1 | none |
| probability | 2 | 1 | 1 | 134 | 49 | 46 |

These are the fixtures' existing drift at `mvp-0.8`, as at the
value-of-information landing; the live database's hash is unchanged by every
shadow run and doctor exits 1 on both sides (linear algebra's one error is
the fixture's missing `rubrics` directory).

**Upgrade mvp-0.21 -> mvp-0.22 (playbook item 7).** A third copy of
`linear_algebra`, migrated by the merge's code: `mvp-0.8` -> `mvp-0.9` ->
`mvp-0.21` (`--to mvp-0.21`; the chain's advisory guard notes passed
through), rebuilt twice to its fixed point; `rebuild --shadow` at mvp-0.21
showed facets 0, mastery 0, schedule 0; `learnloop upgrade` (the default
target) took it to mvp-0.22; `rebuild --shadow` then showed facets 0 and
schedule 0, and mastery 21 rows whose only differing field is
`algorithm_version` (`mvp-0.21` -> `mvp-0.22`), as at every successor. The
live database was unchanged by both shadow runs; doctor at mvp-0.22 reports
56 issues, its one error the same missing `rubrics` directory.

### Known residuals (the verify pass's five Low findings)

The Opus verify of `356784102..b1c7ace3f` was CLEAN with five Low findings;
none is caused or changed by the landing, and they stay open:

- **N1 (F6 residual).** Contamination with one Tier-1 switch on and the
  other off: the switched-off task's subscription receipts lose
  `billing: subscription` / `not_enforced`, `charged` records 0 tokens, and
  with no ready LLM judge the report mints a run and fails at the first
  LLM-first request (`provider_failed`) instead of returning `unavailable`
  up front. Verdicts and checkpoint ids are unaffected.
- **N2.** The review dry run's Decider estimate (`targets * 2 *
  history_error_limit`) is not an upper bound: arms `c` and `d` cite more
  links, so an admissible plan can stop `over_budget` at `--max-calls`.
- **N3 (pre-existing).** A Decider-first contamination checkpoint keys on the
  Decider profile's name, not its model: changing the Decider model reuses
  the old verdicts as `cached`.
- **N4 (documentation).** The agreement report's module doc and CLI help
  count "an LLM fallback beside the Decider's failure" as a pair; the code
  (correctly) counts it as a fallback.
- **N5.** The Settings DTO's `consumer` union (`dto.ts`) lags the routes
  (`tier1`, `learner_text_gaps`), and Settings shows key readiness, not
  whether a route is on (only `eval judges` shows `consumer_status`). The
  same lag holds for `FacetSpanSupportDto.status`, which lists neither
  `tied` nor `unchecked` (the card's fallback line covers both).

### Owner decisions (conservative defaults in force)

- **The Decider and the one OK.** Learner text and book passages reach
  Perplexity through OpenRouter under the connected AI's one OK, now named in
  its sentence (D6). Default: no separate OK and no new screen.
- **Kept books and the span check.** A reword citing a book kept on this
  computer waits for the owner's confirm and its passage is never sent.
  Default: as such; the card says it "could not be checked just now".
- **Automatic builds' money.** The span check's Decider request is admitted by
  the build's per-request gate and counted in the daily guard like any
  metered request. Default: as such (about $0.0004 a check, reserved at the
  build's output ceiling until it settles).
- **N1-N5.** Default: left as known residuals for a later fix pass.
