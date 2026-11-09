from __future__ import annotations

import atexit
import hashlib
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path
import pytest

# Fails a test that leaves a thread running (tests/thread_guard.py).
pytest_plugins = ["tests.thread_guard"]

# Small matrices gain nothing from OpenBLAS threads, and under xdist each worker's pool competes with the others
# (the AD sims used 20% more CPU with them). Set before anything imports numpy.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

# Keep the 4,000+ fixture vaults off the capacity-constrained system temp
# volume. PYTEST_DEBUG_TEMPROOT controls pytest's numbered tmp_path roots when
# --basetemp is not supplied, while still allowing CI to override it.
_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".pytest_tmp"
_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_TEMP_ROOT))

# Isolate tests from machine-global learnloop settings. Point LEARNLOOP_CONFIG_DIR
# at an empty dir (so a developer's real ~/.config/learnloop/settings.env is not
# read) and clear LEARNLOOP_CODEX_CHECKOUT_PATH, so per-test fixtures that inject
# a temp Codex checkout/revision are not overridden by the ambient environment.
os.environ["LEARNLOOP_CONFIG_DIR"] = str(_TEMP_ROOT / "global_settings_isolated")
os.environ.pop("LEARNLOOP_CODEX_CHECKOUT_PATH", None)
# The ChatGPT-plan sign-in store lives under LEARNLOOP_CONFIG_DIR (isolated
# above); forcing its file backend keeps every test away from an OS keyring.
os.environ["LEARNLOOP_CHATGPT_SECRET_STORE"] = "file"
# Tier 1 (mvp-0.22, the template's version) asks the Decider by default, on the
# code-default openrouter_decider profile's key: never a real key in a test, so
# an unfaked Decider is unavailable and its LLM fallback runs (a test that
# exercises the Decider injects a fake client).
for _decider_key in ("OPENROUTER_API_KEY", "PERPLEXITY_API_KEY"):
    os.environ.pop(_decider_key, None)
# Router R2b (mvp-0.24, the template's version): Today's block choice asks the
# router's models through their routes. No test reaches a real model: the
# routes are "off" (the staged rule chooses, as with no model set up), and a
# test of the mixture injects fake models into its own runtime.
os.environ["LEARNLOOP_ROUTER_MODELS"] = "off"
# Adaptive hints H1: a session serve starts an approach-map build in the
# background (hints.maps.build_on_serve, on by default). No test reaches a
# real model: with this set, a serve starts no build unless the test injected
# a fake client (ctx.approach_map_client or the builder's client argument).
os.environ["LEARNLOOP_APPROACH_MAP_BUILDS"] = "off"
# Adaptive hints H2a: practice.request_hint asks the hint chooser (a Decider)
# and the hint writer. No test reaches a real model: with this set, neither
# route resolves a client unless the test injected a fake
# (ctx.hint_writer_client / ctx.hint_chooser_client, or the service's
# writer_client / chooser_client_factory arguments).
os.environ["LEARNLOOP_HINT_MODELS"] = "off"
# Adaptive difficulty AD1: a plan serve and a plan build schedule the outside
# forecasters and the feature audit in the background (on by default). No
# test reaches a real model: with this set, no AD job resolves a client unless
# the test injected a fake (ctx.ad_clients, or the job's own client arguments).
os.environ["LEARNLOOP_AD_MODELS"] = "off"
# Reader workbench RW2b: no workbench route ("Check my work") resolves a real
# client unless the test injected a fake (ctx.workbench_check_client).
os.environ["LEARNLOOP_WORKBENCH_MODELS"] = "off"
# Reader workbench RW3b: the cue judge (background discovery when a source
# opens) resolves no real client unless the test injected a fake
# (ctx.cue_judge_client, or discover()'s client argument).
os.environ["LEARNLOOP_CUE_JUDGE_MODELS"] = "off"
# Reader workbench RW4e: the batch role labeller (`learnloop reader label-roles`)
# resolves no real client unless the test injected a fake (label_roles' client).
os.environ["LEARNLOOP_ROLE_LABELLER_MODELS"] = "off"
# Reader workbench RW7a: the reading-path judge resolves no real client unless
# the test injected a fake (ctx.reading_path_judge_client, or judge()'s client).
os.environ["LEARNLOOP_READING_PATH_MODELS"] = "off"
# Deliverable curriculum C0a: the section coverage judge resolves no real
# client unless the test injected a fake (ctx.coverage_judge_client, or
# judge()'s client).
os.environ["LEARNLOOP_COVERAGE_MODELS"] = "off"
# Deliverable curriculum C0b: neither the scope resolver nor the deliverable
# path judge resolves a real client unless the test injected a fake
# (ctx.deliverable_scope_client / ctx.deliverable_path_client, or the client argument).
os.environ["LEARNLOOP_CURRICULUM_MODELS"] = "off"
# Deliverable curriculum C2: the note link judge resolves no real client
# unless a fake is injected (ctx.note_link_client, or the client argument).
# (C2b: the notes are the vault's own; no external notes tool exists.)
os.environ["LEARNLOOP_NOTE_LINK_MODELS"] = "off"
# Reader workbench RW5a: no figure route (figure_author) resolves a real
# client unless the test injected a fake (ctx.figure_author_client, or the
# service's author_client argument).
os.environ["LEARNLOOP_FIGURE_MODELS"] = "off"
# Reader workbench RW6b part 2: the session narrative (reader_digest) resolves no
# real client unless the test injected a fake (the client argument, or
# ctx.reader_digest_client).
os.environ["LEARNLOOP_DIGEST_MODELS"] = "off"
# Local retrieval P2: no query-student generator model is reached and no query
# process is started unless the test injected a fake (a client, or a spawn).
os.environ["LEARNLOOP_QUERY_STUDENT_MODELS"] = "off"
# Reader RW5d P5: figures ahead of need (figures.prefetch_enabled, on by
# default) queue a background pass from the plan, reading progress, the
# tutor's offers, lessons and the gap worker. No test starts one by accident:
# with this set, a hook queues nothing unless the test injected the runtime's
# seams (ctx.figure_prefetch_inline, with its fake judge and readers).
os.environ["LEARNLOOP_FIGURE_PREFETCH"] = "off"

