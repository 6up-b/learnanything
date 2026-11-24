"""``scripts/label_retirement_counts.py``: the owner-copy counts for the difficulty label's retirement. On a copy of a
vault below the tag, upgraded the way ``learnloop upgrade`` does (the tag, then a whole-vault rebuild), it reads both
copies without writing them, prints counts only, and its comparison agrees with the four-way replay's arm (f)."""

from __future__ import annotations

import json

from learnloop.algorithm_versions import LABEL_RETIRED_ALGORITHM_VERSION, PROBE_ROUTER_ALGORITHM_VERSION
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.vault.loader import load_vault

from tests.difficulty_replay_helpers import HISTORY, build_vault, file_digests, forbid_model_clients, load_script
from tests.helpers import set_algorithm_version

AS_OF = "2027-01-15T00:00:00Z"


def test_the_counts_before_and_after_the_upgrade_and_their_comparison(tmp_path, monkeypatch, capsys):
    forbid_model_clients(monkeypatch)
    script = load_script("label_retirement_counts")
    before_paths = build_vault(tmp_path / "before", served=True, version=PROBE_ROUTER_ALGORITHM_VERSION)
    after_root = tmp_path / "after"
    copy_tree_with_databases(before_paths.root, after_root)
    after_paths = type(before_paths)(after_root, before_paths.config)
    set_algorithm_version(after_paths, LABEL_RETIRED_ALGORITHM_VERSION)
    rebuild_all_derived_state(load_vault(after_root), Repository(after_paths.sqlite_path))

    digests = file_digests(before_paths.root), file_digests(after_root)
    private = tmp_path / "private"
    private.mkdir()
    assert script.main(["snapshot", str(before_paths.root), "--as-of", AS_OF, "--out", str(private / "a.json")]) == 0
    before = json.loads(capsys.readouterr().out)
    assert script.main(["snapshot", str(after_root), "--as-of", AS_OF, "--out", str(private / "b.json")]) == 0
    after = json.loads(capsys.readouterr().out)
    assert (file_digests(before_paths.root), file_digests(after_root)) == digests

    assert before["algorithm_version"] == PROBE_ROUTER_ALGORITHM_VERSION and before["grade_time_receipts"] == 0
    assert before["surprise_by_source"] == {"none (below the tag)": len(HISTORY)}
    assert before["ad_rows_with_kl"] == 0
    # The upgrade replays no AD over history: no grade-time receipt; history reads a bound serve receipt or mastery.
    assert after["grade_time_receipts"] == 0
    assert set(after["surprise_by_source"]) == {"serve_receipt", "mastery"}
    assert sum(after["surprise_by_source"].values()) == len(HISTORY)
    assert after["ad_rows_with_kl"] == after["ad_trained_subject_rows"] > 0
    assert after["integrity"] == "ok" and after["foreign_key_violations"] == 0

    assert script.main(["compare", str(private / "a.json"), str(private / "b.json")]) == 0
    compared = json.loads(capsys.readouterr().out)
    assert (compared["from"], compared["to"]) == (PROBE_ROUTER_ALGORITHM_VERSION, LABEL_RETIRED_ALGORITHM_VERSION)
    assert compared["mastery_changed"].split("/")[1] == str(before["mastery_rows"])
    assert int(compared["mastery_changed"].split("/")[0]) > 0
    assert isinstance(compared["surprise_direction_changed"], int)
    # Stdout holds counts and statistics only: no attempt, item or learning object id.
    printed = json.dumps([before, after, compared])
    assert "pi_" not in printed and "lo_" not in printed and "01" + "M" not in printed


def test_a_live_vault_path_is_refused(tmp_path, monkeypatch):
    script = load_script("label_retirement_counts")
    monkeypatch.setenv("HOME", str(tmp_path))
    live = tmp_path / "learnloop-vaults" / "v"
    live.mkdir(parents=True)
    import pytest

    with pytest.raises(SystemExit):
        script.main(["snapshot", str(live), "--out", str(tmp_path / "x.json")])
