"""The table review list (``scripts/table_review.py``, refactor step J1), on a synthetic source tree and vault copy.

It classes each table from the code (live, derived, retired but still read, dead), says whether readers guard against
a missing table, compares with an older tree, and counts rows only into the private output: the tracked part names no
count, date or value. It opens copies read-only, refuses the owner's live directories, and gives the same bytes twice.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

ROLES = '''
from enum import Enum


class TableRole(str, Enum):
    RAW_LEDGER = "raw_ledger"
    DERIVED = "derived"
    RECEIPT = "receipt"
    WORKFLOW = "workflow"
    COMPAT = "compat"


_TABLE_ROLE_ITEMS: tuple[tuple[str, TableRole], ...] = (
    ("alpha", TableRole.RAW_LEDGER),
    ("beta", TableRole.RECEIPT),
    ("delta", TableRole.DERIVED),
    ("eps", TableRole.WORKFLOW),
    ("gamma", TableRole.COMPAT),
    ("ghost", TableRole.COMPAT),
    ("seeded", TableRole.RAW_LEDGER),
)
'''

STORE = '''
BETA = "beta"
SEEDED = "seeded"


def table_present(connection, name):
    return connection.execute("SELECT 1 FROM sqlite_master WHERE name = ?", (name,)).fetchone() is not None


def _insert(connection, table, row):
    connection.execute(f"INSERT INTO {table} VALUES (?)", row)


def write_alpha(connection):
    connection.execute("INSERT INTO alpha(id, created_at) VALUES (?, ?)", ("a", "2030-01-01T00:00:00Z"))


def read_alpha(connection):
    if not table_present(connection, "alpha"):
        return []
    return connection.execute("SELECT * FROM alpha").fetchall()


def write_beta(connection):
    _insert(connection, BETA, ("b",))


def old_gamma(connection):
    """A docstring is prose, not a reader: SELECT * FROM ghost."""
    connection.execute("UPDATE gamma SET id = 'x'")


def read_eps(connection):
    return connection.execute("SELECT * FROM eps").fetchall()


def never_called(connection):
    connection.execute("DELETE FROM eps")


def read_seeded(connection):
    return connection.execute(f"SELECT * FROM {SEEDED}").fetchall()
'''

APP = '''
from learnloop.store import read_alpha, read_eps, read_seeded, write_alpha, write_beta

ENTRY_POINTS = (write_alpha, read_alpha, write_beta, read_eps, read_seeded)
'''

ORCHESTRATOR = '''
DERIVED_STATE_REPLAYERS = (DerivedStateReplayer("delta_replayer", frozenset({"delta"})),)
'''

DOCTOR = '''
DEPRECATED_TABLES = ("ghost",)
'''

MIGRATION = """
CREATE TABLE alpha (id TEXT PRIMARY KEY, created_at TEXT);
CREATE TABLE beta (id TEXT);
CREATE TABLE delta (id TEXT);
CREATE TABLE eps (id TEXT, alpha_id TEXT REFERENCES alpha(id));
CREATE TABLE gamma (id TEXT);
CREATE TABLE ghost (id TEXT);
CREATE TABLE seeded (id TEXT);
-- a comment naming INSERT INTO ghost is not a write
INSERT INTO seeded VALUES ('x');
"""

#: Private values the tracked output must never carry.
ROWS = 7
NEWEST = "2031-02-03T04:05:06Z"


@pytest.fixture()
def table_review():
    spec = importlib.util.spec_from_file_location("table_review_script", ROOT / "scripts" / "table_review.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _write(root: Path, files: dict[str, str]) -> None:
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


@pytest.fixture()
def tree(tmp_path: Path) -> dict[str, Path]:
    src = tmp_path / "src"
    _write(src, {
        "learnloop/db/table_roles.py": ROLES,
        "learnloop/store.py": STORE,
        "learnloop/app.py": APP,
        "learnloop/substrate/rebuild_orchestrator.py": ORCHESTRATOR,
        "learnloop/ops/doctor.py": DOCTOR,
    })
    # The older tree: the same, plus a reached reader of ``ghost`` that the newer tree removed.
    base = tmp_path / "base" / "src"
    _write(base, {
        "learnloop/db/table_roles.py": ROLES,
        "learnloop/store.py": STORE + '\n\ndef read_ghost(connection):\n    return connection.execute("SELECT * FROM ghost")\n',
        "learnloop/app.py": APP.replace("write_beta\n", "write_beta, read_ghost\n").replace("read_seeded)", "read_seeded, read_ghost)"),
        "learnloop/substrate/rebuild_orchestrator.py": ORCHESTRATOR,
        "learnloop/ops/doctor.py": DOCTOR,
    })
    migrations = tmp_path / "migrations"
    _write(migrations, {"001_init.sql": MIGRATION})
    copy = tmp_path / "copies" / "synthetic"
    copy.mkdir(parents=True)
    connection = sqlite3.connect(copy / "state.sqlite")
    connection.executescript(MIGRATION)
    connection.executemany(
        "INSERT INTO alpha(id, created_at) VALUES (?, ?)",
        [(f"row-{i}", NEWEST if i == ROWS - 1 else "2030-01-01T00:00:00Z") for i in range(ROWS)],
    )
    connection.commit()
    connection.close()
    return {"src": src, "base": base, "migrations": migrations, "copy": copy, "out": tmp_path / "private"}


def _facts(table_review, tree, **kwargs):
    scan = table_review.scan_sources(tree["src"])
    migrations = table_review.migration_facts(tree["migrations"], scan.roles)
    children = table_review.foreign_key_children(tree["migrations"], scan.roles)
    facts = table_review.table_facts(scan, migrations, fk_children=children, **kwargs)
    return {f.table: f for f in facts}


def test_each_table_is_classed_from_the_code(table_review, tree):
    facts = _facts(table_review, tree)

    assert facts["alpha"].klass == "live"
    assert facts["alpha"].writers == ["store.py:15"] and facts["alpha"].readers == ["store.py:21"]
    assert facts["alpha"].tolerates_absence == "yes (1/1)"
    assert "FK parent of 1 table(s)" in facts["alpha"].flags
    # A table handed to a helper whose SQL takes the table from a parameter, through a module constant.
    assert facts["beta"].klass == "live" and facts["beta"].writer_count == 1
    assert "write-only" in facts["beta"].flags
    assert facts["delta"].klass == "derived and rebuildable" and facts["delta"].replayer == "delta_replayer"
    assert facts["eps"].klass == "retired but still read"
    assert "every code writer unreached (1)" in facts["eps"].flags
    assert facts["eps"].tolerates_absence == "no (0/1)"
    assert facts["gamma"].klass == "dead" and "every SQL site unreached (1)" in facts["gamma"].flags
    # Named only in doctor's list and the registry, and in a docstring: no use.
    assert facts["ghost"].klass == "dead" and "no SQL in src" in facts["ghost"].flags
    assert facts["ghost"].doctor is True
    assert facts["seeded"].klass == "live" and "rows written by migration 001" in facts["seeded"].flags


def test_removals_since_an_older_tree_are_named(table_review, tree):
    base = table_review.scan_sources(tree["base"])
    facts = _facts(table_review, tree, base=base)

    assert facts["ghost"].base_class == "retired but still read"
    assert "class changed since the base (retired but still read -> dead)" in facts["ghost"].flags
    assert "removals since the base: 1 SQL site(s) (its last)" in facts["ghost"].flags
    assert facts["alpha"].removed_sites == 0


def test_a_what_if_scan_drops_the_named_files(table_review, tree):
    without = table_review.scan_sources(tree["src"], without=frozenset({"learnloop/store.py"}))
    facts = _facts(table_review, tree, what_if={"C9": without})

    assert "re-check after C9 (without its modules: dead)" in facts["alpha"].flags


def _snapshot(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_counts_stay_private_and_the_run_is_read_only_and_deterministic(table_review, tree, tmp_path):
    public = tmp_path / "table-review.md"
    public.write_text(f"# Review\n\nPreamble.\n\n{table_review.BEGIN}\nstale\n{table_review.END}\n\nAfterword.\n", encoding="utf-8")
    before = _snapshot(tree["copy"])
    argv = [
        "--src", str(tree["src"]), "--migrations", str(tree["migrations"]), "--base-src", str(tree["base"]),
        "--copies", str(tree["copy"]), "--private-out", str(tree["out"]), "--public", str(public),
    ]

    assert table_review.main(argv) == 0
    first = (public.read_bytes(), (tree["out"] / "table-review.json").read_bytes())
    assert table_review.main(argv) == 0
    assert (public.read_bytes(), (tree["out"] / "table-review.json").read_bytes()) == first
    assert _snapshot(tree["copy"]) == before  # no write, no journal or companion file

    text = public.read_text(encoding="utf-8")
    assert text.startswith("# Review\n\nPreamble.\n\n") and text.endswith("\n\nAfterword.\n") and "stale" not in text
    assert "| `alpha` | RAW_LEDGER | live |" in text and "| 1 of 1 |" in text
    assert NEWEST[:10] not in text and "synthetic" not in text
    assert f"| {ROWS} |" not in text
    private = (tree["out"] / "table-review-private.md").read_text(encoding="utf-8")
    assert f"| `alpha` | live | {ROWS} | {NEWEST[:10]} |" in private
    data = json.loads(first[1])
    assert data["copies"]["synthetic"]["tables"]["alpha"]["rows"] == ROWS


def test_it_refuses_the_owners_live_directories(table_review, tmp_path):
    home = tmp_path / "home"
    for name in ("learnloop-vaults", "learnloop-retired", "learnloop-books", "learnloop-backups"):
        with pytest.raises(SystemExit, match=f"~/{name}"):
            table_review.refuse_live(home / name / "linear_algebra", home=home)
    assert table_review.refuse_live(tmp_path / "copies" / "x", home=home) == (tmp_path / "copies" / "x").resolve()


def test_the_registry_parser_reads_this_trees_roles(table_review):
    from learnloop.db.table_roles import TABLE_ROLES

    parsed = table_review.parse_roles(ROOT / "src")
    assert parsed == {table: role.name for table, role in TABLE_ROLES.items()}