# Disable sqlite durability for every test connection. Each durable commit
# pays a journal write plus an fsync, and on Windows on-access antivirus
# scanning amplifies every one of those file operations (measured: a fresh
# 100+-migration vault took ~17.5s with default pragmas vs ~0.3s with these —
# the difference between a suite that runs in minutes on Linux and a multi-hour
# one on Windows). Tests are deterministic and their databases disposable, so
# crash durability buys nothing here. Patch the shared connect() at the source
# AND rebind any already-imported `from ... import connect` aliases so every
# module sees the fast version.
#
# The fast lane also skips the migration's one-way switch to WAL, so its
# databases keep a rollback header and the in-memory journal applies. The
# durability lane (`durability` marker or --durable-sqlite) runs the production
# path: the switch to WAL and synchronous=FULL.
import sqlite3  # noqa: E402

import learnloop.db.connection as _db_connection  # noqa: E402
import learnloop.db.copies as _db_copies  # noqa: E402
import learnloop.db.migrate as _db_migrate  # noqa: E402

_durable_connect = _db_connection.connect
_production_switch_to_wal = _db_migrate.switch_to_wal
_durability_active = False


def _fast_test_connect(sqlite_path, *, read_only=False):
    connection = _durable_connect(sqlite_path, read_only=read_only)
    if not read_only and not _durability_active:
        # A pooled connection (router speed stage 2's landing ruling R4: a PRAGMA with an argument run during a
        # checkout closes it at release) takes the lane's settings once, as part of its open, unwatched.
        raw = getattr(connection, "_connection", None)
        pooled = isinstance(raw, _db_connection._PooledSqlite)
        if pooled and getattr(raw, "_fast_lane", False):
            return connection
        if pooled:
            raw.unwatch()
        connection.execute("PRAGMA synchronous=OFF")
        # A WAL database built by a durability-lane fixture stays WAL: leaving
        # WAL needs exclusive access and would silently fail while another
        # connection is open, making the mode depend on test order.
        if connection.execute("PRAGMA journal_mode").fetchone()[0] != "wal":
            connection.execute("PRAGMA journal_mode=MEMORY")
        if pooled:
            raw._fast_lane = True
            raw.watch()
    return connection


def _lane_switch_to_wal(connection, sqlite_path):
    if _durability_active:
        return _production_switch_to_wal(connection, sqlite_path)
    return "fast test lane keeps the in-memory journal"


