# Project understanding M1: delayed questions on agent-written code

Branch `projects/m1`, worktree `learnanything-projects-m1`, base `main` at `16db5ac5`.
Spec: `docs/specs/spec_project_understanding_v1.md` §3, §4, §5.2, §5.3, §6.1, §7,
§8.2 (G1–G3, G5–G7), §9 (M1 row), §10 (M1 tests), §11 (D1–D10 defaults).
The opt-in explanation gate (M1b: §5.1 gate arm, G4, G8, §8.1) is out of scope.

## Plan (written before coding)

### Files to add

`src/learnloop/projects/` (new package; no `state.sqlite` access):

| File | Role |
|---|---|
| `__init__.py` | Package docstring: M1 is standalone, practice-only, never certification (D6) |
| `git.py` | `git -C <repo>` through `subprocess` with an argument list, no shell, a timeout, `--no-ext-diff --no-textconv`, `GIT_TERMINAL_PROMPT=0`; one `GitError` |
| `redaction.py` | Secret path patterns, `.learnloopignore`, noise files (lockfiles), the content scanner (key prefixes, PEM, assignments, high-entropy tokens); whole lines become `[REDACTED:<kind>]`; per-kind counts |
| `capture.py` | Enrollment, the trailer sweep, the pending list, manual `accept` (working tree, `--commit`, `--include-untracked`); builds the redacted bundle (diff + ±40-line head-side excerpts, extended to the enclosing scope within `project.context_token_budget`) and stores it in the originals store by content hash; `auto_sweep` that never raises (G1) |
| `hooks.py` | Append-only `post-commit` installer/uninstaller; the hook writes one JSON line and always exits 0 |
| `ai_contracts.py` | Blind context dataclasses (`ProbeAuthoringContext`, `ClosedBookContext`, `ProbeGradingContext`), wire models, prompt renderers and prompt versions |
| `ai_runtime.py` | Route resolution (`project` task, grading route for grading), subscription detection, spend estimates, an isolated empty working directory for model calls, the per-call receipt/physical-request observer |
| `probes.py` | Answer-first generation → validity filter (citations resolve, quotes verbatim, `why` needs a cited rationale) → closed-book check → probe-grader verdict → seeded random selection of 2 → sealing; stage-by-stage persistence so a resumed run never re-pays; serving due probes; answering (unassisted by default; `looked`/`used_ai` taps; don't know / unfair / skip); blind grading; owner contest |
| `experiment_store.py` | `<vault>/projects/project_store.sqlite` schema (WAL, `user_version` 1) and every SQL write: `repos`, `diffs`, `provenance_reports`, `probes`, `probe_responses`, `unattributed_commits`, `judgments` (append-only mirror of `judgment_ledger`), `call_receipts` (with disclosure fields), `store_meta` |
| `report.py` | The §8.3 M1 report: unfair/ambiguous taps, contest rate, closed-book rejection rate, citation-resolution failures, generation cost per diff, capture coverage, accuracy and don't-know/skip rates by provenance, version manifest |

`src/learnloop/cli/project.py` (registered as `project`): `enroll`, `unenroll`,
`sweep`, `accept`, `status` (`--disclosure`), `probes`, `answer`, `contest`,
`provenance`, `install-hook`, `uninstall-hook`, `report`.

### Files to change

- `ai/routing.py`: `AITask` gains `project`; an unset `ai.routing.project` falls back to the grading route, then the active provider. Operations `project_probe_authoring` and `project_closed_book_check` → `project`; `project_probe_grading` → `grading`.
- `config/schema.py`: `AIRoutingConfig.project`; a `ProjectConfig` section (`auto_sweep` kill switch, delay, counts, context lines and budget, backfill days, plan-build throttle, `generate_before_serving`).
- `ops/startup.py`: app-start `auto_sweep` (capture only, no model calls; returns at once when no store exists).
- `learnloop_sidecar/handlers/queue.py`: throttled plan-build `auto_sweep` before building the Today queue.
- `pyproject.toml`: an import-linter contract keeping `learnloop.projects` off the vault-state, scheduling and adapter modules; `learnloop.projects` added to the infrastructure contract's forbidden list.
- `tests/structured_ai.py`: handlers and contexts for the `project_*` purposes plus a payload-recording fake (G2, G3).
- `tests/test_architecture.py`: register `experiment_store.py` as an SQL owner; `projects` as a domain package.
- CLI help snapshot; config reference docs (new config leaves).

### Migrations

None. M1 writes only `projects/project_store.sqlite` (own schema, `PRAGMA user_version`), `projects/pending.jsonl`, and content-addressed bundles in `canonical-sources/raw/` (the originals store). G6 is tested.

### Algorithm successors and kill switches

No successor: nothing served from `state.sqlite` changes, and no persisted vault meaning changes. Kill switch `project.auto_sweep = false` stops the automatic app-start and plan-build sweeps; enrollment is the opt-in.

### Spend caps and model routes

- Routes: `ai.routing.project` (authoring, closed-book), default → `ai.routing.grading` → `ai.active_provider`; probe grading on `ai.routing.grading`. Receipts record the resolved provider and model.
- Automatic sweeps never call a model. Generation runs in `project sweep` (unless `--capture-only`) and, for due diffs that have none, before `project probes` serves.
- Every generation/grading command uses `SpendBudget` with `--max-candidates/--max-calls/--max-retries/--max-tokens/--max-cost-usd/--price-per-million` and a `--dry-run` that prints calls, tokens and cost and makes no calls or writes.
- Codex (`codex_sdk`, the ChatGPT subscription): no physical-request bound, tokens and dollars not capped, cost estimated from reported token usage at a reference rate and labelled `estimated_only`; call and candidate caps still apply. Metered routes keep every cap, unknown prices fail closed, and a hidden retry is admitted only against `max_retries`.

### `judgment_ledger` writes

M1 cannot write `state.sqlite` (G6), so verdicts append to the store's `judgments` table, which mirrors `judgment_ledger` (same columns, append-only triggers, LLM verdicts need model and prompt version). M2's `import-experiment` copies them. Tasks: `project_probe_validity` (verifier), `project_closed_book` (llm), `project_probe_grade` (llm), `project_probe_adjudication` (owner, superseding the grade), `project_probe_unfair` (owner).

### Tests

`test_project_capture.py`, `test_project_redaction.py`, `test_project_probes.py`, `test_project_blindness.py` (G3), `test_project_hooks.py` (G1), `test_project_experiment_store.py` (G6), `test_project_report.py`, `test_project_cli.py` (sealing across every command, G5; G2 through the recording fake; dry-run). All repos are temporary repos built in `tmp_path`; every model is a fake.
