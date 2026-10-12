# Slice 2 T4 — contamination detectors (shadow flags)

Spec: `docs/specs/spec_embedding_consumers_v1.md` §7, with §1 (R1–R6), §4 and
§13 (T4 report). Handoff: `docs/specs/implementation_handoffs.md`, "Slice 2 T4,
T5, T7, T8". Branch `slice-2/t4` from `main` at `974c5647`. The handoff's
prerequisite that the owner has reviewed the previous track's report is waived
(owner, 2026-10-12; `implementation_goal.md` §1a): tracks are built in parallel
and their report gates are post-hoc.

## Plan (written before coding)

**Shape.** T4 adds no serving-path code and no live behaviour. The three
lexical detectors stay exactly as they are and remain the floor:

| Detector | Live floor (unchanged) | Shadow addition (owner-run report) |
|---|---|---|
| Held-out exam leakage | `practice_leakage.check_leakage`: 6-word shingles + distinctive numerics, blocks generated items at generation time | kNN of each generated item's stored `item/stem` and `item/expected_answer` vectors over stored held-out span vectors (top-k, no cosine cutoff) shortlists pairs; an LLM judge decides each `leak` |
| Tutor answer leak | `tutor_qa.answer_leak_overlap` (substring / token recall), debits `reveal_events` | rank of the bound item's expected answer among all expected answers for the stored tutor-answer vector (top-k) shortlists; math answers also go through a symbolic check; an LLM judge (or the symbolic verifier) decides each `reveal` |
| Reader reveal | `reader_dialogue` bigram overlap ≥ 0.5 / hash / fingerprint, burns the reserve | kNN of the stored reader-answer vector over stored live-reserve vectors (top-k) shortlists; symbolic check on the reserve's answer; the judge decides; a flag **proposes** a reserve burn and never executes it |

The shadow flags are computed by an owner-run command, not on any serving path,
so no serving path makes an embedding call. Every subject or index without a
complete set of stored vectors degrades to the lexical floor (plus the symbolic
check) and the report says so.

**Files to add.**
- `src/learnloop/ops/contamination/` — `recipes.py` (T4 record kinds and their
  text recipes), `symbolic.py` (safe symbolic answer check), `detectors.py`
  (candidate building from the floor, the symbolic check and stored vectors),
  `judge.py` (the `leak` / `reveal` judge under spend caps), `report.py` (the
  §13 report: flag rates, floor/shadow agreement, proposals, audited samples).
- `src/learnloop/cli/contamination.py` — `learnloop contamination embed` and
  `learnloop contamination report`, both with `--dry-run`.
- `tests/test_contamination_*.py`.

**Files to change (additive).**
- `content/authoring/practice_leakage.py`: public `held_out_spans` (span ids +
  text; the existing text list delegates to it) and `inventory_for_texts`.
- `reader/reader_dialogue.py`: public `surface_statement_text` and
  `lexical_reserve_reveal` (the existing private detector delegates to it, so
  the floor has one definition).
- `diagnosis/offline_review/probes.py`: public `answers_equal` /
  `answers_differ` wrappers over the existing safe exact-arithmetic + SymPy
  comparison (model text reaches SymPy only through `safe_math_text`).
- `vault/embedding_recipes.py`, `ops/embedding_backfill.py`: an optional
  `registry` argument so the Phase 1 backfill (spend caps, receipts, lock,
  idempotency) embeds T4's record kinds without adding them to the default
  backfill.
- `ai/routing.py`, `config/schema.py`, `config/template.py` (defaults
  fingerprint): the `contamination_judge` route.
- `cli/__init__.py`, `tests/cli_help_snapshot.json`.

**Migrations.** None. T4 adds no table: verdicts go to `judgment_ledger`
(tasks `leak` and `reveal`, as §3.1 reserves), vectors to `embedding_vectors`,
and proposals are computed by the report from ledger verdicts and live state.

**Algorithm successors and kill switches.** None. Nothing served changes and
nothing persisted changes meaning; the lexical floor keeps every live decision.
Proposals (`burn_reserve`, `reveal_debit`, `review_item`) are listed in the
report and never executed. A future live switch would be a successor with a
kill switch, decided on this report (R6).

**Spend caps and model routes.**
- `contamination embed`: the Phase 1 backfill on the `embedding` route
  (`ai.routing.embedding`, never falls back), both embedding switches required,
  `SpendCaps` with `--dry-run`.
- `contamination report`: the judge runs on `ai.routing.contamination_judge`
  (unset → the active provider; receipts record the resolved model). Metered
  routes keep the full cap set and the physical-request bound; a Codex route
  runs on the subscription with `estimated_only` cost (Slice A §5 rule 6).
  `--dry-run` prints the estimate with no client, lock or data change.
  `--no-judge` gives a zero-cost report from the floor, the symbolic check and
  stored vectors.

**`judgment_ledger` writes.**
- `leak` — left `practice_item`, right `source_span` (`extraction/span`);
  judge `llm`; verdict `leak` | `clean` | `unsure`.
- `reveal` — left `question_event`, right `practice_item` (tutor answer) or
  `activity_surface` (reader); judge `llm` with verdict `reveal` | `clean` |
  `unsure`, or judge `verifier` (symbolic match on a distinctive math answer,
  verdict `reveal`).
- Ids are content-addressed (`ctj_` / `ctv_` + input hash), so reruns never pay
  twice. Authority when verdicts differ: owner > verifier > llm.

**Tests.** Recipes declare canonical text and never read the learner's
question; the symbolic check matches equivalent forms and never parses unsafe
text; detectors shortlist by rank, not score; a judge stubbed to `clean` yields
no flag (R1); missing vectors degrade to the floor; proposals never change
reservations, exposures or `reveal_events`; dry run changes nothing and builds
no client; caps admit before any call; reruns are cached; the report makes no
embedding call; owner > verifier > llm precedence; the CLI.

## What was built

_(filled in below after implementation)_
