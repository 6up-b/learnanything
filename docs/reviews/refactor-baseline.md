# Refactor baseline (S0)

Step S0 of `docs/specs/refactor_strategy_v3.md` (§2.2): the refactor's "before". **Tip: main `a810f628d8`** (branch `refactor/map`), Nov 9 2026. By then phone V4, instruct/handoff (mvp-0.55, migration 251), the test-suite audit, the placement fix (mvp-0.56), RE0 (migration 252) and slip or gap (mvp-0.57) had all landed. Z2 reruns everything here with the same script and the same commands. The map's corrections from this step are in `docs/reviews/architecture-map-2026-11-08.md` ("Corrections at S0").

**The Nov 7 figures are history, not the before.** The Nov 7 gate's `-n 8` time (59:22, 27,650 test seconds) and the serial 7:02:47 at `a525dbcef4` were taken before the test-suite audit landed, and that audit cut test seconds by about three quarters. Speed claims compare against the timed lanes below.

## How it was measured

One script, `scripts/refactor_measures.py`. It runs a computed sweep over tracked files (seconds) and, when asked, the three timed suites. Each Python or CLI run went through a wrapper:

```
env -i PATH=$PATH HOME=<empty dir> CODEX_HOME=<empty dir> LEARNLOOP_CONFIG_DIR=<empty dir> LANG=C.UTF-8 \
  UV_CACHE_DIR=$HOME/.cache/uv TMPDIR=<dir> "$@"
```

The timed runs add `XDG_RUNTIME_DIR=/run/user/1000`, because `systemd-run --user` can't reach the user bus without it. Their `TMPDIR` was a directory on the home disk (btrfs, outside the worktree), not tmpfs, because `/tmp` had 3 GB free. Z2 should use the same kind of disk: the durability lane's fsyncs cost more on disk than on tmpfs. The venv had the `dev` and `mobile` extras (`uv sync --extra dev --extra mobile --inexact`; `pypdfium2` was missing before that), so no phone-host test skipped for lack of it.

**Computed (fast):**

```
<wrapper> uv run python scripts/refactor_measures.py --json <out>.json --markdown <out>.md
```

**Timed:** one lane per call. Each call holds the full-suite lock, because the script doesn't take it:

```
flock /tmp/learnloop-fullsuite.lock <wrapper + XDG_RUNTIME_DIR> uv run python scripts/refactor_measures.py \
  --timed <lane> --json <out>.json --markdown <out>.md
```

The script then runs each lane exactly as follows. The JUnit XML lands in gitignored `fixtures-local/refactor-measures/`:

```
serial: systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G uv run pytest -q -p no:cacheprovider --junitxml=/home/saturn/Documents/thinking/learnanything-refactor/fixtures-local/refactor-measures/serial.xml
n8: systemd-run --user --scope --quiet -p MemoryMax=10G -p MemorySwapMax=1G uv run pytest -q -p no:cacheprovider -n 8 --dist worksteal --junitxml=/home/saturn/Documents/thinking/learnanything-refactor/fixtures-local/refactor-measures/n8.xml
durability: systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G uv run pytest -q -p no:cacheprovider -m durability --junitxml=/home/saturn/Documents/thinking/learnanything-refactor/fixtures-local/refactor-measures/durability.xml
```

The invocations, verbatim, for one lane (`<lane>` is `n8`, `durability` or `serial`):

```
flock /tmp/learnloop-fullsuite.lock bash -c "<scratch>/iso-timed.sh uv run python scripts/refactor_measures.py --timed <lane> --json <scratch>/timed-<lane>.json --markdown <scratch>/timed-<lane>.md > <scratch>/timed-<lane>.log 2>&1"
```

`iso-timed.sh` is `exec env -i PATH="$PATH" HOME=<scratch>/home CODEX_HOME=<scratch>/codex LEARNLOOP_CONFIG_DIR=<scratch>/cfg LANG=C.UTF-8 XDG_RUNTIME_DIR=/run/user/1000 UV_CACHE_DIR=/home/saturn/.cache/uv TMPDIR=/home/saturn/.cache/refactor-s0-tmp "$@"`, with each directory existing and empty.

Lanes ran in the order `n8`, `durability`, `serial`, one after another, each in its own lock hold.

## Tests (item 13)

