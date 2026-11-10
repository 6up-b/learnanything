"""R4 shadow-rebuild isolation, semantic diff, and CLI contracts."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.substrate.shadow_rebuild import ConfigOverrideError, shadow_rebuild
from learnloop.vault.loader import load_vault
from tests.helpers import MIGRATION_HEAD_FIXTURE


FIXTURE_VAULT = (MIGRATION_HEAD_FIXTURE)


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    destination = tmp_path / name
    shutil.copytree(FIXTURE_VAULT, destination)
    return destination


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _receipt_count(path: Path) -> int:
    with connect(path, read_only=True) as connection:
        return int(
            connection.execute(
                "SELECT COUNT(*) FROM derived_state_rebuilds"
            ).fetchone()[0]
        )


def test_shadow_rebuild_reports_semantic_diff_and_proves_live_db_isolation(tmp_path):
    root = _copy_fixture(tmp_path, "service")
    database = root / "state.sqlite"
    before_hash = _sha256(database)
    receipts_before = _receipt_count(database)

    result = shadow_rebuild(
        load_vault(root),
        assignments=(
            "algorithms.algorithm_version=mvp-0.7",
            "mastery.base_observation_variance=2.0",
        ),
    )

    assert result.baseline_algorithm_version == "mvp-0.6"
    assert result.candidate_algorithm_version == "mvp-0.7"
    assert result.applied_overrides == {
        "algorithms.algorithm_version": "mvp-0.7",
        "mastery.base_observation_variance": 2.0,
    }
    assert result.live_database_unchanged is True
    assert result.live_database_sha256_before == before_hash
    assert result.live_database_sha256_after == before_hash
    assert _sha256(database) == before_hash
    assert _receipt_count(database) == receipts_before

    diff = result.learner_state_diff
    assert set(diff) == {"mastery", "facet", "schedule", "summary"}
    assert diff["summary"]["mastery"] > 0
    assert diff["summary"]["facet"] > 0
    assert diff["summary"]["schedule"] > 0
    assert diff["mastery"]["changes"]
    assert {
        change["key"]["projection"] for change in diff["facet"]["changes"]
    } <= {"evidence_facet_recall_state", "facet_recall_state"}

    # Opening the source for verification is physically read-only, and the
    # candidate receipt/version exists only in the discarded scratch database.
    live = Repository.attach(database, read_only=True)
    with live.connection() as connection:
        versions = {
            str(row[0])
            for row in connection.execute(
                "SELECT DISTINCT algorithm_version FROM learning_object_mastery"
            )
        }
    assert versions == {"mvp-0.5"}


def test_shadow_rebuild_cli_json_is_stable_and_leaves_live_hash_unchanged(tmp_path):
    root = _copy_fixture(tmp_path, "cli-shadow")
    database = root / "state.sqlite"
    before_hash = _sha256(database)
    receipts_before = _receipt_count(database)

    invocation = CliRunner().invoke(
        app,
        [
            "rebuild",
            "--shadow",
            "--set",
            "algorithms.algorithm_version=mvp-0.7",
            "--json",
            "--vault",
            str(root),
        ],
    )

    assert invocation.exit_code == 0, invocation.output
    payload = json.loads(invocation.output)
    assert set(payload) == {"version", "shadow_rebuild"}
    assert payload["version"] == 1
    report = payload["shadow_rebuild"]
    assert report["mode"] == "shadow"
    assert report["candidate_algorithm_version"] == "mvp-0.7"
    assert report["applied_overrides"] == {
        "algorithms.algorithm_version": "mvp-0.7"
    }
    assert report["live_database"] == {
        "sha256_before": before_hash,
        "sha256_after": before_hash,
        "unchanged": True,
    }
    assert set(report["learner_state_diff"]) == {
        "mastery",
        "facet",
        "schedule",
        "summary",
    }
    # RO1 (codex review F2, F3): serving's own read of each side, the live side read-only.
    items = report["schedule_effects"]["practice_item_state"]
    assert {"queue_due", "review_load_per_day", "interval_ratio"} <= set(items)
    assert "queue_due" not in report["schedule_effects"]["activity_card_state"]
    assert _sha256(database) == before_hash
    assert _receipt_count(database) == receipts_before


def test_shadow_rebuild_rejects_unknown_override_without_touching_live_db(tmp_path):
    root = _copy_fixture(tmp_path, "bad-override")
    database = root / "state.sqlite"
    before_hash = _sha256(database)

    try:
        shadow_rebuild(load_vault(root), assignments=("algorithms.typo=mvp-0.7",))
    except ConfigOverrideError as exc:
        assert "unknown config path" in str(exc)
    else:  # pragma: no cover - explicit assertion gives a clearer failure
        raise AssertionError("unknown override was accepted")

    assert _sha256(database) == before_hash


def test_legacy_rebuild_command_keeps_json_shape_and_writes_one_receipt(tmp_path):
    root = _copy_fixture(tmp_path, "legacy-cli")
    database = root / "state.sqlite"
    receipts_before = _receipt_count(database)

    invocation = CliRunner().invoke(
        app,
        ["rebuild-derived-state", "--json", "--vault", str(root)],
    )

    assert invocation.exit_code == 0, invocation.output
    payload = json.loads(invocation.output)
    assert set(payload) == {"version", "rebuild"}
    assert set(payload["rebuild"]) == {
        "algorithm_version",
        "rebuilt_learning_objects",
        "replayed_attempts",
        "learning_object_ids",
        "marker_id",
    }
    assert _receipt_count(database) == receipts_before + 1


def test_a_live_database_that_changes_during_the_run_is_refused(tmp_path):
    """The isolation guard itself. A shadow rebuild is trusted because it refuses to report over a live database that
    moved under it, and every other test here only sees the guard stay silent."""

    import sqlite3
    from contextlib import closing

    import pytest

    from learnloop.substrate.shadow_rebuild import LiveDatabaseChangedError
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    live = Path(paths.sqlite_path)

    def write_to_live(_vault, _repository):
        with closing(sqlite3.connect(live)) as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS moved_under_the_shadow(n)")
            connection.commit()

    with pytest.raises(LiveDatabaseChangedError):
        shadow_rebuild(vault, observe=write_to_live)
    # The control: the same hook that only reads passes.
    assert shadow_rebuild(vault, observe=lambda _vault, _repository: None).live_database_unchanged