# An explicit fsync pays what `PRAGMA synchronous=OFF` already stopped paying (about 12 ms on the btrfs test volume).
# A test that spies on or fails os.fsync replaces this attribute as it did the real one.
_real_fsync = os.fsync


def _lane_fsync(fd):
    if _durability_active:
        return _real_fsync(fd)
    os.fstat(fd)  # a bad descriptor still raises, as fsync would


os.fsync = _lane_fsync


# db.copies writes each copy on a plain sqlite3 connection, outside connect(): the connect patch does not reach it, so
# in the fast lane every test's vault copy paid full fsyncs (about 90 ms against 3 ms on btrfs). The durability lane
# keeps the production copy path.
class _CopiesSqlite3:
    def __getattr__(self, name):
        return getattr(sqlite3, name)

    @staticmethod
    def connect(*args, **kwargs):
        connection = sqlite3.connect(*args, **kwargs)
        if not _durability_active:
            connection.execute("PRAGMA synchronous=OFF")
        return connection


_db_copies.sqlite3 = _CopiesSqlite3()

# A brand-new database costs 0.8 s (every migration's script) and about one test in twelve builds one. The first build
# of each migration list in a process is the real one, and later ones in the fast lane copy it with this call's
# applied_at. Durability-lane and `fresh_connections` tests always run the real path.
_production_apply_fresh = _db_migrate._apply_fresh
_built_schemas: dict[tuple, Path] = {}
_real_open_paths = False


def _lane_apply_fresh(sqlite_path, migrations, clock):
    if _durability_active or _real_open_paths:
        return _production_apply_fresh(sqlite_path, migrations, clock)
    key = tuple((migration.version, migration.name, str(migration.path)) for migration in migrations)
    built = _built_schemas.get(key)
    if built is None:
        applied = _production_apply_fresh(sqlite_path, migrations, clock)
        cache = Path(tempfile.mkdtemp(prefix="fresh-schema-", dir=_TEMP_ROOT)) / "schema.sqlite"
        owner = os.getpid()  # a forked child that exits normally must not delete its parent's copy
        atexit.register(lambda: os.getpid() == owner and shutil.rmtree(cache.parent, ignore_errors=True))
        _db_copies.backup_database(sqlite_path, cache)
        _built_schemas[key] = cache
        return applied
    tmp_path = sqlite_path.with_name(sqlite_path.name + ".tmp")
    _db_migrate._remove_companion_files(tmp_path, include_database=True)
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    _db_copies.backup_database(built, tmp_path)
    with sqlite3.connect(tmp_path) as connection:
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("UPDATE schema_migrations SET applied_at = ?", (_db_migrate.utc_now_iso(clock),))
    connection.close()
    _db_migrate._remove_companion_files(sqlite_path, include_database=False)
    tmp_path.replace(sqlite_path)
    return list(migrations)


_db_migrate._apply_fresh = _lane_apply_fresh
_db_connection.connect = _fast_test_connect
_db_migrate.switch_to_wal = _lane_switch_to_wal
for _module in list(sys.modules.values()):
    if getattr(_module, "__name__", "").startswith("learnloop") and getattr(_module, "connect", None) is _durable_connect:
        _module.connect = _fast_test_connect


# A vault mints its builtin outcome schemas' ids at random, those ids are in the calibration model's content hash, and
# that hash seeds the certainty bound's draws. So a test's effective mass depended on the run: about 1 vault in 600 got a
# bound below its certainty, and a dont_know read 0.690 instead of 0.7 (see docs/reviews/test-suite-audit.md). Production's
# ensure_outcome_schema runs here unchanged, its real insert included; only the one id it mints is fixed, per slug, so
# every test's draws are the same on every run. tests/test_outcome_schema_ids.py pins the real random id and the bound's
# limits over many seeds. In production a vault's id, and so its draws, are fixed once minted.
from learnloop.db import repositories as _repositories  # noqa: E402

_production_ensure_outcome_schema = _repositories.Repository.ensure_outcome_schema
_production_new_ulid = _repositories.new_ulid
_minting_schema = threading.local()


def _schema_id_for(slug: str) -> str:
    digest = hashlib.sha256(slug.encode("utf-8")).hexdigest().upper()
    return ("01SCHEMA" + digest.translate(str.maketrans("", "", "ILOU")))[:26]


