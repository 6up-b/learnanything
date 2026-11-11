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
