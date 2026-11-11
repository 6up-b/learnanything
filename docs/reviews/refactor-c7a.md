# Refactor C7a: `textual` moves to a `tui` extra

Arc C ("delete what's proven dead"), step C7a of `docs/specs/refactor_strategy_v3.md` §2.5. Branch
`refactor/c7a-tui-extra`, based on main `c828893847` (the arc C batch: C1 + C3 + C4 landed). Owner decision 7
(Nov 11): C7 removes no CLI command and leaves `experiments/` whole, so C7 is only C7a. C2 and C5 run in parallel;
this step stays in `pyproject.toml`, `uv.lock`, the `today` command, the TUI's test files and the notes it makes
false.

The old `src/learnloop/tui/` stays working and frozen (owner, Nov 9: rebuilt from the ground up after the refactor).
Nothing in it is edited or deleted here; `tui-keeps-the-open-queue` (DL1) stays.

## Step 0: proved again at `c828893847`, before any change

The step moves one dependency and deletes nothing, so the candidate is the `textual` requirement itself: what
imports it, and what reaches those importers.

| What | Evidence at this tip | Verdict |
|---|---|---|
| `textual` imports in `src/` | `src/learnloop/tui/` only: `app.py` (2), `screens/feedback.py` (6), `screens/practice.py` (7), `screens/start.py` (7), `screens/today.py` (6), `theme.py` (1), `widgets.py` (2). `tui/state.py` and `tui/minutes_memory.py` import none. No `importlib` or string mention of `textual` anywhere else in `src/`, `scripts/`, `experiments/`, the vault `_scripts/` or `apps/` | move to the `tui` extra |
| Who imports `learnloop.tui` | in `src/`, only `learnloop/app_launch.py:11` (`launch_tui`, function-local); `launch_tui` is called only by the CLI `today` command (`cli/app.py:4184`, function-local). Not `learnloop_sidecar`, `learnloop_mobile`, `learnloop_mcp`; not in `METHOD_REGISTRY`, `MODULE_INVENTORY` or `_reg_const`; the `tui-is-independent` and adapter contracts already forbid every other adapter from importing it | the TUI loads only on `learnloop today` |
| Frontend, phone, scripts | no `tui`, `textual` or `learnloop today` in `apps/` (Tauri, phone PWA), `scripts/`, `deploy/`, `integrations/` | nothing else launches the TUI |
| Replay, rebuild, upgrade | the TUI writes through the same repository calls as other surfaces, plus its remembered minutes file (`tui/minutes_memory.py`, in the machine-global config dir); no replayer, rebuild path or migration names `learnloop.tui` or `textual` | no stored row or config changes meaning |
| Textual's own dependencies | `markdown-it-py[linkify]`, `mdit-py-plugins`, `platformdirs`, `pygments`, `rich`, `typing-extensions`. No module outside `tui/` imports `mdit_py_plugins`, `platformdirs`, `pygments`, `linkify_it`, `typing_extensions` or `rich`; `rich` stays in the base install through `typer`; the one other `MarkdownIt` (`scheduling/device_eligibility.py:107`) is `"commonmark"`, which needs no linkify | the base install loses nothing it uses |
| Test files | 15 `tests/test_*.py` files import `learnloop.tui` (with `tests/helpers.py`'s `begin_session`, the strategy's "16 test files"; the same set as at the TUI's last change, `3c5f0cbca8`): 9 at module level (`test_active_errors_overlay`, `test_daily_loop_start_minutes`, `test_daily_loop_start_postpone`, `test_e2e_tui`, `test_tui_app`, `test_tui_feedback`, `test_tui_practice`, `test_tui_theme`, `test_tui_today`) and 6 inside single tests (`test_model_call_receipt_owners`, `test_pfc_unverified_unassessed`, `test_provider_resolution_parity`, `test_serve_eligibility`, `test_stuck_prompt`, `test_ux_phase4_feedback`). At the base, the 15 files: 899 passed, 6 skipped, 32.5 s at `-n 4` | kept; each skips cleanly without `textual` |
| `tests/cli_surface.json` | `today` has one parameter, `--vault`; this step keeps it | unchanged (compatible) |

**Learner reach and fixed inputs.** Nothing that serves, grades, schedules or replays changes. The only behaviour
change is `learnloop today` on an install without the extra: it prints the install hint and exits 1 instead of a
`ModuleNotFoundError` traceback. With the extra installed (the landing gate's sync), `today` runs the same TUI.

## What changed

Nothing was deleted: the step moves a dependency. Source and lock: 22 lines added, 5 removed.

- `pyproject.toml`: `textual>=8.2.7` leaves `[project] dependencies` for a new `tui` extra (6 added, 1 removed).
- `uv.lock`: re-resolved with `uv lock --offline` (no network needed): `textual` moves from learnloop's
  dependencies to `optional-dependencies.tui`, its `requires-dist` row gains `extra == 'tui'`, and
  `provides-extras` gains `tui`. No package version changed (5 added, 3 removed).
- `src/learnloop/cli/app.py` `today`: a `ModuleNotFoundError` whose module is `textual` (or under it) prints
  `The terminal app needs the tui extra: uv sync --extra tui (or pip install 'learnloop[tui]')` to stderr and exits 1;
  any other missing module still raises (11 added, 1 removed). The same shape as `learnloop mcp serve`'s check for
  the `mcp` extra. `today`'s parameters and help are unchanged, so `tests/cli_surface.json` is untouched.
- `src/learnloop/tui/` and `app_launch.py`: unchanged.

**Tests (no test removed, so no seconds saved).** The TUI's tests now skip cleanly without textual, so the landing gate
(which syncs dev + mobile + tui) still runs every one of them:
- 7 files that are wholly about the TUI start with `pytest.importorskip("textual")`: `test_daily_loop_start_postpone`,
  `test_e2e_tui`, `test_tui_app`, `test_tui_feedback`, `test_tui_practice`, `test_tui_theme`, `test_tui_today`.
- 2 files whose other tests need no TUI keep those running: `test_active_errors_overlay` builds its `FeedbackScreen`
  stub in a function and its 2 TUI tests call `importorskip`; `test_daily_loop_start_minutes` imports the TUI's screens
  in a `try` (re-raising anything but a missing textual) and marks its 8 TUI tests `needs_textual`
  (`minutes_memory` needs no textual and stays a plain import).
- 9 single tests that import the TUI inside the test call `importorskip` first: `test_model_call_receipt_owners` (1),
  `test_pfc_unverified_unassessed` (1), `test_provider_resolution_parity` (the TUI row of the six-site AST check, and the
  matrix test that runs all six), `test_serve_eligibility` (1), `test_stuck_prompt` (4), `test_ux_phase4_feedback` (1).
- `test_architecture::test_every_runtime_module_imports` exempts a `learnloop.tui.*` module only when the missing
  module is textual.
- New `tests/test_tui_extra.py` (3 tests, the step's proof, below).

**Docs.** `README.md`: `today` needs the `tui` extra (quick start), and the dev install line adds `--extra tui`.
Vault: `Architecture/Adapter Architecture.md` (the TUI row and the adapter paragraph), `Workflows/Start a Learning
Cycle.md` and `Examples/First Learning Session.md` (`today` needs the extra). References regenerated once
(`b270cd3a42`: `cli/app.py`'s module note and the line cites below `today` moved by 10, `app_launch.md`'s caller
line, the catalogs and `_generated.md`); a second `generate_all.py` run changed nothing.

`CLAUDE.md`'s `uv sync` line is not edited here: an agent does not change `CLAUDE.md` on another agent's word. The
line the orchestrator or owner can apply: `uv sync --extra dev --extra mobile --extra tui   # install; without
--extra mobile ~40 phone-host tests skip silently, without --extra tui the terminal app's tests skip (add --extra pdf
for Marker; manim is a core dependency)`.

## Proofs

- **The TUI's test files pass with the extra** (the 15 files, plus `test_tui_extra` and
  `test_every_runtime_module_imports`): 903 passed, 6 skipped, 29.6 s at `-n 4` (base: the 15 files, 899 passed,
  6 skipped, 32.5 s; the 6 skips are the same `owner_vaults` ones).
- **The same set with textual hidden** (a `-p` pytest plugin putting a `sys.meta_path` hook first that raises
  `ModuleNotFoundError(name="textual")`, as a missing package does): 859 passed, 37 skipped, 0 failed, 26.6 s; every
  new skip names textual, and the architecture import test passes.
- **`tests/test_tui_extra.py`** (3 passed, 3.3 s): in a subprocess with that hook, `import learnloop`,
  `learnloop.app_launch`, `learnloop.cli.app` and `learnloop_sidecar.handlers` leave `textual` out of `sys.modules`,
  and `learnloop --help` exits 0 listing `today`; `learnloop today --vault <dir>` exits 1 with both install lines on
  stderr and no traceback; in process, a missing `textual.widgets` gets the hint and a missing other module still
  raises. Fail-first: at the base `cli/app.py`, the last two fail (a `ModuleNotFoundError` traceback); `--help`
  already passed there, since `today` already imported the TUI lazily, and now guards it.
- **Targeted tests:** `scripts/affected_tests.py` falls back to the whole suite (`pyproject.toml` and `uv.lock` are
  inputs every test depends on), so the list is explicit: the selector on the diff without those two files (244 test
  files, through `cli/app.py`, the edited tests and the docs) plus `test_architecture`, `test_test_layout`,
  `test_cli_help_snapshot`, `test_cli_json`, `test_effective_defaults_golden`, `test_tui_extra` and the 15 TUI files:
  246 files, `-m "not arc_close" -n 4`: 4,917 passed, 31 skipped, 3 xfailed, 1 failed in 482 s. The failure,
  `test_regrade_contract_upgrade::test_an_upgrade_interrupted_after_publication_is_resumed`, is the known
  load-dependent flake (`docs/reviews/router-speed-codex-review.md`, `teacher-te2.md`); nothing on its path changed,
  and it passed alone 3 of 3 times and with its file (17 passed).
- `lint-imports --no-cache`: 42 kept, 0 broken. `ruff check`: all checks passed.
- Vault: `module_validate`, `desktop_validate`, `db_validate_reference` (no errors) and `validate_vault` (2,281 notes)
  pass; the second regeneration is a fixed point.

## Owner's list

None: every step 0 claim held.

## UX list

None: no settings screen or desktop surface loses a backend. The one learner-visible change is the terminal's
`learnloop today` on an install without the extra (an install line in place of a traceback).

## Open items

- `CLAUDE.md`'s `uv sync` line (above), for the orchestrator or owner.
- The landing gate's sync must include `--extra tui`, or the TUI's tests skip silently (as the phone host's do
  without `--extra mobile`).
- The phone host's and desktop's environments are untouched: neither imports the TUI. An existing venv synced
  exactly (`uv sync` without `--inexact` and without `--extra tui`) now removes textual; `learnloop today` there
  prints the install line.

## Unverified

- A real install without textual (a fresh venv from `pip install .`): proved by the import hook instead, as the
  brief asks; the hook makes every `textual` import fail the way a missing package does.
- `pip install 'learnloop[tui]'` from a built wheel: not built; the extra resolves in `uv.lock`.
