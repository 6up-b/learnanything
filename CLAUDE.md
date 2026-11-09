# CLAUDE.md

## Commands

Use `uv` for everything Python.

```bash
uv sync --extra dev --extra mobile       # install; without --extra mobile ~40 phone-host tests skip silently (add --extra pdf for Marker; manim is a core dependency)
uv run pytest                            # full suite, every lane; add -n 8 --dist worksteal to parallelize (pytest-xdist; about 15 min). Times: docs/reviews/test-suite-audit.md
uv run pytest -m "not slow"              # while iterating: leaves out long sims, journeys and renders; the landing gate runs them
uv run pytest -m durability              # production SQLite pragmas + WAL + fresh vaults (or add --durable-sqlite to any selection)
uv run pytest --fresh-connections        # production connection opens and fresh-schema builds in the fast lane
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
LEARNLOOP_VAULT=/abs/path npm run dev    # open a specific vault (default: last-opened, then fixtures-local/*, then a new ~/LearnLoop)
npm run typecheck && npm test && npm run frontend:build   # npm test = vitest
cargo check --manifest-path src-tauri/Cargo.toml
```

Debug env vars: `LEARNLOOP_SIDECAR_LOG_LEVEL=DEBUG`, `LEARNLOOP_SIDECAR_DEBUG_LOG=<file>` (tees sidecar logs; Tauri can swallow stderr), `LEARNLOOP_SIDECAR_TIMEOUT_SECS` (desktop per-request timeout, default 960s), `LEARNLOOP_PYTHON` (pins the sidecar interpreter), `LEARNLOOP_AI_PROVIDER` (overrides serving AI routes, but not the explicit opt-in `embedding`, `field_question_classifier`, or `field_llm_probability` routes).

## Architecture

See `docs/learnloop-architecture-vault/Home.md` for information on architecture, examples of user journeys, and previous design decisions (ADRs in `Decisions/`; ADR-015 WAL + `synchronous=FULL` supersedes ADR-014). Changes to persisted meaning (scoring, scheduling, projections) follow `docs/algorithm-change-playbook.md`; feature specs are in `docs/specs/`.

## Tests

`tests/` is flat (~1,400 `test_*.py` files) with `conftest.py`, `helpers.py`, `structured_ai.py` (`StructuredClientFake` for AI doubles), and `openai_fakes.py` at the root. `helpers.py` has the vault-seeding builders — use them instead of hand-rolling a vault.

`conftest.py` does several things that surprise people. It isolates `LEARNLOOP_CONFIG_DIR` from the developer's real `~/.config/learnloop/`. It monkeypatches `db.connection.connect` and `db.migrate.switch_to_wal` to disable SQLite durability and WAL, and makes `os.fsync` and the target of `db.copies` skip the disk (opt back in with `@pytest.mark.durability` or `--durable-sqlite`, which apply to fixtures of every scope — WAL behaviour is only testable there). `create_basic_vault` copies a per-session template instead of initializing (pass `fresh=True` when a test needs real init/migration; the durability lane also builds fresh), and a process's later fresh schemas are copies of its first real build. A test's `connect()` calls reuse idle connections (`tests/connection_reuse.py`, most of the speed-up from 59 to 15 minutes): a setting, DDL, a replaced file or a patched open path ends the reuse, and `@pytest.mark.fresh_connections` or `--fresh-connections` opens every connection for real. So a background job that used to lose a race with a slow main thread may now win it: a test must wait for the work it reads, not rely on timing. A reader holding a snapshot blocks a background commit in this lane's rollback journal, though not in WAL: a test that needs both at once belongs in the durability lane. Builtin outcome schemas get a fixed id per slug, because the id seeds the certainty bound's draws. Because of the connect patching, prefer `from learnloop.db.connection import connect` at module level in code under test. `--strict-markers` is on: declare new markers in `pyproject.toml`. Mark a test `slow` when it takes more than about 15 s after these shortcuts; the gate still runs it. `tests/cli_surface.json` pins each CLI command's parameter contracts: add nothing for a compatible addition, and edit it only for a deliberate incompatible change (`python tests/test_cli_help_snapshot.py --write`).

Adding a migration: classify each new table in `src/learnloop/db/table_roles.py` (a `DERIVED` table also needs exactly one replayer in `substrate/rebuild_orchestrator.py`; both are tested). Upgrade and rename `fixtures/migration_head_<N>/` (keep it rollback-mode: `PRAGMA journal_mode=DELETE` after migrating) and update its `README.md` and every file naming the old path (`git grep -l migration_head_<N> -- tests scripts docs/learnloop-architecture-vault/_scripts`: 73 files at migration 252, 70 tests plus `scripts/sanitize_migration_head_fixture.py` and the two `docs/learnloop-architecture-vault/_scripts/db_*_reference.py`), then rerun `db_generate_reference.py` and `db_validate_reference.py`.

Since storage S0 (`docs/specs/spec_storage_sync_v1.md` §6.11) the public tip tracks no personal data: the owner's vaults (`linear_algebra`, `probability`, `arxiv_v2`, and the older `arxiv`, `conic-sections`, `law`, `physical_therapy`, `linear_algebra_legacy`) live outside every checkout (`~/learnloop-vaults/<name>`; retired ones in `~/learnloop-retired/`), the textbooks in `~/learnloop-books/`. Never search the filesystem for them. Tests that read them carry the `owner_vaults` marker and are skipped unless `LEARNLOOP_OWNER_VAULTS=<dir>` names backup-API copies under their old fixture names (`tests/owner_vaults.py`; make the copies with `learnloop.db.copies.copy_tree_with_databases` under gitignored `fixtures-local/`; never point it at a live vault); fixture walkers walk only what git tracks. The only tracked databases are `fixtures/migration_head_<N>/state.sqlite` (sanitized, with a project-authored transcript and answers by `scripts/sanitize_migration_head_fixture.py`; rebuild it from the tracked copy so the sanitized text carries over) and the synthetic `fixtures/mvp017_route_check_replay/state.sqlite`, both in rollback mode. `tests/test_public_tip_guards.py` (G8) fails on any other tracked database, a PDF/EPUB/DjVu/audio/video file outside `samples/` (each needs a `samples/NOTICE` entry), another binary outside `docs/` images and `apps/` assets, a file over 5 MB, a `canonical-sources/` file outside those two fixtures, or a git-LFS rule; a screenshot showing a book page goes on `docs/screenshots/BOOK_PAGES.md`. A commit that untracks paths deletes their clean copies in any checkout updated to it: the owner lands such commits (S0's own through `scripts/s0_landing.py`, which refuses until the data is copied out), never an agent. Empty `-wal`/`-shm` beside a fixture are harmless; a non-empty `-wal` fails `test_tracked_fixture_databases.py` (checkpoint it, never delete it), and conftest fails the run if a test changed a tracked fixture's or an owner-lane copy's journal header or left WAL frames. Copy databases with `learnloop.db.copies` (backup API); a new `shutil` copy call fails `test_sqlite_file_copies.py` until audited there.
