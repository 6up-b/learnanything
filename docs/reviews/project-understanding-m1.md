# Project understanding M1: delayed questions on agent-written code

Branch `projects/m1`, worktree `learnanything-projects-m1`, base `main` at `16db5ac5`.
Spec: `docs/specs/spec_project_understanding_v1.md` §3, §4, §5.2, §5.3, §6.1, §7,
§8.2 (G1–G3, G5–G7), §9 (M1 row), §10 (M1 tests), §11 (D1–D10 defaults).
The opt-in explanation gate (M1b: §5.1 gate arm, G4, G8, §8.1) is out of scope.

> **Codex review (2026-10-12).** Fifteen findings were fixed after this file was
> written; see `docs/reviews/projects-m1-codex-review.md`. The "Built",
> "Decisions" and "Open questions" sections below are updated where a fix changed
> them (isolation, small diffs, store schema 2, grading effort, retries).

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

---

## Built

**Capture (§3, D1, D5).** Once a repo is enrolled, capture needs nothing from the owner.
- `auto_sweep` runs at app start (`ops/startup.run_startup_maintenance`, which the sidecar, TUI and `learnloop review`/`why` all call) and at plan build (the sidecar's `get_today_queue`, throttled to once per `project.plan_sweep_min_interval_minutes`, default 15). It only runs git: it never calls a model, never raises, and returns at once without creating anything when no repo is enrolled. `project.auto_sweep = false` is the kill switch.
- A sweep lists local branches and `HEAD` since the repo's `capture_since` (enrollment minus `project.enroll_backfill_days`, default 7), paging through `git log`; past 200,000 commits it stops and reports the repo's history as incomplete. Merges are skipped. Every commit with an agent trailer (`Co-Authored-By`/`Assisted-by`/`Generated-by` naming Claude, Codex, Copilot, Cursor, Aider and others, or Claude Code's "Generated with" line) that isn't stored yet is captured. Duplicates are recognised by sha and by `git patch-id`, so rebased or cherry-picked copies, and a working-tree capture that is later committed, are not captured twice.
- The optional `post-commit` hook (`project install-hook`, or `enroll --install-hook`) only appends `{"repo_id","sha","at"}` to `projects/pending.jsonl` and always exits 0. Each enrolled work tree has its own block, guarded by its top-level path, because linked worktrees share one hooks directory. The next sweep moves the list into a durable queue in the store and captures agent-trailer commits from it; an entry leaves the queue only once its repo was swept. Trailer-less commits become an *unattributed* list in `status`, and one command (`accept --commit <sha> [--agent codex]`) marks them as AI-written.
- `accept` captures trailer-less agent work: the working tree (`pre_commit`), specific commits (`post_commit`), and `--include-untracked` (`git ls-files --others --exclude-standard`).
- Each capture stores a content-addressed bundle in the originals store (`canonical-sources/raw/`): per included file, its redacted diff and redacted head-side excerpts. Excerpts cover ±`project.context_lines` (40) around each hunk, extended to the enclosing function or class (an indentation heuristic) while the bundle fits `project.context_token_budget` (12,000 estimated tokens). Bundles over budget shrink to hunk-only excerpts, then drop trailing files, then truncate, and are marked `truncated`. Every capture with probe-able content is probed, however small (`project.min_diff_lines` is the M1b randomization threshold only).

**Disclosure (§4, D7, G2).**
- **Files never read into a bundle:** secret-pattern files (`.env*`, `*.pem`, `*.key`, `id_rsa*`, `*.p12`, `*credential*`, `*secret*`), `.learnloopignore` matches, noise files (lockfiles, minified bundles, source maps) and binaries.
- **Lines replaced with `[REDACTED:<kind>]`:** diff, excerpt and commit-message lines (and the source text git repeats after a hunk header's coordinates) that match a key prefix (`sk-`, `AKIA`/`ASIA`, `gh*_`/`github_pat_`, `xox*-`, `AIza`), a PEM block (every line of it), a credential assignment, or a long high-entropy token. This happens before storage, and models only ever see stored text.
- **What models are sent:** the diff hunks with their context and the commit message, with agent trailers stripped (the generator must not learn who wrote the code).
- **Receipts:** every call records its files, hunks, bytes, scope, provider and model. `project status --disclosure` summarises them per repo.
- **Remotes:** credentials are stripped from remote URLs.
- **Repo scope:** `--context-scope repo` is recorded but falls back to diff scope, because `READ_ONLY_WORKSPACE` (Slice 1 §5.6) isn't built yet.

**Probes (§5.2, D4).** Generation runs in stages, and each stage is persisted before the next paid call, so a resumed run never pays twice:
1. **Answer-first authoring.** The wire model's field order puts `reference_answer` and `citations` before `question`.
2. **Deterministic validity check**, recorded as a `verifier` verdict. Each `file:line` citation must lie inside a stored excerpt, quotes must match verbatim, redacted lines can't be quoted, and a `why` needs a cited span that itself states the reason (P4): prose (a commit message, a code comment, or a prose document such as an ADR, outside its fenced code blocks), a reason cue, and terms shared with the reference answer. The generator's `rationale` flag is not trusted, and the check is stored in the verdict. Uncited rationale is never used as a key.
3. **Closed-book check.** A model gets the questions only; the probe grader grades its answers, and a `correct` verdict rejects the candidate as generic. A reply missing, duplicating or inventing an answer id fails the stage instead of inventing empty answers.
4. **Selection.** Two probes are chosen at random with the diff's stored seed. Fewer survivors leave the diff `under_probed`.

Probes are sealed until `captured_at + 7 days`.
- **Sealing (G5).** No command renders a sealed question. A sealed, unselected or unknown probe gets the same refusal, and error messages never echo model output.
- **Answers.** An answer is unassisted unless the owner taps `/looked` or `/ai`. Don't know, unfair and skip are the other responses; skip and don't know are outcomes, never negative evidence, and lateness is recorded.
- **Grading (G3).** One blind grading pass per answer, at `project.grading_reasoning_effort` (default `high`). Grading is claimed with a lock before any call, and each outcome commits with its judgment in one transaction. The owner can contest: the adjudication becomes the outcome of record, the grade is kept, and the owner verdict supersedes the LLM verdict in the judgment log.
- **Practice only (D6).** `evidence_class = 'practice'` and `exposure_isolation = 'unknown'` are SQL CHECK constraints on `probe_responses`.

**Provenance (§5.3).** Three signals are recorded:
- `agent` and `agent_source`, from the trailer, the `--agent` flag or the act of accepting;
- `capture_timing`;
- the optional `project provenance <diff> --accept-style … --usage …` taps.

The report breaks out accuracy and the don't-know/skip rates by each label. Provenance never changes a grade.

**Store (§6.1, D2).** `<vault>/projects/project_store.sqlite`, in WAL mode with `synchronous=FULL` (ADR-015), with `PRAGMA user_version` 2 (2 added `pending_commits`; a version-1 store is upgraded in place). A store from a newer LearnLoop is refused. Tables:
- `repos`, `diffs`, `provenance_reports`, `probes`, `probe_responses`, `unattributed_commits`, `store_meta`;
- `judgments`: the same columns and append-only and supersession triggers as `judgment_ledger`;
- `call_receipts`: the vault receipt columns plus `diff_id`, `disclosure_json`, `cost_label` and `estimated_usd`.

`experiment_store.py` is the registered SQL owner. The package can't import `db.repositories`, `db.stores`, `vault.loader`, the domain packages or the adapters (import-linter), and the G6 test shows `state.sqlite` stays byte-identical through every command.

**Routing and spend (§7, rule 6).**
- **Routes.** `AITask` gains `project`, and `ai.routing.project` falls back to `ai.routing.grading`, then the active provider. The operations are `project_probe_authoring` and `project_closed_book_check` (on the `project` route) and `project_probe_grading` (on the `grading` route).
- **Tool isolation.** Model clients are built around an empty temporary directory instead of the vault root. A directory alone does not stop an agentic transport reading absolute paths, so with `project.require_tool_isolation` (default) Codex runs its app-server in a bubblewrap sandbox (`learnloop.ai.isolation`): no home, vault or repo, an in-memory agent home with only its credentials and config, its own PID namespace. Only the executable itself (or a Node launcher's package) is mounted, the vault and enrolled repos are masked in every mounted tree, and a layout that would put any of them in view (an executable, the working directory or the agent home inside one) is refused. Chat transports are tool-free; any other transport is refused. Receipts record `tool_isolation`.
- **Spend.** Every paid command has caps and `--dry-run`: `sweep`, `probes`, `answer` and `grade`. A dry run opens the store read-only, so it never writes or upgrades it. On the Codex subscription (`codex_sdk`) there is no physical-request bound and no token or dollar cap. Cost is the reported tokens × a $10/M reference rate, labelled `estimated_only`, and the call and candidate caps still stop runaway loops.
- **Metered routes** keep every cap, and each request carries its admitted output budget as the provider's limit. An unknown price fails closed (`--price-per-million`), and a hidden provider retry is admitted only against `--max-retries`. `project probes` spends one budget across generation and grading.
- **No double paying.** Non-blocking locks stop two commands from generating for the same diff or grading the same answers. A crash after a completed call but before its outcome commits re-pays that one call on resume (the paid output stays in the receipt).
- **Retries.** `sweep --retry-failed` and `grade --retry-failed` take failed items back under the same caps and dry-run.

**Report (§8.3 M1).** `project report` (text or `--json`) covers:
- capture coverage: by source, timing, agent and agent source, exclusions, truncations, redactions, unattributed commits, and repos with sweep errors;
- probe validity: citation-resolution failures, closed-book rejection rate, under-probed and failed diffs, and the kinds and rationale labels selected;
- generation cost per diff and answer-grading cost, with cost labels;
- unfair/ambiguous taps, contest rate, and accuracy (unassisted, don't-know-as-zero, assisted);
- by-provenance accuracy and don't-know/skip rates;
- questions tapped unfair (served ones only);
- a version manifest.

Every rate carries its n and a small-sample flag. M1 sets no numeric gate.

**Gates.**

| Gate | Where |
|---|---|
| G1 | `test_project_hooks.py`: the hook exits 0 when the pending file is unwritable, outside a repo, without `git`/`date`, and with the vault gone (it recreates nothing), and commits still succeed. `auto_sweep` survives a missing vault, the kill switch, a vanished repo (reported, not silent) and a locked store. `learnloop project sweep` exits 0 on errors |
| G2 | `test_project_redaction.py` (store and bundle bytes, including `-wal`) and `test_project_cli.py::test_secrets_never_reach_a_model` (every recorded prompt) |
| G3 | `test_project_blindness.py`: the context dataclasses' fields are exactly the allowed set, and the rendered authoring, closed-book and grading prompts contain no agent, trailer, provenance tap, declaration or closed-book origin |
| G5 | `test_project_cli.py::test_no_command_renders_a_sealed_question` (every command, text and JSON) and the API tests in `test_project_probes.py` |
| G6 | `test_project_experiment_store.py::test_m1_never_writes_state_sqlite`: file hash, schema hash and row counts unchanged through enroll, sweep, status, probes, answer, contest, provenance, grade, report and unenroll |
| G7 | Import contract `replay-never-reaches-projects`, plus a test where `rebuild --shadow` and `rebuild-derived-state` run with `subprocess`, the sweep and paid calls patched to fail, and leave the project store untouched |

## Decisions and deviations

1. **Generation is decoupled from capture.** Automatic sweeps run only git, so app start and plan build stay fast and never spend. Generation runs in `project sweep` (unless `--capture-only`) and, for diffs already due, just before `project probes` serves (`project.generate_before_serving`). The spec's "generate at capture" exists for M1b's arm-blindness (P3), which doesn't apply without the gate. Probes are still generated from the stored snapshot, before anything about the answer exists.
2. **M1b tables aren't created.** `assignments`, `gate_events`, `preregistration`, `gate.py` and the `project_gate_judge`, `project_session_classify` and `project_defense_question` operations are left out. The store is versioned, so M1b adds them with `user_version` 3 (2 is the pending queue). `repos.gate_policy` exists and is always `off`.
3. **Verdicts and receipts live in the project store** (G6). The `judgments` columns are identical to `judgment_ledger`, for M2's import. The receipts table is named `call_receipts`, not `model_call_receipts`, so the generated database docs don't list the project store as a writer of the vault table. Owner adjudication uses the same task as the LLM grade (`project_probe_grade`, judge `owner`, `supersedes_id`), because `judgment_ledger`'s supersession rule requires the same task. The plan above named it `project_probe_adjudication`.
4. **Small diffs are probed** (reversed after the Codex review, F14). The spec applies `project.min_diff_lines` only to M1b randomization; a two-line change can flip a comparison. Only captures with no probe-able file are excluded.
5. **A capture window with patch-id dedupe replaces "commits since the last sweep".** It is robust to branch switches, rebases and concurrent sweeps.
6. **Noise files** (lockfiles, minified bundles, source maps) are skipped like secrets, to keep context minimal (P5).
7. **The question header shows repo, files and commit date, never the commit message**, which often states the rationale a `why` probe asks for. The reference shown after answering labels a cited reason `agent_stated` when the agent wrote it: added lines, or the commit message of an agent-committed diff.
8. **A `why` candidate without a cited reason is rejected**, not kept as `inferred`: an uncited rationale can't be an answer key (P4).
9. **The closed-book check and its grade are one call each per diff**, using the same probe-grader prompt, so a diff costs three calls: authoring, closed-book and grading. A closed-book `partially_correct` keeps the candidate.
10. **Skip is a final outcome** (§5.3 reports it as one). `/quit` leaves questions due.
11. **"Plan build" means the Today queue.** The daily plan doesn't exist yet, so the plan-build hook is the sidecar's `get_today_queue`. The daily-loop plan builder should call `auto_sweep` the same way.
12. **Config.** The new `[project]` section and `ai.routing.project` are additive, and nothing served from the vault changes. So `DEFAULTS_SNAPSHOT_BY_ALGORITHM["mvp-0.9"]` was updated with a comment rather than a new algorithm version, as Phase 1 did. The `project.*` knobs are classified structural/operational in the parameter registry (no vault measurement authority). The template gains a comment-only hint for `ai.routing.project`.
13. **Test-only git isolation.** `tests/project_support.py` points `GIT_CONFIG_GLOBAL` at a temp file and sets `GIT_CEILING_DIRECTORIES` to pytest's temp root. pytest's temp root lives inside this checkout, and without the ceiling a test discovered the LearnLoop repo itself. The production git wrapper strips only repo-retargeting variables (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, …), so user settings still apply.
14. **Docs.** Regenerating the reference stamps every note with the current commit. Only substantive changes were kept:
    - `Config - project.md`, which is new;
    - shifted `schema.py` line citations;
    - pre-existing test-reference drift in a few table notes;
    - the prose leaf counts, now 530 leaves in 29 sections.

## Gate results (final, at `7a6d0ac9` plus this review file)

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **8 contracts kept, 0 broken** (two new: `projects-stay-standalone`, `replay-never-reaches-projects`) |
| `uv run pytest -n auto` | **6,256 passed**, 14 existing deprecation warnings, 240 s |
| `uv run pytest -m durability` | **63 passed**, 6,193 deselected |
| Project tests with `--durable-sqlite` | **104 passed** |
| `db_generate_reference.py` + `db_validate_reference.py` | **0 errors**; schema head 166 (no migration), 261 table notes, 530 config leaves, 29 sections |
| Frontend | Not changed; npm checks not applicable |
| Manual run on a backup-API copy (`fixtures-local/projects-m1-smoke` from `fixtures/conic-sections`), with `LEARNLOOP_CONFIG_DIR` isolated and a scratch repo | `enroll --install-hook` captured the agent commit and skipped `.env`. `sweep --dry-run` estimated 3 calls and 15,911 tokens on `codex_low`, `estimated_only` at $0.16, with no calls. A human commit went through the hook into the pending list and showed up as unattributed in `status`. `state.sqlite` sha256 unchanged. No model was called |

The first full run failed nine tests, all from the new config leaves: the defaults fingerprint snapshot, and the parameter registry's leaf classification (`test_registry_audit.py` ×5, `test_grading_cli.py` ×2, `test_p0_cutover_mvp08.py`, `test_config_refactor.py`). Both were fixed as described in decision 12.

## Files touched

- **New:**
  - `src/learnloop/projects/` (`__init__`, `git`, `redaction`, `capture`, `hooks`, `ai_contracts`, `ai_runtime`, `probes`, `experiment_store`, `report`);
  - `src/learnloop/cli/project.py`;
  - `tests/project_support.py`;
  - `tests/test_project_{capture,redaction,probes,blindness,hooks,experiment_store,report,cli}.py`;
  - `docs/learnloop-architecture-vault/Reference/Configuration/Fields/Config - project.md`.
- **Changed:**
  - `src/learnloop/ai/routing.py`;
  - `src/learnloop/config/schema.py` and `template.py`;
  - `src/learnloop/ops/startup.py`;
  - `src/learnloop/params/parameter_registry.py`;
  - `src/learnloop/cli/__init__.py`;
  - `src/learnloop_sidecar/handlers/queue.py`;
  - `pyproject.toml`;
  - `tests/structured_ai.py` (project handlers and `RecordingStructuredClientFake`), `tests/test_architecture.py` and `tests/cli_help_snapshot.json`;
  - the config and table reference notes, and `db_generate_reference.py`.

## Migrations

None. No vault table, algorithm version or rebuild path changes.

## Owner-run commands

Run these against your real vault, or against a `fixtures-local/` copy first. Nothing below runs until you enroll a repo. On the Codex subscription, generation and grading have no marginal cost: the figures are `estimated_only`. A metered route needs `--price-per-million`.

Optional, recommended for question quality: route authoring to the medium-effort profile in `learnloop.toml`:

```toml
[ai.routing]
project = "codex_medium"   # empty = the grading route (codex_low)
```

**1. Enroll each repo you want questions about** (once each):

```bash
learnloop project enroll ~/path/to/repo --install-hook --vault <vault>
# --since-days N also captures agent commits from the last N days (default 7);
# --install-hook adds the append-only post-commit hook (optional).
```

**2. Sweep and status.** Capture is automatic at app start and when the Today queue builds. To generate questions, dry-run first:

```bash
learnloop project sweep --dry-run --vault <vault>   # estimate; no calls, no writes
learnloop project sweep --vault <vault>             # capture + generate (~3 calls per diff)
learnloop project status --vault <vault>            # counts; never shows a question
learnloop project status --disclosure --diffs --vault <vault>
```

**3. Answering probes** (each diff's two questions are due 7 days after capture):

```bash
learnloop project probes --vault <vault>                 # interactive; from memory
#   end an answer with an empty line; /dk  /unfair  /skip  /quit;
#   add /looked or /ai if you looked at the code or used AI
learnloop project probes --list --vault <vault>          # due questions with ids
learnloop project answer <probe_id> --text "..." --vault <vault>
learnloop project contest <response_id> --score 0.7 --note "why" --vault <vault>
learnloop project grade --vault <vault>                  # retries grades that failed
learnloop project accept --commit <sha> --agent codex --repo <repo> --vault <vault>   # agent work without a trailer
learnloop project provenance <diff_id> --accept-style all_at_once --usage it_designed --vault <vault>   # optional
```

**4. The report** (review it before M2):

```bash
learnloop project report --vault <vault>        # or --json
```

## Open questions

1. **Authoring route.** By default, `project` follows the grading route (`codex_low`, low reasoning effort). Answer-first authoring with verbatim citations may need `codex_medium`; the commands above suggest the override. Should the template route `project` there by default?
2. **Background generation in the desktop app.** Generation runs in the CLI (`sweep`, or just before `probes` serves). For probes to be ready without waiting, M2's sidecar handler could generate in the background for subscription routes. Is that acceptable?
3. **Other people's agent commits.** In shared repos, commits with agent trailers written by other people (merged from a remote) are captured too. That is fine for single-owner repos. Should M2 filter by author email?
4. ~~Closed-book isolation is cwd-level only.~~ Resolved (F2): Codex runs in a bubblewrap sandbox. If bubblewrap can't create a sandbox on a host, project calls on Codex are refused; `project.require_tool_isolation = false` is the kill switch.
5. **The `.learnloopignore` used is the working tree's current file**, not the file at `head_sha`. This follows the owner's latest intent, and the hash is recorded per capture.
6. **M2 import mapping.** `judgments` → `judgment_ledger` unchanged. `call_receipts` → `model_call_receipts` needs a home for the disclosure and cost-label fields: new columns, or a side table.
7. ~~The trivial-diff threshold for probing.~~ Resolved (F14): M1 probes every diff with probe-able content.