| Lane | Wall clock | Result | Test seconds | Upgrade and successor family | Load average at the end |
|---|---:|---|---:|---:|---|
| **`-n 8 --dist worksteal`** (10 GB) | **18:40** (1,119.8 s) | 30,894 passed, 96 skipped, 47 xfailed, 0 failed | **8,508.5** | 218 s, **2.6%** | 10.2 (11.9 over 5 min) |
| **`-m durability`**, serial (5 GB) | **7:16** (435.8 s) | 417 passed, 1 skipped | 426.6 | 0 | 4.6 |
| **Serial** (5 GB) | **2:01:13** (7,273.4 s) | 30,894 passed, 96 skipped, 47 xfailed, 0 failed | **7,193.3** | 175 s, 2.4% | 3.9 (1.6 over 15 min) |

The lanes ran from 18:30 to 20:58 on Nov 9. The `-n 8` lane overlapped another agent's targeted runs; the serial lane mostly ran on a quiet machine. The serial lane's test seconds are lower than `-n 8`'s (7,193 against 8,509), because eight workers contend for the CPU. The audit estimated about 1:50 serial; it took 2:01.

**History, not the before:**
- **Nov 7 gate at `5a9dae936f`:** 59:22 at `-n 8`, 27,650 test seconds, family 16%.
- **Serial at `a525dbcef4`:** 7:02:47.
- **Test-suite audit's landing gate (`0439d1ad06`):** 16:36 at `-n 8`, durability 7:08.

**The `-n 8` lane in detail** (from its JUnit):
- **31,037 cases.** The median test takes 0.019 s, the 90th percentile 0.43 s and the 99th 4.7 s. 23,325 take under 0.1 s.
- **Where the seconds are.** The top 10 tests hold 942 s (11%), the top 100 hold 27%, the top 500 hold 51% and the top 1,000 hold 64%.
- **Slowest files:**

  | File | Seconds |
  |---|---:|
  | `test_ad23_sim` | 744 |
  | `test_ih2_one_open_offer` | 303 |
  | `test_ih4_preferences_inform_router` | 223 |
  | `test_rofu_weeks` | 207 |
  | `test_evsi_multisim` | 197 |
  | `test_ro6_tail_data` | 187 |
  | `test_ih2_lessons_compete` | 156 |
  | `test_ad_protected_readings` | 119 |
  | `test_ih_numeric_seed` | 114 |

  IH's tests are now four of the nine slowest, at about 800 s together.
