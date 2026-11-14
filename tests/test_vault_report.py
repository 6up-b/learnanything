"""The owner's read-only vault report (``scripts/vault_report.py``, refactor strategy v3 §2.6 D1), on synthetic vaults.

It names the tag, the migration head, an activation journal, the removal steps' keys and the kill switches a vault
sets (with each switch's value and default, and no other value, id or learner text); and it changes nothing on disk
(no write, no journal mode, no companion file).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from tests.helpers import create_basic_vault

ROOT = Path(__file__).resolve().parents[1]

#: A whole learnloop.toml (the report reads the file, never the model). Every value is a sentinel: none may reach
#: the report.
CONFIG = """
schema_version = 2

[storage]
sqlite_path = "state.sqlite"

[algorithms]
algorithm_version = "mvp-0.55"

[locks]
facet_lock_mass = 3.25

[facet_identity]
merge_locked_facets = false

[plan]
pre_questions = 7

[error_impacts.recall_failure]
families = { recall = -0.25 }
lo_mastery_delta = -0.0625

[codex]
model = "SENTINEL-codex-model"

[ai]
active_provider = "my_codex"
fallback_provider = "chatgpt_low"

[ai.providers.my_codex]
type = "codex_sdk"
model = "SENTINEL-profile-model"

[ai.routing]
grading = "my_codex"
tutor_qa = "codex_low"
proof_check = "chatgpt_low"

[router_objective]
merged_sessions = false
failure_share_to_other_policy = false

[followups]
enabled = false
"""


@pytest.fixture()
def vault_report():
    spec = importlib.util.spec_from_file_location("vault_report_script", ROOT / "scripts" / "vault_report.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _snapshot(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def _head(database: Path) -> int:
    connection = sqlite3.connect(database)
    try:
        return connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
    finally:
        connection.close()


def test_the_report_names_what_the_removals_touch_and_nothing_else(tmp_path, vault_report, capsys):
    paths = create_basic_vault(tmp_path / "with_keys")
    (paths.root / "learnloop.toml").write_text(CONFIG, encoding="utf-8")
    paths.sqlite_path.with_name(paths.sqlite_path.name + ".claim-fixes-activation").write_text(
        json.dumps({"predecessor": "mvp-0.54", "target": "mvp-0.55"}), encoding="utf-8")
    plain = create_basic_vault(tmp_path / "plain")
    before = {root: _snapshot(root) for root in (paths.root, plain.root)}

    assert vault_report.main([str(paths.root), str(plain.root), "--json"]) == 0
    printed = capsys.readouterr().out
    with_keys, without = json.loads(printed)

    assert with_keys["vault"] == "with_keys"
    assert with_keys["algorithm_version"] == "mvp-0.55"
    assert with_keys["migration_head"] == _head(paths.sqlite_path)
    assert with_keys["activation_journal"] == {"present": True, "predecessor": "mvp-0.54", "target": "mvp-0.55"}
    assert with_keys["c3_keys"] == ["locks", "locks.facet_lock_mass", "facet_identity.merge_locked_facets",
                                    "plan.pre_questions", "error_impacts.recall_failure.lo_mastery_delta"]
    assert sorted(with_keys["c4_keys"]) == sorted([
        "ai.routing.proof_check", "codex", "codex.model", "ai.providers.my_codex", "ai.active_provider",
        "ai.routing.grading", "ai.routing.tutor_qa"])
    assert [(row["path"], row["tag"], row["value"], row["differs"]) for row in with_keys["tagged_switches"]] == [
        ("followups.enabled", "mvp-0.39", False, True),
        ("router_objective.merged_sessions", "mvp-0.50", False, True),
        ("router_objective.failure_share_to_other_policy", "mvp-0.55", False, True)]
    assert with_keys["untagged_switches"] == []

    assert without["activation_journal"] == {"present": False}
    assert (without["c3_keys"] == without["c4_keys"] == without["tagged_switches"]
            == without["untagged_switches"] == [])

    # No value reaches the output: only names, tags and the migration number.
    for sentinel in ("SENTINEL", "3.25", "-0.0625", "chatgpt_low"):
        assert sentinel not in printed
    # Nothing on disk changed, and no companion file appeared beside either database.
    assert {root: _snapshot(root) for root in (paths.root, plain.root)} == before


def test_the_text_report_and_a_directory_without_a_config(tmp_path, vault_report, capsys):
    paths = create_basic_vault(tmp_path / "vault")
    (tmp_path / "empty").mkdir()
    assert vault_report.main([str(paths.root), str(tmp_path / "empty")]) == 1
    out = capsys.readouterr().out
    assert "vault:\n  algorithm_version: mvp-" in out
    assert ("  activation journal: no\n  C3 keys set: none\n  C4 keys set: none\n  tagged switches set: none\n"
            "  other kill switches set: none") in out
    assert "Not read (outside learnloop.toml): phone_probes" in out
    assert "empty: no readable learnloop.toml (FileNotFoundError)" in out


def test_a_wal_mode_database_is_read_with_no_companion_file_left(tmp_path, vault_report):
    root = tmp_path / "wal_vault"
    root.mkdir()
    (root / "learnloop.toml").write_text('[algorithms]\nalgorithm_version = "mvp-0.55"\n', encoding="utf-8")
    database = root / "state.sqlite"
    writer = sqlite3.connect(database)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("CREATE TABLE schema_migrations(version INTEGER)")
    writer.execute("INSERT INTO schema_migrations VALUES (250)")
    writer.commit()
    writer.close()  # checkpointed: no -wal or -shm remains
    assert sorted(path.name for path in root.iterdir()) == ["learnloop.toml", "state.sqlite"]
    before = _snapshot(root)
    assert vault_report.report(root)["migration_head"] == 250
    assert _snapshot(root) == before

    # With the app open (a writer holding the WAL), the frames not yet checkpointed are read too.
    writer = sqlite3.connect(database)
    try:
        writer.execute("INSERT INTO schema_migrations VALUES (251)")
        writer.commit()
        companions = sorted(path.name for path in root.iterdir())
        assert companions == ["learnloop.toml", "state.sqlite", "state.sqlite-shm", "state.sqlite-wal"]
        assert vault_report.report(root)["migration_head"] == 251
        assert sorted(path.name for path in root.iterdir()) == companions
    finally:
        writer.close()


SWITCHES = """
[algorithms]
algorithm_version = "mvp-0.58"

