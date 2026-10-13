# Decider migration, Tier 1 (`mvp-0.20`)

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
