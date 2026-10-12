# Slice A Phase 2 — learner field F1

**Checkpoint:** implemented on `slice-a/phase-2`; no serving change, activation,
merge or push. Owner review of reports 1–2 remains the next decision.

## Plan

Base: primary checkout `main` at `1a0f7a0`, including merged Phase 1.
Branch: `slice-a/phase-2`. Owner accepted field D1, D2, D3, D8, D9,
D10 and D12 defaults.

- Add `src/learnloop/field/` for authoritative outcome projection, immutable
  replay rows, interaction signals, predictor interfaces and pure predictors.
  Reuse grading epochs, item snapshots, effective observations, facet outcome
  arithmetic, canonical facet resolution and serving receipts.
- Add the shared evaluation harness and CLI commands `learnloop field data-check`
  and `learnloop eval`. Generate aggregate-only JSON and Markdown reports 1–2
  with exclusions, uncertainty, prequential ordering and version manifests.
- Harness arms: `base_rate_lo`, `facet_beta`, incumbent `mastery_ekf`,
  `lo_general`, practice/capability/transfer/retrievability/hints/tutor-signal
  extensions and composite; retrievability and signal-constant sweeps.
  Provide a registration seam for Phase 3's family arms. Optional offline LLM
  predictions remain off by default and cannot be active.
- Add field config and import contracts. Only the incumbent may serve in F1;
  no algorithm successor, placement changes, graph coupling or evidence writes.
- Add a migration for DERIVED `facet_outcome_observations` and WORKFLOW
  `question_classifications`, register the outcome rebuild owner, then take the
  next free number at completion and regenerate the migration-head fixture and
  database references. No active challenger snapshot is needed in F1.
- Reuse Phase 1 spend caps, dry-run, checkpoints and per-component routes for
  optional question classification and offline LLM prediction. Each model
  verdict appends to `judgment_ledger`; replay consumes cached outputs only.
- Change the map RPC/types/rendering so no-evidence points omit `ready` and
  explicitly display an outlined, flat `untested` state. Preserve demonstrated
  geometry, beads, ghost rings and decay markers.
- Add the F1 tests named in field §9 and gate tests G1–G6/G10–G13; run focused
  tests, import lint, full parallel pytest, durability, frontend typecheck,
  vitest and build. Exercise both CLI commands and reports on backup-API copies
  under `fixtures-local/`, never on working vaults.

## Scope boundaries and decisions

- F2 assumed-known and quick-check tests/behaviour, activation successors and
  kill switches belong to later phases. Phase 3 owns family-specific arms.
- No live API calls in tests. Never read `.env` files or
  `~/.config/learnloop`. Validation commands use isolated configuration.
- D12 specifies a cap but not its numeric value, and “before any work” lacks
  a defined timestamp cutoff. Any conservative interpretation will be
  explicitly documented and versioned, not fitted to owner history.

### Resolved implementation ambiguities

- The spec writes `a * theta - b`, but the existing resolver/mastery filter
  uses difficulty in ability units: `a * (theta - b)`. All arms retain the
  existing units (the equivalent intercept is `a*b`), so the independent
  one-LO limit agrees for non-unit discrimination as well.
- Incumbent arithmetic remains unchanged, including its minimum positive
  effective mass of 0.1. Challengers use the spec's true `/ effective_mass`
  observation variance. The limiting-equivalence test uses mass at least 0.1;
  zero underlying mass is an exact no-op in every arm. The hint arm explicitly
  replaces assistance-only dampening, including a zero assistance factor, with
  the separately computed undampened mass. Quarantine zeros both masses.
- `dont_know` is outcome zero with the existing configured attempt-type mass
  (0.7 by default), not an invented unit-mass observation. This resolves the
  conflict between §4's “full mass” wording and §3's authoritative
  `EffectiveObservation` arithmetic in favour of preserving the latter.
- The interaction-signal cap is conservatively fixed at 0.3 per subject/LO/UTC
  day, versioned with the other a-priori constants. Only an explicitly logged
  `seconds_into_attempt == 0` is “before any work”; missing timing is not
  invented. The report's sweeps do not fit these constants to the owner.