- **Skips:** 83 in the owner lane (`LEARNLOOP_OWNER_VAULTS` unset), 8 for torch (no `pdf` extra), and one each for the GPU smoke test, a non-Codex provider, a base-tree golden, `openai_codex` (not in any gate, by the owner's decision) and missing `node_modules`.

| Measure | Baseline | Target |
|---|---|---|
| Serial; `-n 8 --dist worksteal`; `-m durability` | above | the same commands at Z2. No fixed target; each removal reports its seconds |
| Upgrade and successor family | **218 s of 8,508, 2.6%** (`-n 8`; it was 16% on Nov 7) | under 3%: **already met at S0**, because the audit cut the chain walks from 138 s to about 7 s. Z2 reports it in seconds |
| Tests run on the served path | **269** files use the default vault at mvp-0.6 and name no version (450 use it) | 0 |

## Size and rules

| Measure | Map (`a525dbcef4`) | **S0 (`a810f628d8`)** | Target (Z2) |
|---|---:|---:|---|
| Python files, all four packages | 1,268 | **1,285** | down 6-11% |
| Raw lines; code lines | 624,515; 436,042 | **632,055; 441,708** | down 5-9% |
| Statements; functions | | 278,774; 22,232 | |
| Functions over 100 lines; over 200 | ; 81 | **477; 83** | down; `build_due_queue` and `_compute_resolved_grade_application` out of the list (both still in it, at #2 and #3) |
| Root `*_upgrade.py`; all upgrade modules (lines) | 40; 42 (about 8,900) | **43; 45 (9,613)** | 0; 1 table module |
| `Repository` methods | 943 | **945** | at least 58 fewer |
| `mvp-0.N` literals: code / docstring / comment | 285 / 949 / 3,070 | **310 / 987 / 3,144** | under 60 / under 300 / under 500 |
| Tag gates: constant at the floor (mvp-0.43) / all | 79 / 90 | **79 / 94** (15 varying, 0 unclassified) | 0 / only tags above the floor |
| Tags in the chain; latest | 45 | **48; mvp-0.57** | |
| Kill switches at or below the floor | 27 named, at least | not recounted (manual; procedure below) | 0, except any the owner keeps |
| Import-linter contracts | 43 | **43** | lower; each kept contract readable |
| `config/template.py`; `config/schema.py` lines | 4,203; | **4,255; 5,218** | about 450 for `template.py` |
| Migrations (`.sql` files) | | 239 | |
| Removed list | | none yet | every removed feature named in Z2's report |
| Database size | private | private: `fixtures-local/refactor-map/table-counts-20261109.md` (Nov 9 backup copies) | reported before and after each drop |

The 15 varying gates are listed in the script's JSON (`varying_sites`). Three are new since the map: `FAILURE_SHARE_VERSIONS` (two sites), `UNEVIDENCED_RETURN_VERSIONS` and `SLIP_GAP_VERSIONS`.

## The plumbing list (test-suite audit §7), at this tip

The audit counted these on its branch at mvp-0.54. Three tags have landed since, and every item has grown. Recounted by the script:

| Item | Audit (§7) | **S0** | Step |
|---|---:|---:|---|
| Frozen `X_VERSIONS == frozenset({...})` assertions (files) | 36 | **46 (44)** | A3 |
| Test files with a "latest" pin (`LATEST`/`SUCCESSOR_CHAIN[-1] == "mvp-0.N"`) | in each successor test | **40** | A3 |
| Test files naming the latest tag; a tag at or above mvp-0.43; any tag | 46 name a recent tag | **50; 106; 353** | A3, D3 |
| Frozen defaults digests; test files reading them | 48 files | **48 digests; 51 files** (any `tests/*.py`, helpers included) | A2 |
| Test files carrying the `timeout_seconds = 8.0` preamble | | **11** | A2 |
| Head fixture path: test files + scripts (lines) | 68 + 3 | **70 + 3 (77)**; fixture `migration_head_252`, 24 files | A2 |
| Generated notes; with commit stamps | 593 of router speed 2's 615 files | **2,176 of 2,270 vault notes, all 2,176 stamped**; RE0's head commit changed 561 of them | A1 |
| Chain tests that `_pass_guard` | through mvp-0.12 | not recounted | D3 |
| Default test vault (`create_basic_vault`) | mvp-0.6 | **mvp-0.6; 450 files use it, 269 name no version** | D2 |
| Upgrade and successor test files (lines) | 34 (8,808) | **36 (9,535)** | D3 |

**The audit's source changes,** outside its brief and still open:
- `parameter_registry.refresh` inside `repository.pinned()`;
- reusing `Repository.connection` across a request;
- the DML-keeping pool rule;
- a content-derived id for the built-in outcome schemas.

They feed F1 and F2 (connections) and D3 (the refresh's cost on upgrades). None has a step of its own here.

## What a change costs (files edited)

"Today" is the strategy's figure where nothing has changed, and a fresh count where S0 could make one from a landed commit.

| Sample change | Today | How counted | Target |
|---|---|---|---|
| Threshold or default (40 s timeout) | 1 line, **48** digests (46 at the map), 12 test files, 1 note | carried; digest count rerun | 1 line; 1 golden line; at most 1 test literal; 1 note |
| A new table (or column) | Migration, roles, AD's 2 lists, store; then the head-fixture commit: **658 files** at RE0 (`f72b034551`): 24 fixture files (22 renamed unchanged), 70 test files, 1 script, `CLAUDE.md`, 1 `src` line, 561 generated notes | RE0's landing commits | those 5; 2 fixture files; 0 pins; a handful of notes |
| Speed work with no version (router speed 2) | 615 files (9 source, 593 notes) | carried | about 110 at most |
| A new tag | 9 source files, 36 pinned tests, 101 digest lines | carried. Since the map, three tags added 3 upgrade modules and 2 successor tests, and edited 35 existing upgrade and successor test files between them | 1 constant, 1 table row, 1 test row, plus its switch |
| Add a sensor (objective) | 11, 7 files | carried | `daily_plan/sensors.py` and its test |
| Change an objective term | 3, 6, 4, 1 files | carried | `router_objective/objective.py` and its test |
| Swap the mixing rule | 13 files, 47 lines of rule | carried | `mix.py` and its test |
| Add an action | 20 files | carried | `router_objective/actions.py`, its test, a trace label |
| Change a seed or prior | 1 line, plus digest churn | carried | as a default |
| Prompt | 1 file and a bump, plus goldens per parity test | carried | 1 file and bump; goldens only for that prompt |
| New signal to model contexts (TE0) | 11 files | carried | the signal's function, one line per builder |
| New step in a pipeline | not a number | time to locate, below | Developer Map names the seam |
| **A model route** | **41 files, 28 of them tests:** Decider v1.2's default move. `b8b25b8337` changed 28 files: 4 `src` (97 lines of `config/template.py` are recomputed digests), 1 frontend test, 1 generated note, 7 specs, 15 tests and fakes. `60303f7d4f` added 12 frozen-digest test files, and `8cdc296b4b` 1 more at IH's merge | landed commits, not a scratch branch: a recent route change did land alone | 1 default, 1 golden line |

## Speed

**Not remeasured at S0.** The router speed harness on large copies is F1's step 0. Its target is "after IH's prefetch", and IH has now landed, so F1 measures against the Nov 9 backup.

| Measure | Baseline (carried) | Target |
|---|---|---|
| Next right after feedback, large copies | Median 2,676 ms, 16 of 21 over 2 s (router speed 2), against mvp-0.49's 2,250 ms, 25 of 30 (a pinned week) | No worse than mvp-0.49's by the same method, after IH's prefetch |
| Connection opens per job | 17 | about 5 |
| Decision values at a fixed draw count | | byte-identical across every speed step (P-draw) |

## Inspectability

| Measure | At S0 |
|---|---|
| The four real cases | `learnloop why` doesn't exist yet; neither test file does. **The rows exist:** the Nov 9 backup (migration 250, mvp-0.54) has rows of the shape each case needs on `arxiv_v2`. Counts are private (`fixtures-local/refactor-map/table-counts-20261109.md`) |
| `why` on the latest decision, an attempt, a block, a figure | no `why` |
| Silent sites S1-S15 | none has a fail-first test or an ADR-017 line (ADR-017 doesn't exist) |
| Decisions with no record | no inventory yet (B8) |

## Time to locate

**Procedure.** S0 and Z2 use the same procedure. Five fresh read-only agents run in parallel, one per symptom. Each gets only the symptom, the checkout and the documentation vault. At S0 `why` didn't exist, so it was left out; at Z2 it's added. The agents are Claude Code `Explore` agents on the session model (Opus 5.5).
- They may read `src/`, `tests/`, `migrations/`, `apps/`, `pyproject.toml`, `CLAUDE.md` and `docs/learnloop-architecture-vault/`.
- They may not open `docs/reviews/`, `docs/specs/`, `docs/brainstorming/`, `reports/`, `research_notes/` or git history, which hold the answer keys. They run no code.
- Each records `date +%s` first and last, the files it opened in order, and its searches. The harness's duration and tool-use count are recorded too.
- The answer is graded against the bug's review.

The prompt template is at the end of this file.

| # | Symptom | Self-timed | Harness | Files opened | Searches | Correct |
|---|---|---:|---:|---:|---:|---|
| 1 | Dormant or resolved learning objects are still served (`daily-loop-bugs.md` §2) | 38 s | 53 s, 12 tools | 3 (10 with a call-site scan) | 8 | Yes. `vault/lifecycle.py` and every door; the module's docstring lists them |
| 2 | Choosing a help style changed nothing (owner capture B2) | 40 s | 60 s, 15 tools | 8 | 12 | Yes. `hints/chooser.py` `fallback_choice`, workbench `styled_level`, the reuse in `service.py`. Found through the fix's comments |
| 3 | The scheduler offer does not belong to this item/session (B4) | 21 s | 38 s, 11 tools | 4 | 4 | Yes. `db/stores/collection.py` `_offer_open`/`require_offered`, and the sidecar's stale-offer fix. Found by grepping the message |
| 4 | A router decision fell back to a rule: which model failed and how | 49 s | 73 s, 17 tools | 8 | about 12 | **Partly.** It found `router_decisions.fallback`, `detail_json`'s `fallback_reasons` and `mixture.models.*` (status, error cut to 200 characters), and the receipts. But it led with the older `router_chooser` path, not the objective chooser that serves at mvp-0.57. It missed the chooser-crash fallback (`<error: Type>`, message lost, map S1) and the timed-out answer dropped with no payload |
| 5 | Where do I change the mixing rule, an objective term, a route, a threshold? | 78 s | 105 s, 21 tools | 5 | about 36 | Yes for all four. It caught the Developer Map naming `_terms` (the trace's breakdown) as the objective, where the objective is `_Ledger.q`; fixed in this step |

**Reading it.** Symptoms 1-3 are fixed bugs whose fixes left comments naming the review, so a grep finds them in under a minute. Z2 will measure the same thing. The comment convention (C1) removes review names from comments, which may make these slower at Z2; the Developer Map and `why` are meant to make up for it. Symptom 4 is the one the strategy targets, and it's the one a fresh agent got partly wrong.

## Manual measures, and how each is taken

- **Time to locate:** above.
- **The four real cases:** `tests/test_why_cases.py` passes. `tests/test_why_real_cases.py` passes on a backup-API copy of the owner's fresh backup, under `fixtures-local/why-cases/`. A no-code reader answers from `why`'s output, and the owner judges the answers.
- **`why` coverage:** `learnloop why` answers the latest decision, an attempt, a block and a figure. Each answer has the chosen option, the alternatives, the losers' reasons, inputs, decider, versions, seed and what came next.
- **Silent sites S1-S15:** each has a fail-first test, or a line in ADR-017 saying why not.
- **Decisions with no record:** B8's inventory lists none unexplained.
- **What a change costs:** on a scratch branch at Z2, make each sample change above and count the files edited (`git diff --stat`).
- **Next right after feedback; connection opens per job:** the router speed harness on large backup-API copies (`docs/reviews/router-speed2.md`, its method and pinned week), against mvp-0.49 by the same method.
- **Decision values at a fixed draw count:** P-draw, byte-identical across each speed step.
- **Kill switches at or below the floor:** read D7's list, and count the switches whose tag is at or below the floor.
- **Tag gates paired with a kill switch:** read each site in the JSON's `constant_sites`. The split isn't syntactic.
- **Database size:** each live vault's `state.sqlite` size before and after each drop. It's private, kept in `fixtures-local/` and never committed. At S0 it's the Nov 9 backup's three databases.
- **Removed list:** Z2's report names every removed feature.

## The owner's backup at S0

- **Used for:** J1's table list and the four cases' availability, as the strategy says.
- **Copies:** backup-API copies (`learnloop.db.copies.backup_database`) of `~/learnloop-backups/20261109-copy/{arxiv_v2,linear_algebra,probability}/state.sqlite`, under gitignored `fixtures-local/refactor-map/copy-20261109/`. The stale empty `probability/.learnloop/state.sqlite` was skipped.
- **Tables:** all three are at migration 250, with 395 tables each. Every one is in `db/table_roles.py`, whose 396th is 251's `router_learner_preferences`.
- **Private counts:** per-table rows, newest dates and file sizes are in `fixtures-local/refactor-map/table-counts-20261109.md`.

## Not verified

- **Speed:** not remeasured (above).
- **Kill switches at or below the floor; chain tests that `_pass_guard`:** not recounted.
- **Time to locate:** one run per symptom, so no variance. The agents' self-reported file counts were taken as given, and their harness durations include model latency.
- **Load during the timed lanes:** they ran while another agent worked in a separate worktree, so the machine wasn't idle. Load averages are recorded with the lanes.
- **Part of §6 that isn't S0's to measure:** the change-cost rows marked "carried" are the map's and the strategy's counts, not recounted at this tip.

## Appendix: the time-to-locate prompt

Each agent got this. The symptom texts are in the table above. Symptoms 4 and 5 were phrased as a developer's question: "which model failed, and how; tell me exactly what I would read in a vault (tables and columns, or logs)", and "for each, list every file I would have to edit for the change to be complete".

> You are timing how long it takes a fresh engineer to locate code in the LearnLoop codebase. This is a measurement: work as you naturally would, but keep an honest log. Checkout (read-only): `<worktree>`. You may read anything under src/, tests/, migrations/, apps/, pyproject.toml, CLAUDE.md and the documentation vault docs/learnloop-architecture-vault/ (start at its Home.md or Maps/Developer Map.md if you like). Rules: read only, change nothing, create no files in the checkout. Do NOT open docs/reviews/, docs/specs/, docs/brainstorming/, reports/, research_notes/ or any git history (no git commands at all): they contain the answer key. Do not run Python, pytest or the learnloop CLI. [No vault, backup, config or credential paths.] Timing: your very first action is `date +%s`; your very last action before answering is `date +%s` again. Count files opened [...]. The symptom you are given (the bug may already be fixed in this code, in which case locate the code that now decides it): "<symptom>". Answer with: (1) where the behaviour is decided: file:line and function; (2) how you know; (3) confidence; (4) start and end epoch seconds; (5) the ordered list of files opened and the count; (6) how many grep/find searches you ran.
