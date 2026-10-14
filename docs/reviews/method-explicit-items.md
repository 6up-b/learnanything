# Method-explicit items: criteria by fact, required methods

Stage `method-explicit-items`, branch `grading/method-explicit-items`,
worktree `learnanything-merge`, base `1def803a1` (main at mvp-0.20, migrations
to 199, head fixture `migration_head_199`).

> **Redesign (2026-10-14).** §1 and §2 describe the first writer check,
> which read the prompt to decide whether it stated a method. That reader is
> gone. The `required_method` field, frozen with the assessment contract, is
> the one thing grading reads. Writers append the canonical sentence, and a
> textbook statement or a PF variant's stem is judged once (Decider, else
> the LLM judge, ledgered). See "Redesign" in
> `docs/reviews/method-explicit-items-codex-review.md`.

**Owner rule (2026-10-13).** Rubric criteria name the FACT a step establishes
("shows the determinant is zero"), not the METHOD used ("uses cofactor
expansion"). Method-phrased criteria are an artifact of generation forcing an
LO, facet or concept into a practice question, and graders then mark down
valid alternative routes. The one exception: when the method itself is the
point of the item (its target LO, facet or concept IS that method), the item's
own statement requires it ("Use {method} in your answer.") and only then may a
criterion grade use of that method.

**Commits.**

| Commit | What |
|---|---|
| `64297af46` | the change: items, generation, grader, successor, doctor and report, gold set v3 |
| `abd206d24` | regenerated DB/config reference |
| `89da8a41e` | repair fixes found by the live run (strict target matching, the target's own name, safe sources) |
| (this commit) | this record |

Counts (`git diff --numstat 1def803a1`): `src/` +2,321 / −110, `tests/`
+1,723 / −109. No migration, no new table, no frontend or `src-tauri` change.

## 1. Items: the required method

`PracticeItem.required_method` (`vault/models.py`, `RequiredMethod`):

- `name` (non-empty), `criterion_ids` (the ONLY criteria that grade use of the
  method), and optional links `learning_object_id`, `concept_id`, `facet_id`;
- omitted when null (`exclude_if`), so every existing item serializes
  byte-identically; `practice_item_hash` adds it only when present, so every
  existing item keeps its hash (test: the hash of an item without one equals
  the old field set's).

`learnloop.vault.required_method` is the rule's dependency-neutral vocabulary
(importable from every layer):

- **The instruction.** `required_method_instruction(name)` = "Use {name} in
  your answer."; `prompt_states_method` (case and spacing aside);
  `ensure_method_instruction`.
- **Method targets from existing metadata** (`method_targets`): the item's LO
  whose concept has `type = procedure`, or a facet of `kind =
  procedure_contract`; never for an item whose capability is
  `method_selection` (choosing the method is then what is measured).
- **Name matching** (`names_match`): one name's content tokens contain the
  other's (generic words and crude plurals aside). Strict on purpose (fixed
  after the live run, §5): "cofactor expansion along the first row" names
  "Cofactor expansion"; "coordinatewise subtraction of the vector" does not
  name "negative of a coordinate vector".
- **The writer check** (`normalize_required_method`): a generated item keeps
  a required method only on a method target it names; it is linked to that
  target; unknown criteria are dropped; a generated prompt gets the
  instruction appended when missing; a SOURCE statement (a textbook stem) is
  never rewritten, so a method its stem does not state is dropped.
  `inherit_required_method` serves variants that keep a parent's rubric.
- **Validation** (`required_method_problems`): `required_method:not_stated`
  (error), `required_method:unknown_criterion` (error), and
  `criterion:method_phrased` (warning) for a criterion phrased by method that
  is not the required method's.
- **The conservative heuristic** (`method_phrase`): an explicit method verb
  ("uses", "applies", "via", "by" ...) within a few words of a method noun
  ("expansion", "rule", "theorem", "induction", "complement" ...), never a
  span that leaves the method open ("a valid method", "any approach"). It
  misses criteria that presuppose a method without naming one ("computes each
  2x2 minor"). On the non-owner fixtures it flags 6 of 478 criteria.

## 2. Generation: every writer

Shared text: `CRITERIA_BY_FACT_GUIDANCE` (criteria by fact; a required method
only on a listed method target, with the instruction and its criteria) and
`REQUIRED_METHOD_VARIANT_GUIDANCE` (a variant of a parent with a required
method states it). Every versioned prompt that changed moved its version.

| Path | Prompt / version | Contract | Writer check |
|---|---|---|---|
| Authoring proposals (`learnloop propose`; graph-edit proposals reuse the row builder) | `authoring_prompt`: guidance appended to `_PRACTICE_METADATA_GUIDANCE`; `AUTHORING_PROMPT_VERSION` `mvp-0.9-criterion-total-scoring` → `mvp-0.10-criteria-by-fact`. Each LO in the context lists `required_method_targets` when it has any (absent otherwise, so other LOs' context is unchanged) | `PracticeItemPatchPayload.required_method` (`RequiredMethodPayload`: name, criterion_ids) | `proposal_item_row` → `_hold_required_method_to_rule` (an update without its own prompt is checked against the item's current prompt) |
| Practice generation (expansion, diagnostic practice, post-probe, goal practice, cross-source, reading-progress seeding) | the same authoring prompt; recorded `PRACTICE_GENERATION_PROMPT_VERSION` `mvp-1.3-expected-minutes` → `mvp-1.4-criteria-by-fact` | same | same |
| Diagnostic authoring | `DIAGNOSTIC_AUTHORING_PROMPT_VERSION` `mvp-0.5-diagnostic-authoring` → `mvp-0.6-diagnostic-authoring-criteria-by-fact` | same | same |
| Tutor promotion, and learner-text gap seed items (`seed_from_question` → promotion) | through `generate_authoring_proposal`, recorded under `AUTHORING_PROMPT_VERSION`; `TUTOR_PROMOTION_PROMPT`'s own text is unchanged | same | same |
| Rung variants | the practice-generation lane; the source item's `required_method` is shown in the instructions when it has one | same | same |
| Canonical ingest and exam imports (`exam_ingest_instructions`) | the shared guidance; `CANONICAL_INGEST_PROMPT_VERSION` `mvp-0.6-criterion-total-scoring` → `mvp-0.7-criteria-by-fact` | `AuthoringProposal` | `proposal_item_row` |
| Exercise authoring and source exercise imports (Reader import, harvest, need fulfilment) | rule 8 (the guidance, plus: a required method only when the BOOK's stem already requires it); `EXERCISE_AUTHORING_PROMPT_VERSION` `mvp-0.2-criterion-total-scoring` → `mvp-0.3-criteria-by-fact`; the LO catalog lists `required_method_targets` when set | `ExerciseAuthoredItem.required_method` | `normalize_required_method(source_statement=True)`: the stem is never rewritten; a drop is an import warning |
| Study-map synthesis (bootstrap) and append | rule 15 (bootstrap) / rule 9 (append): the guidance, with the target defined as an LO anchoring a `procedure` concept or a `procedure_contract` facet; ONE-FACET rules renumbered 16 / 10. Versions: `mvp-1.3-sibling-criterion-dependencies` → `mvp-1.4-sibling-criterion-dependencies-criteria-by-fact`, the facet-identity variant likewise, append `mvp-0.10-...` → `mvp-0.11-...-criteria-by-fact` (both) | `SynthPracticeItem.required_method` (`SynthRequiredMethod`) | `_normalize`: targets from this batch's concepts, facets and LOs plus the registry (`_method_target_view`); a dropped method is a `required_method` review diagnostic |
| Teach-back authoring | "CRITERIA BY FACT" clause: criteria name the fact or reason the explanation establishes; only a source whose prompt requires a method may ask how that method establishes the result. `TEACH_BACK_AUTHORING_PROMPT_VERSION` `mvp-0.1-source-item-quest-transfer` → `mvp-0.2-source-item-quest-transfer-criteria-by-fact` | none: an explanation never requires a method | n/a |
| PF generation and publication | `REQUIRED_METHOD_VARIANT_GUIDANCE` in the generator-program, proposer, single-shot and source-anchored prompts: `pf-generator-program-v6` → `v7`, `pf-ensemble-propose-v2` → `v3`, `pf-single-shot-v2` → `v3`, `pf-source-anchored-v2` → `v3`. The parent view and the publication contract view show `required_method` only when set | the parent's rubric, verbatim | `build_item_payload` → `inherit_required_method`: the variant keeps the parent's method and its stem states it |
| Deterministic rubrics: Reader quick-check cards, learner-written cards, recall calibration, probe-instance templates, the exercise fallback | unchanged: already fact-phrased ("Answer matches the expected answer in substance.", "Correct fact.", strategy-open long-form criteria) | — | — |
| Learner-gap prerequisite draft (`learner-gap-prerequisite-draft-v1`) | unchanged: it drafts an LO, no rubric | — | — |

Generation does NOT block a method-phrased criterion deterministically (no
validation warning at proposal time; a warning would hold every such item for
review on a heuristic). The prompts do the phrasing; doctor and the report
catch what slips through (open question 2).

## 3. The grader: own-route-v2

`attempts/grading_support.py`:

- **Rules version.** `route_rules_version(vault)`: `own-route-v2` when
  `method_rules_active` (the successor, `required_method.enabled`, and the
  own-route rules themselves on), else `own-route-v1` at mvp-0.20, else none.
  `ROUTE_RULES_V2` = the v1 text plus `REQUIRED_METHOD_RULES`: a criterion
  listed in `required_method.criterion_ids` is graded on USE of the method;
  another route fails it even when every step is valid; set
  `divergent_route`, name the method used instead, mark down without quoting
  a wrong step; do not list it unverified merely because the route differs;
  every other criterion keeps the own-route rules.
- **Policy.** At v2 `reference_policy` carries `required_method` (name, the
  criterion ids of the rubric being graded), only when the prompt the learner
  ANSWERED (the assessment contract's) states the method: an answer to a
  statement that did not require it is never failed for not using it.
- **PF-c's gate.** `apply_valid_alternative_gate(..., method_criterion_ids)`:
  on a route the grader reads as divergent, an unlocated mark-down of a
  required-method criterion is not unverified (the grader's own declaration
  still unverifies it).
- **The own-route rule.** `apply_route_rule(..., method_criterion_ids)`: such
  a criterion is never unlocated; a mark-down of it on a divergent route with
  no located quote stays assessed and is reported in `method_route`. Held for
  review only when nothing is assessed, so a failing method criterion is no
  hold; it is an assessed shortfall (a diagnosis is queued).
- **Record.** The blind record's `proof_route_check` gains `rules =
  own-route-v2`, and, for a required-method item, `required_method` and
  `method_route_criterion_ids` (additive keys; `ROUTE_RULE_RECORD_VERSION`
  unchanged, open question 6). The route verdict in `judgment_ledger` carries
  them too.
- **Identity.** Prompt `mvp-2.1-blind-reference-policy+own-route-v2`,
  calibration `grading_prompt_v2_1_blind_reference_policy+own-route-v2`, the
  same for every item at the successor (the prompt's rules are the same).

## 4. Versioning ruling (playbook)

The grader change alters grading for new answers on required-method items, so
it ships as a successor.

- **Tag.** `METHOD_EXPLICIT_ALGORITHM_VERSION = "mvp-0.22-placeholder"`, a
  PLACEHOLDER relabelled at the merge (main is at mvp-0.20; VOI v2 lands as
  mvp-0.21, the Decider migration after). Appended to `SUCCESSOR_CHAIN`, so
  `LATEST_ALGORITHM_VERSION` and every version set follow; new vaults start
  there. Gate: `METHOD_EXPLICIT_VERSIONS`.
- **Kill switch.** `[required_method] enabled = true` (new section, modelled
  default, out of the decision-only template). Off, new answers grade exactly
  as mvp-0.20: tests compare an mvp-0.20 vault and the switched-off successor
  on a method item (prompt text modulo attempt id, context hash, prompt
  version, calibration identity, attempt columns, evidence rows and the whole
  `grading_support` block are equal).
- **Upgrade.** `method_explicit_upgrade.upgrade_to_method_explicit`, chained
  after `route_rules_upgrade.upgrade_to_mvp020`: accepts mvp-0.20, or mvp-0.9
  to mvp-0.19 through the chain; passes chained notes through
  (`chained_notes = list(chained.notes or [])`); T1's guard stays advisory,
  and the refusal test sets `config="[recurrence]\nrequire_guard = true"` with
  the vault left at mvp-0.10; refuses jumps; prepares the projection before
  the atomic config rename; rewrites nothing (items included). `learnloop
  upgrade` defaults to it; `--to mvp-0.22-placeholder` names it and `--to
  mvp-0.20` still reaches mvp-0.20.
- **Defaults.** All thirteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries
  recomputed (each moves only because the effective config gains
  `[required_method]` and the unset `ai.routing.rubric_phrasing_judge`);
  mvp-0.22-placeholder has its own entry. The template `.pyc` was cleared
  before and after.
- **Generation and the report** are content paths: no tag.
- **Replay.** Existing grades unchanged: an mvp-0.20 grade of a method item
  (its method criterion unassessed) replays identically after the upgrade
  (projection, `practice_attempts`, `grading_evidence`, `blind_grade_records`
  and `judgment_ledger` byte-equal); same-version rebuild equivalence holds at
  the successor with no model.
- **Playbook item 7 (shadow rebuild)**, on a backup-API copy of
  `linear_algebra` (`fixtures-local/method-explicit/la_shadow`): upgraded
  mvp-0.8 → mvp-0.9 → mvp-0.20 (the advisory guard's notes passed through),
  rebuilt twice; `rebuild --shadow` at mvp-0.20: facets 0, mastery 0,
  schedule 0. Upgraded to mvp-0.22-placeholder; `rebuild --shadow`: facets 0,
  schedule 0, mastery 21 rows whose only differing field is
  `algorithm_version`. The live copy's hash was unchanged by both shadow runs,
  and the tracked `fixtures/linear_algebra/state.sqlite` hash was the same
  before and after (`a3972c00...`; copied with the backup API only).
- **Playbook item 8.** `test_head_fixture_predecessor_to_successor_path`
  (`tests/test_method_explicit_upgrade.py`): head fixture 199 set to mvp-0.20,
  upgrade, foreign-key check, doctor (no `required_method` errors), and an
  idempotent rebuild.
- **No migration**, no new table.

## 5. Existing items: doctor and `learnloop grading method-phrasing`

**Doctor** (no model call; says `judge = heuristic` in each issue's details):
`criterion:method_phrased` (warning) on items' own rubrics and once per
default rubric, `required_method:not_stated` and
`required_method:unknown_criterion` (errors), and
`required_method:not_a_method_target` (warning). Retired items are skipped.
On the linear-algebra copy: one `criterion:method_phrased` warning.

**The report** (`content/proposals/method_phrasing.py`, CLI `learnloop
grading method-phrasing`):

- **Judge**, in this order unless `--judge` forces one, and the report says
  which ran (`judge.kind`, `reason`, `tried`):
  1. the Decider: `ai.routing.rubric_phrasing_judge` when it names a decider
     profile, or the code-default `openrouter_decider` when the route is unset
     and ready. One request per item, one typed `choice` (fact / method) per
     criterion; method at P ≥ 0.5;
  2. the LLM judge on the same route (a chat profile, or `ai.active_provider`
     when unset): one structured reading per item, with each method-phrased
     criterion's fact rewrite;
  3. the conservative heuristic.

  The route is new (`rubric_phrasing_judge` in `DECIDER_ACCEPTING_TASKS`).
- **Rewrites.** The LLM judge's own; after the Decider, the LLM route rewrites
  only the flagged items; with no LLM ready, a deterministic DRAFT that strips
  the method clause (`deterministic_draft`). A Decider flag the LLM writer
  reads as a fact is labelled `judges_disagree`.
- **Repairs.** One `update` proposal per item through the normal path
  (`proposed_patches.purpose = rubric_phrasing_repair`; updates are never
  auto-applied; `learnloop accept` applies). For each flagged criterion:
  add the required method (the target's own name, the instruction appended)
  when the item's target really is that method by metadata and name, else
  rephrase by fact. A teach-back item never gains a required method; a
  textbook exercise only when its stem already names it (the stem is never
  rewritten). Every other criterion field survives (the rubric is copied
  whole). Practised items are labelled `practised`. Nothing changes until the
  owner accepts; an accepted repair moves the rubric (and prompt) hash, so the
  next presentation snapshots a new assessment contract, and graded attempts
  keep theirs.
- **Spend.** One `ReviewSpend`: every request admitted before it is sent,
  receipts owned by `rubric_phrasing_report`; Decider and LLM verdicts are
  appended to `judgment_ledger` (task `rubric_method_phrasing`, left
  `rubric_criterion` / `<item>#<criterion>`). `--dry-run` builds no client.

**Live run on backup-API copies of `linear_algebra`** (owner-authorized paid
calls; the app loaded its own key; `ai.active_provider = or_haiku`, Haiku 5.5
via OpenRouter with `json_object`, as the LLM writer):

| Run | Code | Flagged | Repairs | Cost (provider-reported) |
|---|---|---|---|---|
| `la_phrasing` | `64297af46` | 24 criteria on 17 items (59 items, 105 criteria read) | 19 rephrase, 5 add-required-method; 3 items practised | Decider $0.00086 (59 requests), Haiku $0.0127 (17 + 1 truncation retry) |
| `la_phrasing2` | `89da8a41e` | the same 24 | 24 rephrase (16 LLM rewrites, 8 drafts where the writer read a fact: `judges_disagree`) | Decider $0.00086, Haiku $0.0103 |

The first run's 5 add-required-method repairs exposed three faults: the
matching accepted a shared generic word ("vector"), the method took the
model's paraphrase as its name ("Use distributing the product and replacing
i^2 with -1 in your answer."), and a textbook exercise's stem and a teach-back
item were given one. `89da8a41e` fixes all three (with tests); the second run
proposes none of them. The first run's proposal was accepted on its copy to
exercise the apply path (17 items, 3 practised, applied; doctor then reports
no `criterion:method_phrased` or `required_method` issue).

Reading the Decider's 24 flags: 13 are on `method_selection` items ("Selects
commutativity as a decisive required law to test"). Under the rule these can
still reject a learner who picks another valid strategy, so they stay flagged;
the report shows each item's capability for the owner's review (open
question 4).

## 6. Gold set v3 and harness v4

`fixtures/grading_hardcases/cases_v3.json` (the default; v1 and v2 kept): the
16 v2 cases plus four, in pairs:

| Required method (cell 5, `required_method_bypassed`) | Same mathematics, no required method |
|---|---|
| `la-det-required-cofactor-by-row-reduction`: "Use cofactor expansion along the first row", answered by row reduction | `la-det-no-required-method-row-reduction` (cell 1, fact-phrased criteria) |
| `pr-at-least-one-six-required-inclusion-exclusion-by-complement`: "Use inclusion-exclusion", answered by the complement | `pr-at-least-one-six-no-required-method-complement` (cell 2) |

Harness `grading-hardcases-v4`: production rules `own-route-v2` with the
item's required method; the production path exempts method criteria on a
divergent route; outcomes for cell 5 are `caught` (method failed, facts
credited), `wrong_acceptance` (method at full credit: not enforced),
`wrong_rejection` (a fact marked down) or `unassessed`; each summary has a
`required_method` block (enforced / not enforced / fact rejected), apart from
P2's rates. The loader refuses a cell-5 case whose prompt does not state its
method, whose label is not exactly its method criteria, or whose final answer
differs from the reference.

**Live check** on a backup-API copy (`fixtures-local/method-explicit/la_eval`),
production arm, `or_haiku` (Haiku 5.5, `json_object`) and `or_luna` (GPT-6
Luna, `reasoning_effort = low`); OpenRouter's public listing gives both
$0.10 / $0.50 per million input / output tokens (checked 2026-10-13). Dry run
first (40 calls, upper bound $0.46, cap $0.85), then the full set once, then a
second repetition of the four new cases (dry run: 16 calls, $0.19 upper
bound, cap $0.25; repetition 0 served from checkpoints).

| Route | Path | Wrong rejection (cells 1-2) | Wrong acceptance (cells 3-4) | Required method enforced (cell 5) | Facts rejected (cell 5) | Failed |
|---|---|---|---|---|---|---|
| Haiku 5.5 | raw | 0/10 | 0/7 | 2/2 | 0/2 | 1 |
| Haiku 5.5 | production | 0/10 | 0/7 | 2/2 | 0/2 | 1 |
| GPT-6 Luna | raw | 0/9 | 0/7 | 2/2 | 0/2 | 2 |
| GPT-6 Luna | production | 0/9 | 0/7 | 2/2 | 0/2 | 2 |

- Both paired cases without a required method were graded `correct` by both
  routes in every repetition; both required-method cases `caught` in every
  repetition (repeat noise on the four: 0/3 Haiku, 0/4 Luna changed).
- `la-det-row-reduction-checkable` (v2's method-phrased "minors" criterion,
  which Luna marked down in both mvp-0.20 repetitions) was `correct` for both
  under v2's prompt.
- The production path changed nothing on Luna and left one Haiku mark-down
  unassessed (`rule = unlocated`), as at mvp-0.20.
- Failures are invalid outputs (Haiku 1 on the full set and 1 on the second
  repetition, Luna 2), counted as failed, never as acceptances.
- Smoke coverage only: every case is synthetic, and cell 5 has two cases.

**Spend for the stage**, provider-reported from the copies' receipts:
hard cases $0.0909 (Haiku $0.0690, Luna $0.0219), phrasing reports $0.0247
(Decider $0.0017, Haiku $0.0230). **Total $0.1156**, under the $1 cap. No call
touched a tracked vault. Reports: `fixtures-local/method-explicit/`
(`hardcases-reports/`, `hardcases-cell5-reports/`, `phrasing-report/`,
`phrasing2-report/`), not committed.

## 7. Tests

New files (71 cases): `tests/test_required_method_grading.py` (18),
`tests/test_method_explicit_upgrade.py` (11),
`tests/test_required_method_items.py` (29),
`tests/test_method_phrasing_report.py` (13); `tests/test_grading_hardcases.py`
has 20 (7 new). They cover: the item contract and its hash; the heuristic,
names and targets; the writer check (method target, unmatched name, source
statement, unknown criteria); variant inheritance; doctor's four codes; every
generation path's guidance and version and the authoring, exercise-import,
synthesis and PF-publication writers; the pure grader rules (method criterion
kept on another route, declared still unverifies, PF-c exemption, quoted
errors still count); the prompt, policy and identity; the presented-prompt
guard; live grades, regrades and replay; the kill switch's exactness against
mvp-0.20; replay of mvp-0.20 grades after the upgrade; the upgrade chain; the
report's judges, drafts, disagreements, repairs and their apply path; the gold
set's pairs, loader refusals and production path.

**Fail-first at the base** (`1def803a1` exported to
`fixtures-local/tmp/base_1def803a1`, run with its own `src`): the four new
files fail at collection (`ImportError: cannot import name
'METHOD_EXPLICIT_ALGORITHM_VERSION'`, `'RequiredMethod'`, and
`ModuleNotFoundError` for the report); the updated hard-case file fails 18 of
20. A behavioural probe (a required-method item, the method criterion marked
down on a divergent route with no quote, `DivergentGrader`) at the base's
latest (mvp-0.20): `setup_unassessed = True, unlocated = ['setup']`; on the
branch: `setup_unassessed = False, method_route = ['setup'], rules =
own-route-v2`.

**Re-pointed tests.** The latest-version pins of the earlier upgrade tests
(mvp-0.11, 0.13 to 0.18, 0.20, recurrence, reading step, route rules) now name
mvp-0.22-placeholder; `test_synthesis_criterion_dependencies` the new
synthesis version; the hard-case counts the v3 set (20 cases);
`test_held_grade_composition`'s documented two-route dry run 2 × 20 calls. Two
spend-envelope tests (`test_source_service_spend_envelopes.py`) moved their
caps: the exercise-authoring prompt grew by about 2 KB, so its reservation
rose from about $0.24 to $0.26 at the test's $10 per million; the import cap
0.30 → 0.31 and the daily cap 0.25 → 0.28 keep each test's property (probed:
two operations fit and the third is refused up to 0.34; one import fits and
the second is refused from 0.28).

## 8. Gate

Run on the tree at `89da8a41e` (later commits are this record only), with
`TMPDIR` set to the worktree's `fixtures-local/tmp`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| Full suite: `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,335 passed**, 0 failed (12 min 31 s) |
| Durability lane: `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10,236 deselected |
| `db_generate_reference.py`, then `db_validate_reference.py` (at `64297af46`; no config change since) | **0 errors**: schema head 199, 318 table notes, 796 configuration leaves in 48 sections (the hand-written counts in `Configuration.md` and `Database.md` updated) |
| `validate_vault.py` | passed (1,099 notes) |
| CLI help snapshot | regenerated (`grading`, `grading hardcases`, new `grading method-phrasing`, `upgrade`) |
| Frontend and cargo | not applicable: nothing under `apps/learnloop-tauri` changed |

- **Not applicable.** No migration; the schema did not change.
- **An earlier run** (before the last fixes) had 11 failures: the
  latest-version pins of older upgrade tests, two spend-envelope caps, the
  documented hard-case dry run's call count, and a function-local
  `ops -> diagnosis` edge (the report module moved from `ops/` to
  `content/proposals/`, where module-level imports of `diagnosis` already
  exist). All are fixed in the gated tree.

## 9. Open questions

1. **Relabel at merge.** `mvp-0.22-placeholder` is renamed then:
   `METHOD_EXPLICIT_ALGORITHM_VERSION`, the defaults snapshot key, the CLI
   `--to` branch and help, `method_explicit_upgrade` (name, docstring,
   refusal regex), the tests' literals, the template comments, the playbook
   note, `Algorithm Versions and Reproducibility.md`, `Version Registry.md`,
   the reference generator note, and the regenerated references.
2. **Generation does not block a method-phrased criterion.** The prompts ask
   for facts and the writers enforce the required method's structure; a
   method-phrased criterion that slips through is flagged by doctor and the
   report, not held at generation. A heuristic validation warning would hold
   such items for review (no auto-apply); say if you want that friction.
3. **What counts as a method target.** Only a concept typed `procedure` or a
   `procedure_contract` facet; the vaults type many concepts `procedure`
   (SVD, complex multiplication), so required methods are permitted widely and
   the model's judgment decides. Facets without a title produce long names
   (the id, humanized).
4. **The Decider's precision.** 24 flags on the linear-algebra copy, 13 on
   `method_selection` items and 8 the LLM writer read as facts (threshold
   P(method) ≥ 0.5). Whether method-selection criteria should be judged
   differently is the owner's call.
5. **Kill switch name.** `[required_method] enabled` (a new section) rather
   than a key under `[proof_check]`.
6. **Record version.** `ROUTE_RULE_RECORD_VERSION` stays
   `route-rules-in-grader-v1`: the successor's keys are additive and `rules`
   names the version.
7. **Haiku 5.5 invalid outputs** under `json_object` persist (1 of 20, and 1
   of 4 on the repeat), as in the route-rules runs.