- F1 changes the effective-default fingerprint under `mvp-0.9` only for
  offline analysis settings and disabled paid routes. There is no serving or
  evidence-meaning change requiring a successor.
- Offline commands use explicit vault TOML with environment-file loading
  disabled. Optional paid routes are explicit and cannot inherit global
  chat-provider overrides; API keys, when the owner opts in, come from the
  process environment.
- Historical selection snapshots do not record FSRS retrievability or the
  complete empirical-Bayes item posterior. The loader does not substitute
  today's heads. It reports missing historical covariates; absent retrievability
  contributes no covariate, so a report without those values cannot identify
  that extension's benefit. Reconstructing it would require a separately
  validated historical FSRS-policy replay, not a simple current-state join.
- Report 2 uses a frozen conservative `q=0.9` by default; `--fast-track-q 0.8`
  is an explicit report-only experiment. Neither result activates placement.
- **Historical attribution limit:** the existing grading contract records
  prompt/answer hashes and targets, but not a full graded-item hash or numeric
  criterion-to-facet weights. A scheduler snapshot alone is not proof of the
  graded mapping. Exact rows therefore require matching immutable receipts and
  a uniquely determined single-facet allocation; historical multifacet items
  are excluded unless the owner explicitly enables flagged current-content
  reconstruction. This is stricter than the spec's assumed snapshot coverage,
  not permission to substitute today's content.
- Historical subject, demand, question mappings and claim timing come from
  receipts. Today's LO membership/subjects/difficulty never retarget past rows.
  Unmapped questions are counted rather than guessed. Claim priors are frozen
  strictly before the first attempt, using the existing mastery-prior arithmetic;
  later claims and concept claims without historical membership are counted as
  exclusions rather than backdated.
- Existing propensity writers record `legacy-unverified` or
  `unavailable_composed_offer`, neither a valid system-choice probability.
  Propensity remains null where no verified probability exists. Requested
  origin is not inferred from mutable requests or explanation text.
- The optional offline LLM sensor currently reads numeric item features and
  recent graded observations, not learner-text excerpts. It is not an experiment
  measuring the additional value of rich text. It remains point-only and cannot
  activate. Paid preparation supports observable `openai_chat`/`openrouter`
  transports only; opaque SDK agents cannot enforce the physical-call boundary.
  Hidden retries/repairs are refused before I/O, with retry/pair caps fixed at 0.
- The sole outcome-replayer composition edge is explicitly exempted from the
  frozen cross-package-cycle contract. No broad package exception was added.
  SQL writes live in registered `db/stores/field.py`, restricted to the two
  field-owned tables. Predictor imports remain separately forbidden from stores,
  models, graph policy and evidence writers.

## Owner commands: reports 1–2 on a copy

Run from the repository root. Set `SOURCE_VAULT` yourself; these commands do not
search for it. Use a new destination each time. Copying excludes environment
files and uses SQLite's backup API (including committed WAL contents).

```bash
export SOURCE_VAULT=/absolute/path/to/your/vault
export FIELD_COPY="$PWD/fixtures-local/field-review"
uv run python - <<'PY'
import os
from pathlib import Path
from learnloop.config.loader import load_config
from learnloop.db.copies import copy_tree_with_databases

source = Path(os.environ["SOURCE_VAULT"]).resolve()
destination = Path(os.environ["FIELD_COPY"]).resolve()
if destination.exists():
    raise SystemExit("Choose a new FIELD_COPY; do not overwrite an earlier review.")
config = load_config(source / "learnloop.toml", load_environment=False)
database = Path(config.storage.sqlite_path)
if database.is_absolute() or ".." in database.parts:
    raise SystemExit("Use a vault-local database path before making this review copy.")
copy_tree_with_databases(
    source, destination,
    database_names=(database.name,),
    ignore=lambda _directory, names: {
        name for name in names if name == ".env" or name.startswith(".env.")
    },
)
print(destination)
PY
uv run learnloop field data-check --vault "$FIELD_COPY" --json
uv run learnloop eval \
  --vault "$FIELD_COPY" --section field \
  --output-dir fixtures-local/reports/field-review \
  --bootstrap-samples 1000 --seed 0 --fast-track-q 0.9 --json
```