def _new_ulid_or_fixed_schema_id():
    slug = getattr(_minting_schema, "slug", None)
    return _production_new_ulid() if slug is None else _schema_id_for(slug)


def _ensure_outcome_schema_fixed_id(self, *, slug, kind, clock=None):
    _minting_schema.slug = slug
    try:
        return _production_ensure_outcome_schema(self, slug=slug, kind=kind, clock=clock)
    finally:
        _minting_schema.slug = None


_repositories.new_ulid = _new_ulid_or_fixed_schema_id
_repositories.Repository.ensure_outcome_schema = _ensure_outcome_schema_fixed_id


# Two pure functions that cost 26% of a sample's time after the connection work, and repeat their inputs across tests.
# Both remember only exact results of the real function, and the real function runs on every new input.
#
# yaml_io._dumped dumps and then re-parses (pure Python, 9 ms). Only plain data is remembered, keyed by its repr: a
# round-trip CommentedMap carries comments its repr doesn't show, so it always runs for real. Failures aren't remembered.
import copy  # noqa: E402

import pydantic  # noqa: E402

from learnloop.vault import yaml_io as _yaml_io  # noqa: E402

_production_dumped = _yaml_io._dumped
_dumped_texts: dict[str, str] = {}


def _is_plain(value, seen: set[int] | None = None) -> bool:
    """Exact scalars, dicts and lists in which no container appears twice: YAML writes a repeated container as an anchor
    and an alias, which a repr can't show, and a cycle has no repr to key on."""

    kind = type(value)
    if kind is dict or kind is list:
        seen = set() if seen is None else seen
        if id(value) in seen:
            return False
        seen.add(id(value))
        if kind is dict:
            return all(type(key) is str and _is_plain(item, seen) for key, item in value.items())
        return all(_is_plain(item, seen) for item in value)
    return kind in (str, int, float, bool) or value is None


def _remembered_dumped(data):
    if not _is_plain(data):
        return _production_dumped(data)
    key = repr(data)
    text = _dumped_texts.get(key)
    if text is None:
        text = _dumped_texts[key] = _production_dumped(data)
    return text


_yaml_io._dumped = _remembered_dumped

# pydantic generates a model's JSON schema afresh on each call (8 ms), once or more per faked model request. The result
# depends on the class, the arguments, its core schema (a rebuild replaces it) and the model_config of every model in that
# schema (read when generating, not when building), so all of them are the key. Each caller gets its own copy.
_production_json_schema = pydantic.BaseModel.model_json_schema.__func__
_json_schemas: dict[tuple, dict] = {}
_models_in_core_schema: dict[int, tuple[object, tuple[type, ...]]] = {}


def _models_in(core_schema) -> tuple[type, ...]:
    known = _models_in_core_schema.get(id(core_schema))
    if known is not None:
        return known[1]
    models, seen, pending = set(), set(), [core_schema]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            if id(node) not in seen:
                seen.add(id(node))
                if node.get("type") == "model" and "cls" in node:
                    models.add(node["cls"])
                pending.extend(node.values())
        elif isinstance(node, (list, tuple)):
            pending.extend(node)
    ordered = tuple(sorted(models, key=lambda model: f"{model.__module__}.{model.__qualname__}"))
    _models_in_core_schema[id(core_schema)] = (core_schema, ordered)  # holds the schema, so its id stays its own
    return ordered


def _remembered_json_schema(cls, *args, **kwargs):
    core_schema = cls.__dict__.get("__pydantic_core_schema__")
    if not isinstance(core_schema, dict):  # not built: its own error, or its own rebuild, belongs to the real call
        return _production_json_schema(cls, *args, **kwargs)
    try:
        key = (cls, id(core_schema), tuple(repr(model.model_config) for model in _models_in(core_schema)), args,
               tuple(sorted(kwargs.items())))
        hash(key)
    except TypeError:
        return _production_json_schema(cls, *args, **kwargs)
    schema = _json_schemas.get(key)
    if schema is None:
        schema = _json_schemas[key] = _production_json_schema(cls, *args, **kwargs)
    return copy.deepcopy(schema)


pydantic.BaseModel.model_json_schema = classmethod(_remembered_json_schema)


# Background owners (sidecar contexts, ingest hosts, post-attempt workers,
# exam graders) that test code constructs are closed when the test ends
# (tests/background_owners.py); production-built ones stay their owner's.
from tests import background_owners as _background_owners  # noqa: E402

