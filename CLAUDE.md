# CLAUDE.md

## Commands

Use `uv` for everything Python.

```bash
uv sync --extra dev                      # install (add --extra pdf for Marker; manim is a core dependency)
uv run pytest                            # full suite, serial (~17 min); add -n auto to parallelize (pytest-xdist)
uv run pytest -m durability              # production SQLite pragmas + WAL + fresh vaults (or add --durable-sqlite to any selection)
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
LEARNLOOP_VAULT=/abs/path npm run dev    # open a specific vault (default: last-opened, then fixtures-local/*, then tracked fixtures/linear_algebra)
npm run typecheck && npm test && npm run frontend:build   # npm test = vitest
cargo check --manifest-path src-tauri/Cargo.toml
```

Debug env vars: `LEARNLOOP_SIDECAR_LOG_LEVEL=DEBUG`, `LEARNLOOP_SIDECAR_DEBUG_LOG=<file>` (tees sidecar logs; Tauri can swallow stderr), `LEARNLOOP_SIDECAR_TIMEOUT_SECS` (desktop per-request timeout, default 960s), `LEARNLOOP_PYTHON` (pins the sidecar interpreter), `LEARNLOOP_AI_PROVIDER` (overrides serving AI routes, but not the explicit opt-in `embedding`, `field_question_classifier`, or `field_llm_probability` routes).

## Architecture

See `docs/learnloop-architecture-vault/Home.md` for information on architecture, examples of user journeys, and previous design decisions (ADRs in `Decisions/`; ADR-015 WAL + `synchronous=FULL` supersedes ADR-014). Changes to persisted meaning (scoring, scheduling, projections) follow `docs/algorithm-change-playbook.md`; feature specs are in `docs/specs/`.

## Tests

`tests/` is flat (~450 `test_*.py` files) with `conftest.py`, `helpers.py`, `structured_ai.py` (`StructuredClientFake` for AI doubles), and `openai_fakes.py` at the root. `helpers.py` has the vault-seeding builders — use them instead of hand-rolling a vault.

`conftest.py` does three things that surprise people: it isolates `LEARNLOOP_CONFIG_DIR` from the developer's real `~/.config/learnloop/`; it monkeypatches `db.connection.connect` and `db.migrate.switch_to_wal` to disable SQLite durability and WAL (opt back in with `@pytest.mark.durability` or `--durable-sqlite`, which apply to fixtures of every scope — WAL behaviour is only testable there); and `create_basic_vault` copies a per-session template instead of initializing (pass `fresh=True` when a test needs real init/migration; the durability lane also builds fresh). Because of the connect patching, prefer `from learnloop.db.connection import connect` at module level in code under test. `--strict-markers` is on: declare new markers in `pyproject.toml`.

Adding a migration: classify each new table in `src/learnloop/db/table_roles.py` (a `DERIVED` table also needs exactly one replayer in `substrate/rebuild_orchestrator.py`; both are tested). Upgrade and rename `fixtures/migration_head_<N>/` (keep it rollback-mode: `PRAGMA journal_mode=DELETE` after migrating) and update its `README.md` and 5 hard-coded paths (3 tests, 2 `docs/learnloop-architecture-vault/_scripts/db_*_reference.py`; `db_generate_reference.py` names it 3 times), then rerun `db_generate_reference.py` and `db_validate_reference.py`.

Fixture vaults under `fixtures/*/` contain tracked `state.sqlite` files — they show up dirty in `git status` after running the app against them. `linear_algebra`, `probability`, and `arxiv_v2` are also the owner's working vaults: don't commit, revert, or stash their changes; use a copy in gitignored `fixtures-local/`. Empty `-wal`/`-shm` beside a fixture are harmless; a non-empty `-wal` fails `test_tracked_fixture_databases.py` (checkpoint it, never delete it), and conftest fails the run if a test changed a fixture's journal header or left WAL frames. Copy databases with `learnloop.db.copies` (backup API); a new `shutil` copy call fails `test_sqlite_file_copies.py` until audited there.