`evaluation.json` and `evaluation.md` contain both report 1 (prequential replay)
and report 2 (historical fast-track simulation). No paid route is used by these
commands. Inspect exclusion counts first: `exclude` is the honest default, and
thin or missing data keeps the incumbent. An explicit exploratory
`field.legacy_fallback = "current_content"` in the **copy's** TOML flags those
rows as reconstructed, never exact.

## Built

- `field/types.py`, `predictors.py`, `priors.py`: immutable observation-free
  prediction inputs, the `LearnerPredictor` contract, independent incumbent,
  joint float64 EKF, conditional information gain, region uncertainty/direct
  evidence labels, frozen claim priors and versioned constants.
- Eleven default arms plus nine fixed sweep variants. Phase 3 can register its
  family arms without changing the harness. No challenger snapshot is persisted
  because no challenger is active.
- `field/outcomes.py`, `signals.py`: latest surviving grading epochs, conservative
  revision proof, canonical facet merges/shares, serving provenance, immutable
  hint/question/reader signals and read-only diagnostics.
- Migration **167**, selected after fetching primary `main` (migrations through
  166). The final fetch saw `be33cdd0` with daily-loop fixes but no additional
  migrations; this branch remains based on `1a0f7a0`. Table roles and sole `field_outcomes`
  replayer registered. `migration_head_167` is migrated, FK-clean and in DELETE
  journal mode. All five fixture-path consumers and generated DB/config
  references updated.
- `field/evaluation.py`, `offline_llm.py` and CLI adapters: all-arm prequential
  prediction before observation, facet-share aggregation, paired
  attempt-cluster bootstrap, calibration/AUC/log-loss/Brier, first/later,
  origin/revision/topic/help splits, fast-track simulation and conservative
  no-activation recommendations. Aggregate-only JSON/Markdown and manifests.
- `learnloop eval` preserves the existing `--section`, `--bins` and `eval` JSON
  payload for decision-calibration consumers; `--section field` selects F1.
- `field classify-questions` and explicit `eval --prepare-llm --llm-cache ...`:
  separate opt-ins/routes, whole-run and per-request admission, dry-run,
  cancellation, resumable caches, physical-call guards, model receipts and an
  append-only judgment for every returned verdict. Normal cache replay has no
  model calls. Set API keys in the process environment, never committed files.
- Map sidecar discriminated payload and frontend: untested points omit readiness,
  ghost and variance values; flat outline and explicit label. Demonstrated
  depth/beads and actual decay markers retain their original geometry.

## Verification

| Check | Result |
|---|---|
| Full suite `uv run pytest -n auto` | **6,451 passed**, 14 existing warnings; exit 0 on final frozen code |
| Durability `uv run pytest -m durability` | **63 passed**, 6,388 deselected; exit 0 on final frozen code |
| `uv run lint-imports --no-cache` | 8 contracts kept, 0 broken |
| Final focused F1/CLI/architecture tests | 143 passed; claim-prior/CLI/architecture follow-up 19 passed |
| `npm run typecheck` | Passed |
| `npm test` | 29 passed across 8 files |
| `npm run frontend:build` | Passed; existing >500 kB chunk warning |
| DB reference generator and validator | Passed: schema 167, 263 table notes, 526 config leaves, no validation errors |
| `git diff --check` | Passed |
| `learnloop field data-check` and `learnloop eval --section field` on backup-API smoke copy | Passed; both reports generated |
| Same-version second shadow rebuild on that copy | Source SHA unchanged; facet/mastery/schedule deltas all 0 |
| Doctor on a fresh backup-API copy of `migration_head_167` | 0 errors; 35 pre-existing legacy/authored-content warnings |