_background_owners.install()


@pytest.fixture(autouse=True)
def close_test_background_owners():
    start = _background_owners.mark()
    yield
    _background_owners.close_since(start)


def pytest_addoption(parser):
    parser.addoption("--durable-sqlite", action="store_true", help="Use production SQLite durability for every selected test.")
    parser.addoption("--fresh-connections", action="store_true", help="Open every SQLite connection for real instead of reusing idle ones in the fast lane (tests/connection_reuse.py).")


# The SQLite mode is switched in runtest hooks rather than in a fixture because
# pytest builds module- and session-scoped fixtures before any function-scoped
# autouse fixture runs; a fixture-based switch would leave shared fixtures in
# the fast lane. The mode active when a shared fixture is first built is the
# one it keeps, so a module fixture used by both `durability` tests and plain
# tests runs in whichever lane its first consumer selected.
_session_durable = False


def _set_sqlite_test_mode(*, durable: bool) -> None:
    from tests import helpers

    global _durability_active
    _durability_active = durable
    # Durability tests also exercise real vault construction, not a copy.
    helpers._FRESH_VAULTS = durable


# Tracked fixture databases must never be opened writable in place: that
# would switch their header to WAL and leave -wal/-shm files in the working
# tree. The state is recorded at start and compared when the session ends, so
# the check covers every test that ran, whatever its order.
_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
_fixture_state_at_start: dict[str, tuple[str, tuple[str, ...]]] = {}


def _fixture_database_state() -> dict[str, tuple[str, tuple[str, ...]]]:
    from learnloop.db.copies import COMPANION_SUFFIXES
    from learnloop.db.storage import header_journal_mode

    from tests.owner_vaults import owner_vaults_root, tracked_fixture_files

    # The repository side is what git tracks under fixtures/ (Codex review of
    # S0, F6): an untracked vault left there is not the tip's, and another
    # process may be using it. The owner lane's copies are guarded like
    # tracked fixtures, through the lane's own root only: a test must copy
    # them before opening one writable.
    roots = [("", _FIXTURES, tracked_fixture_files("*.sqlite"))]
    owner_root = owner_vaults_root()
    if owner_root is not None and owner_root.is_dir():
        roots.append(("owner:", owner_root, sorted(owner_root.rglob("*.sqlite"))))
    # A read-only open of a WAL database creates an empty -wal and a -shm, so
    # companion presence alone is not a change; only the header mode and
    # un-checkpointed WAL frames are.
    state = {}
    for prefix, root, databases in roots:
        for database in databases:
            pending = tuple(
                database.name + suffix
                for suffix in COMPANION_SUFFIXES
                if database.with_name(database.name + suffix).exists()
                and database.with_name(database.name + suffix).stat().st_size > 0
                and suffix != "-shm"
            )
            state[prefix + str(database.relative_to(root))] = (header_journal_mode(database), pending)
    return state


def pytest_configure(config):
    global _session_durable
    _session_durable = bool(config.getoption("--durable-sqlite"))
    _set_sqlite_test_mode(durable=_session_durable)
    _fixture_state_at_start.update(_fixture_database_state())


def pytest_sessionfinish(session, exitstatus):
    current = _fixture_database_state()
    changed = {
        name: (_fixture_state_at_start.get(name), current.get(name))
        for name in sorted(set(_fixture_state_at_start) | set(current))
        if _fixture_state_at_start.get(name) != current.get(name)
    }
    if not changed:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    message = (
        "tracked fixture databases changed during the test run (journal mode or un-checkpointed WAL frames); "
        f"a test opened one writable in place instead of copying it first: {changed}"
    )
    if reporter is not None:
        reporter.write_line(f"ERROR: {message}", red=True)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_collection_modifyitems(config, items):
    """Skip the ``owner_vaults`` lane unless ``LEARNLOOP_OWNER_VAULTS`` names its copies."""
    from tests.owner_vaults import OWNER_VAULTS_ENV, OWNER_VAULTS_SKIP_REASON, owner_vaults_root

    root = owner_vaults_root()
    if root is not None and root.is_dir():
        return
    reason = OWNER_VAULTS_SKIP_REASON if root is None else f"{OWNER_VAULTS_ENV}={root} is not a directory"
    skip = pytest.mark.skip(reason=reason)
    for item in items:
        if item.get_closest_marker("owner_vaults") is not None:
            item.add_marker(skip)


