# CLAUDE.md

## Commands

Use `uv` for everything Python.

```bash
uv sync --extra dev                      # install (add --extra pdf for Marker; manim is a core dependency)
uv run pytest                            # full suite (~17 min)
uv run pytest -m durability              # production SQLite pragmas + fresh vaults (or add --durable-sqlite to any selection)
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
npm run typecheck && npm test && npm run frontend:build   # npm test = vitest
cargo check --manifest-path src-tauri/Cargo.toml
```

Debug env vars: `LEARNLOOP_SIDECAR_LOG_LEVEL=DEBUG`, `LEARNLOOP_SIDECAR_TIMEOUT_SECS` (default 240s; raise for long model calls), `LEARNLOOP_PYTHON` (pins the sidecar interpreter).

## Architecture

See `docs/learnloop-architecture-vault/Home.md` for information on architecture, examples of user journeys, and previous design decisions. 

## Tests

`tests/` is flat (~440 `test_*.py` files) with `conftest.py`, `helpers.py`, and `openai_fakes.py` at the root. `helpers.py` has the vault-seeding builders — use them instead of hand-rolling a vault.

`conftest.py` does three things that surprise people: it isolates `LEARNLOOP_CONFIG_DIR` from the developer's real `~/.config/learnloop/`; it monkeypatches `db.connection.connect` to disable SQLite durability (opt back in with `@pytest.mark.durability` or `--durable-sqlite`, which apply to fixtures of every scope); and `create_basic_vault` copies a per-session template instead of initializing (pass `fresh=True` when a test needs real init/migration; the durability lane also builds fresh). Because of the connect patching, prefer `from learnloop.db.connection import connect` at module level in code under test. `--strict-markers` is on: declare new markers in `pyproject.toml`.

Adding a migration: upgrade and rename `fixtures/migration_head_<N>/` and update its 5 hard-coded references (3 tests, 2 `docs/learnloop-architecture-vault/_scripts/db_*_reference.py`).

Fixture vaults under `fixtures/*/` contain tracked `state.sqlite` files — they show up dirty in `git status` after running the app against them.
