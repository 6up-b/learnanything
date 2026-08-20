# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Use `uv` for everything Python — never bare `python`, `pip`, or `pytest`.

```bash
uv sync --extra dev                      # install (add --extra pdf for Marker, --extra animation for Manim)
uv run pytest                            # full suite (~10 min)
uv run pytest tests/test_scheduler.py::test_name -x   # single test
uv run lint-imports --no-cache           # architectural dependency contracts
uv run learnloop --help                  # CLI; most subcommands take --vault and --json
uv run learnloop doctor --fix-state --vault <path>    # after manual vault edits
uv run learnloop config effective --vault <path>      # normalized effective config
uv run learnloop rebuild --shadow --json --vault <path> # isolated replay diff
uv run python -m learnloop_sidecar       # sidecar directly (JSON-RPC over stdio)
```

Desktop app (from `apps/learnloop-tauri/`):

```bash
npm install && npm run dev               # Tauri shell spawns the Python sidecar itself
LEARNLOOP_VAULT=/abs/path npm run dev    # open a specific vault
npm run typecheck && npm run frontend:build
cargo check --manifest-path src-tauri/Cargo.toml
```

Debug env vars: `LEARNLOOP_SIDECAR_LOG_LEVEL=DEBUG`, `LEARNLOOP_SIDECAR_TIMEOUT_SECS` (default 240s; raise for long model calls), `LEARNLOOP_PYTHON` (pins the sidecar interpreter).

## Architecture

Four layers, top to bottom. A user-visible feature usually touches all four:

1. `apps/learnloop-tauri/src/` — React/TS. `api/client.ts` wraps `invoke()`, `api/dto.ts` holds hand-written types mirroring sidecar JSON (camelCase). Screens in `src/screens/`.
2. `apps/learnloop-tauri/src-tauri/src/` — Rust shell. `commands.rs` `#[tauri::command]` fns are thin passthroughs via `blocking_sidecar_call(method, params)`; each must also be listed in `main.rs`'s `generate_handler![]`. `sidecar.rs` spawns/manages the Python process.
3. `src/learnloop_sidecar/` — JSON-RPC bridge. Handlers register with `@method("name", ParamsModel)` (see `registry.py`); every module must be imported in `handlers/__init__.py` or the method won't exist. Handlers validate params, call public domain APIs, and serialize — no domain logic. Raise `SidecarError` for stable, user-facing error codes; anything else becomes an opaque `internal`.
4. `src/learnloop/` — domain packages are explicit: `attempts/`, `learner/`,
   `scheduling/`, `goals/`, `diagnosis/`, `curriculum/`, `substrate/`,
   `content/`, `reader/`, `tutor/`, `ops/`, and `params/`. Infrastructure lives
   in `db/`, `vault/`, `ingest/`, `config/`, and provider-neutral `ai/`.
   `cli/` is a Typer adapter peer to the sidecar, not a wrapper around it. See
   `ARCHITECTURE.md` for the package map and enforced dependency rules.

The TUI (`src/learnloop/tui/`) is an active Textual frontend exercised by tests.

## Vault model

A vault is a directory with two sources of truth that must stay consistent:

- **Markdown/YAML** (`concepts/`, `subjects/`, `profile/`, `errors/`, `facets.yaml`, `canonical-sources/`) — human-editable learning content. Access paths through `vault/paths.py:VaultPaths`, never by string concatenation.
- **`state.sqlite`** — attempts, events, scheduling, jobs, and *derived* state. Derived state is rebuildable: raw attempts are retained so `learnloop rebuild-derived-state` can replay them after an algorithm change.

Schema changes go in `migrations/NNN_name.sql`, applied in numeric order and recorded in `schema_migrations`. **Always `ls migrations/` for the next free number** — numbering has gaps and parallel worktrees have collided here.

## Conventions that matter

- **Determinism.** Domain operations take an injectable `Clock` (`learnloop/clock.py`); tests use `FrozenClock`. Don't call `datetime.now()` in domain code. Timestamps are ISO-8601 UTC strings with `Z`.
- **`algorithm_version`** (`config/schema.py`, currently `mvp-0.9`) tags derived rows. Changing scoring/scheduling behavior means bumping it and making the change replayable; follow `docs/algorithm-change-playbook.md`.
- **Evidence, not mastery.** The learner model deliberately keeps predicted ability, demonstrated evidence, claims, and readiness as separate quantities. Don't collapse them into one score, and don't present prediction as certification.
- **Provenance.** Generated content carries source spans end to end; anything AI-authored that needs review lands in proposals or a maintenance queue rather than being applied silently.
- **AI is optional and routed.** Per-workflow provider routing lives in the vault's `learnloop.toml` `[ai.routing]`. Scheduling, replay, and storage must work with no provider configured (`manual` grading).

## Tests

`tests/` is flat (~378 files) with `conftest.py`, `helpers.py`, and `openai_fakes.py` at the root. `helpers.py` has the vault-seeding builders — use them instead of hand-rolling a vault.

`conftest.py` does two things that surprise people: it isolates `LEARNLOOP_CONFIG_DIR` from the developer's real `~/.config/learnloop/`, and it monkeypatches `db.connection.connect` to disable SQLite durability (the suite is minutes vs. hours otherwise). Because of that patching, prefer `from learnloop.db.connection import connect` at module level in code under test.

Fixture vaults in `fixtures/linear_algebra/` and `fixtures/arxiv/` contain tracked `state.sqlite` files — they show up dirty in `git status` after running the app against them.