# The fast lane's connection reuse spans a test's setup, call and teardown (tests/connection_reuse.py).
@pytest.hookimpl(wrapper=True)
def pytest_runtest_protocol(item, nextitem):
    from tests.connection_reuse import TestLanePool

    fresh = (
        _session_durable
        or item.config.getoption("--fresh-connections")
        or any(item.get_closest_marker(name) is not None for name in ("durability", "owner_vaults", "fresh_connections"))
    )
    global _real_open_paths
    _real_open_paths = fresh
    if fresh:
        return (yield)
    pool = TestLanePool()
    token = _db_connection._REUSED.set(pool)
    try:
        return (yield)
    finally:
        _db_connection._REUSED.reset(token)
        pool.close()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    durable = _session_durable or item.get_closest_marker("durability") is not None
    _set_sqlite_test_mode(durable=durable)
    # The Codex launch check is cached per process and config fingerprint;
    # a test's fakes (a stubbed probe, a fake CLI) must never see another
    # test's cached verdict.
    from learnloop.ai.providers.codex_lockdown import clear_check_cache

    clear_check_cache()


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    _set_sqlite_test_mode(durable=_session_durable)


@pytest.fixture
def legacy_codex_http_double(monkeypatch):
    """Let a test use the legacy Codex HTTP adapter as an in-process provider double.

    The tool lockdown refuses that transport at every entry (hardening round
    2, H3: ``codex_lockdown.refuse_legacy_http_transport``). End-to-end CLI,
    sidecar and TUI tests drive a fake in-process HTTP server through it as a
    stand-in model; they request this fixture by name or with
    ``pytestmark = pytest.mark.usefixtures("legacy_codex_http_double")``. No
    configuration, environment variable or flag can do this outside tests."""

    from learnloop.ai.providers import codex_lockdown

    monkeypatch.setattr(codex_lockdown, "refuse_legacy_http_transport", lambda where: None)


@pytest.fixture
def migration_upgrade_allowed():
    """The test suite's named allowance to upgrade an existing database
    (``db.migrate.UPGRADE_TEST_HELPER``; F8 of the coordinated-migration
    verify). Outside the migration coordinator, ``apply_migrations`` refuses to
    upgrade a database with migrations pending; a test that builds an older
    database and upgrades it directly requests this fixture (by name, or with
    ``pytestmark = pytest.mark.usefixtures("migration_upgrade_allowed")``)."""

    from learnloop.db.migrate import UPGRADE_TEST_HELPER, upgrade_allowance

    with upgrade_allowance(UPGRADE_TEST_HELPER):
        yield


def _selected_sources(session):
    for path in {item.path for item in session.items}:
        yield path.read_text(encoding="utf-8").lower()


@pytest.fixture(scope="session", autouse=True)
def basic_vault_template(request, tmp_path_factory):
    from tests import helpers
    global _durability_active
    # A session of tests that never name a vault skips the 0.8 s build. It can't be built on first use instead: that
    # first test's monkeypatches would end up inside every later copy. A wrong guess here is only slower, because
    # create_basic_vault with no template builds the real vault itself.
    if not any("vault" in source for source in _selected_sources(request.session)):
        yield
        return
    # Only fast-lane tests copy the template, so it is built in the session's
    # lane even when a durability test is the first to request it; otherwise
    # it would carry a WAL header into every fast-lane copy.
    requesting_lane = _durability_active
    _durability_active = _session_durable
    try:
        paths = helpers.create_basic_vault(tmp_path_factory.mktemp("basic-template") / "vault", fresh=True)
    finally:
        _durability_active = requesting_lane
    # Copying a database with embedded template-root identities would silently
    # point tests at shared state. Scan text and SQLite bytes before enabling it.
    prefix = str(paths.root).encode()
    files_naming_root = [
        str(path.relative_to(paths.root))
        for path in paths.root.rglob("*")
        if path.is_file() and prefix in path.read_bytes()
    ]
    assert not files_naming_root, f"template vault files embed their absolute root: {files_naming_root}"
    helpers._BASIC_VAULT_TEMPLATE = paths
    yield
    helpers._BASIC_VAULT_TEMPLATE = None