The smoke vault is `fixtures-local/slice-a-phase-2-smoke`, copied from the
migration-head fixture. Its six old graded attempts are correctly excluded by
strict revision policy; reports explicitly state zero scored rows and cannot
support a switch. Nonempty and winning/losing report paths are tested on
synthetic histories. Outputs are in
`fixtures-local/reports/slice-a-phase-2-smoke/`; full test logs are under
`fixtures-local/phase2-validation/` and are not committed.
Final release logs: `release-full-pytest.log`, `release-durability-pytest.log`,
and `release-lint-imports.log`. The 14 full-suite warnings are existing
Python 3.12 multiprocessing-fork and SQLite datetime-adapter warnings.

The first shadow against the fixture's stale stored projection reported 32 facet,
4 mastery and 4 schedule differences, without changing its source SHA. After
`rebuild-derived-state` **on the copy**, a second shadow under the same
`mvp-0.6` version reported all three delta counts as zero. No algorithm upgrade
was performed.

The migration-head fixture also now preserves its required empty `rubrics/`
directory with `.gitkeep`. The predecessor lost that empty directory in Git,
which caused `layout:missing_directory` on a fresh copy. No authored rubric or
working-vault content was changed.

### Gate/test coverage

| Gates | Evidence |
|---|---|
| G1–G3 | `test_facet_outcome_view.py`, `test_rebuild_orchestrator.py`, `test_shadow_rebuild.py`, `test_field_boundaries.py`, read-only CLI/cache tests and import contracts |
| G4/G6 | `test_map_untested.py` and `KnowledgeWellView.test.tsx`: no prior masquerades as demonstrated evidence; tested geometry/decay unchanged |
| G5/G10/G11 | `test_lo_general.py`, `test_predictor_interface.py`, `test_field_config.py`, consumer/predictor import contracts |
| G12 | Outcome epoch/revision/weight tests, direct EKF equivalence/priming tests, zero underlying mass invariance including later familiarity |
| G13 | `test_interaction_signals.py`, hint-replacement tests, daily-cap sweeps, evidence read-only checks |
| Harness/report contract | `test_eval_harness.py`, `test_field_cli.py`, `test_field_llm_cli.py`, `test_field_priors.py` |

All F1 portions of field §9 are covered. Assumed-known/quick-check/live kill-switch
tests are F2, not missing F1 work.

### Resolved validation failures and environment notes

The initial full suite had four failures: unregistered SQL writers, an existing
`eval` JSON compatibility regression, the intentionally changed CLI help
snapshot, and the existing PDF-page test missing its optional renderer.
The first three were fixed in code/registered ownership/snapshots. Installed
`pypdfium2==5.14.0` in the local test environment only (`uv pip install pypdfium2`);
no project dependency or lockfile changed. The PDF test and subsequent full
suite passed. Snapshot regeneration uses
`COLUMNS=80 uv run python -m tests.test_cli_help_snapshot --write`.

Additional Rust check was blocked before compiling project code:

```text
error: process didn't exit successfully: `rustc -vV` (exit status: 127)
rustc: symbol lookup error: /usr/lib/librustc_driver-b9ead9e03832c46d.so:
undefined symbol: _ZNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEE9_M_mutateEmmPKcm,
version LLVM_23.1
```

This phase changes no Rust code. The three frontend checks above passed. Npm
reported 14 existing dependency vulnerabilities during installation; no
dependency versions were changed.

## Open questions at the checkpoint

- Owner review of reports 1–2 remains required; no model is activated here.
- Historical FSRS/empirical-Bayes covariates are unavailable for some logs.
  Should a later phase add immutable pre-attempt covariate snapshots or a
  separately validated historical replay? Current heads must not be substituted.
- A future receipt improvement should capture full graded-item revision hashes
  and numeric criterion-to-facet mappings. Until then, multifacet historical
  exclusions can make default reports thin; explicit reconstructed reports are
  exploratory, not a reason to silently claim exact provenance.
- Confirm the conservative 0.3 daily signal cap and exact-zero early-help
  interpretation before any future live consumer. Both are versioned and
  report-only here.
- If Phase 3 lands first, rebase, renumber this migration if necessary,
  regenerate the head fixture, and rerun registry, durability and equivalence
  checks before merge.
- Primary `main` advanced to `be33cdd0` (daily-loop bug fixes) during this work.
  Rebase onto the then-current main before merge; no merge/rebase of that
  independent work was performed at this F1 checkpoint.