[router_objective]
stop_coin = 0.05
check_rate = "off"
merged_sessions = false

[ui]
shell = "classic"

[hints]
adaptive_enabled = true

[teacher]
enabled = true
"""


def test_the_report_names_exactly_the_switches_a_vault_sets_and_whether_each_moved(tmp_path, vault_report, capsys):
    """One at its default, one off, one mode, in each table: nothing else is reported, a key counts when present."""

    root = tmp_path / "switches"
    root.mkdir()
    (root / "learnloop.toml").write_text(SWITCHES, encoding="utf-8")
    entry = vault_report.report(root)
    assert [(row["path"], row["tag"], row["value"], row["default"], row["differs"]) for row in entry["tagged_switches"]] == [
        ("teacher.enabled", "mvp-0.41", True, True, False),
        ("router_objective.stop_coin", "mvp-0.48", 0.05, 0.05, False),
        ("router_objective.check_rate", "mvp-0.48", "off", "embedded", True),
        ("router_objective.merged_sessions", "mvp-0.50", False, True, True)]
    assert [(row["path"], row["value"], row["differs"]) for row in entry["untagged_switches"]] == [
        ("hints.adaptive_enabled", True, False), ("ui.shell", "classic", True)]

    assert vault_report.main([str(root)]) == 0
    out = capsys.readouterr().out
    assert "    router_objective.merged_sessions [mvp-0.50] = false  (DIFFERS from the default true)" in out
    assert '    router_objective.check_rate [mvp-0.48] = "off"  (DIFFERS from the default "embedded")' in out
    assert "    teacher.enabled [mvp-0.41] = true  (equals the default true)" in out
    assert '    ui.shell = "classic"  (DIFFERS from the default "simple")' in out


def test_a_switch_set_to_a_table_or_a_wrong_type_is_reported_without_its_contents(tmp_path, vault_report):
    root = tmp_path / "odd"
    root.mkdir()
    (root / "learnloop.toml").write_text(
        '[teacher]\nenabled = 1\n[router]\nrestraint = { note = "SENTINEL" }\n', encoding="utf-8")
    rows = {row["path"]: row for row in vault_report.report(root)["tagged_switches"]}
    assert rows["teacher.enabled"]["differs"] is True  # an integer is not the boolean default
    assert rows["router.restraint"]["value"] == "<table>"
    assert "SENTINEL" not in json.dumps(rows)
