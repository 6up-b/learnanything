# FG1d: Codex review record (`followup/fg1d-facet-shadow`, reviewed `90a2f430c9..2dfce87e8e`)

Codex (gpt-6.1-sol, job `20261104-210234-FkuXk8`) reviewed the branch statically and found no actionable defect. Its sandbox could
not reach the user systemd bus, so it ran no tests; the gate below runs them. It found one false claim in the implementer review and
listed every spec requirement as conforming (probe evidence immediate, no model or embedding call on replay, generated probes single
use, marks causes/ordering/holds kept, no successor or new admission rule, no schema change, no new grader input or outbound text, no
paid operation).

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| C1 | Low (doc) | `followup-fg1d.md` "Which side is wrong" answers "Replay", the reverse of what the section and the fix say | fixed | this commit | Doc only, not testable: the sentence after it already said the live write was the stale cache, and fix 1 (`70ac1b9f38`) makes live follow replay. Now reads "Live; replay is the reference." |
| C2 | Info | Fix 1's extra whole-ledger fold not timed on a large ledger | not a defect | none | Codex lists it as a measurement gap with no concrete failure; already in `followup-fg1d.md` "Open items". No owner-sized ledger may be opened in this stage (synthetic vaults only). |

No High or Medium finding; no code change.

## Gate (fix step; the full suite runs once at the landing)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install --offline pypdfium2==5.14.0` | done |
| `lint-imports --no-cache` (under `env -i`, empty `HOME`, `CODEX_HOME`, `LEARNLOOP_CONFIG_DIR`), frozen-cycles contract included | 43 kept, 0 broken |
| `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6`: `tests/test_followup_fg1d_probe_shadow.py`, `tests/test_followup_fg1d_panel_read.py`, label audit `tests/test_measurement_state_labels.py`, `tests/test_cli_help_snapshot.py`, process-launch list `tests/test_codex_lockdown_round3.py`, `tests/test_architecture.py`, `tests/test_public_tip_guards.py` | 77 passed (1:13) |

Only docs changed in this step, so the implementation step's 81-file targeted list (`followup-fg1d.targeted-tests.txt`, 1984 passed,
6 skipped, 4 xfailed) stands for the code; it was not rerun. No migration, schema, frontend or `src-tauri` change: no durability lane,
npm, vitest, cargo or DB-reference step applies. No model call, no paid command, no vault opened.
