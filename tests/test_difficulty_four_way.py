"""The four-way difficulty replay (scripts/difficulty_four_way.py) on a synthetic vault: every arm runs on scratch
copies, the input is never written, the arms move exactly what each changes, and no model is called."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path

import pytest

from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.substrate.shadow_rebuild import shadow_rebuild
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.difficulty_replay_helpers import HISTORY, build_vault, file_digests, forbid_model_clients, load_script

AS_OF = datetime(2027, 1, 15, tzinfo=UTC)


@pytest.fixture(scope="module")
def script():
    return load_script("difficulty_four_way")


@pytest.fixture(scope="module")
def run(script, tmp_path_factory):
    paths = build_vault(tmp_path_factory.mktemp("four-way") / "vault")
    before = file_digests(paths.root)
    with pytest.MonkeyPatch.context() as monkeypatch:
        forbid_model_clients(monkeypatch)
        report = script.run_four_way(paths.root, as_of=AS_OF, top_k=(3, 10))
    return {"paths": paths, "report": report, "before": before, "after": file_digests(paths.root)}


def _copy(paths: VaultPaths, destination: Path) -> Path:
    copy_tree_with_databases(paths.root, destination)
    return destination


def test_each_arm_runs_on_scratch_copies_and_the_input_is_never_written(run):
    report = run["report"]
    assert list(report["arms"]) == ["a_today", "b_label_off_mastery", "c_surprise_from_ad", "d_both",
                                    "e_surprise_from_receipt", "f_label_off_and_receipt"]
    assert set(report["comparisons"]) == {"b_label_off_mastery", "c_surprise_from_ad", "d_both",
                                          "e_surprise_from_receipt", "f_label_off_and_receipt"}
    assert {arm["replayed_attempts"] for arm in report["arms"].values()} == {len(HISTORY)}
    assert report["arms"]["b_label_off_mastery"]["applied_overrides"] == {"mastery.irt.difficulty_from_prior": False}
    assert report["arms"]["d_both"]["applied_overrides"] == {"mastery.irt.difficulty_from_prior": False}
    assert report["arms"]["c_surprise_from_ad"]["applied_overrides"] == {}
    assert report["input_databases_unchanged"] is True
    # Independently of the script's own check: no file of the input changed, appeared or went.
    assert run["after"] == run["before"]


def test_arm_a_equals_a_plain_shadow_rebuild(run, script, tmp_path):
    root = _copy(run["paths"], tmp_path / "plain")
    vault = load_vault(root, load_environment=False)
    live = VaultPaths(vault.root, vault.config).sqlite_path.resolve()

    def observe(loaded, repository):
        if Path(repository.sqlite_path).resolve() == live:
            return None
        return script.read_replayed(loaded, repository, as_of=AS_OF)

    plain = shadow_rebuild(vault, observe=observe)
    assert plain.observed_after == run["report"]["values"]["a_today"]
    # Neither (a) nor (b) runs with the surprise patch.
    assert run["report"]["arms"]["a_today"]["surprise_patch"] is None
    assert run["report"]["arms"]["b_label_off_mastery"]["surprise_patch"] is None


def test_the_label_off_moves_mastery_and_surprise(run):
    entry = run["report"]["comparisons"]["b_label_off_mastery"]
    assert entry["mastery"]["changed"] > 0
    assert entry["surprise"]["changed"] > 0


def test_surprise_from_ad_moves_surprise_alone_and_reads_ads_prediction(run, script):
    report = run["report"]
    values = report["values"]
    entry = report["comparisons"]["c_surprise_from_ad"]
    assert values["c_surprise_from_ad"]["mastery"] == values["a_today"]["mastery"]
    assert entry["mastery"]["changed"] == 0
    assert entry["surprise"]["changed"] > 0
    # The queue reads mastery, never surprise.
    assert entry["queue"]["same_order"] is True
    # (d)'s mastery is (b)'s: the surprise source never reaches the mastery update.
    assert values["d_both"]["mastery"] == values["b_label_off_mastery"]["mastery"]
    predictive = report["ad"]["predictive"]
    patch = report["arms"]["c_surprise_from_ad"]["surprise_patch"]
    assert sum(patch["tiers"].values()) == len(HISTORY) and patch["outside_grade"] == 0
    assert {"item", "population"} <= set(report["ad"]["predictive_tiers"])
    offset = 2.0  # mastery.irt.priming_b_offset at its default, with a = 1
    primed = 0
    for arm in ("c_surprise_from_ad", "d_both"):
        for attempt_id, row in values[arm]["surprise"].items():
            p = predictive[attempt_id]["p"]
            expected = row["expected_correctness"]
            if math.isclose(math.log(expected / (1 - expected)), math.log(p / (1 - p)), abs_tol=1e-9):
                continue
            # A primed retry: the same priming offset the label's b takes, on AD's implied b.
            assert math.isclose(math.log(expected / (1 - expected)), math.log(p / (1 - p)) + offset, abs_tol=1e-9)
            primed += 1
    assert primed == 2  # the one primed attempt, in each of the two arms


def test_where_ad_has_no_prediction_surprise_uses_difficulty_default(script, run, tmp_path, monkeypatch):
    forbid_model_clients(monkeypatch)
    monkeypatch.setattr(script, "ad_predictive", lambda _events, _settings: {})
    report = script.run_four_way(_copy(run["paths"], tmp_path / "cold"), as_of=AS_OF,
                                 arms=(script.ARMS[0], script.ARMS[1], script.ARMS[3]))
    values = report["values"]
    assert report["arms"]["d_both"]["surprise_patch"]["tiers"] == {"default": len(HISTORY)}
    # With no prediction, (d)'s surprise reads b = difficulty_default, exactly (b)'s surprise.
    assert values["d_both"]["surprise"] == values["b_label_off_mastery"]["surprise"]


def test_stored_due_dates_do_not_read_surprise_at_the_head(run):
    report = run["report"]
    assert report["interval_factor_removed"] is True
    for entry in report["comparisons"].values():
        assert entry["due"]["practice_item_state"]["moved"] == 0
        assert entry["surprise"]["interval_factor_changed"] == 0


def test_the_prefix_replay_predicts_as_ads_own_observer_does(run, script, tmp_path):
    root = _copy(run["paths"], tmp_path / "prefix")
    vault = load_vault(root, load_environment=False)
    repository = Repository.attach(VaultPaths(vault.root, vault.config).sqlite_path, read_only=True)
    events, settings = script._load_ad_events(vault, repository)
    prefix = script.ad_predictive(events, settings)
    observed = script.ad_observer_predictions(events, settings)
    assert observed and set(observed) < set(prefix)  # repeats are predicted too
    for attempt_id, p in observed.items():
        assert prefix[attempt_id].p == pytest.approx(p, abs=1e-12)


def test_ad_scoring_with_and_without_z_llm(run):
    scoring = run["report"]["ad"]["scoring"]
    assert run["report"]["ad"]["events_identical_across_arms"] is True
    assert scoring["attempts_with_z_llm"] > 0
    assert scoring["abs_p_shift"]["max"] > 0
    assert scoring["variants"]["with_z_llm"]["all"]["n"] == scoring["variants"]["without_z_llm"]["all"]["n"] > 0


def test_stdout_shows_counts_only_and_the_json_keeps_the_values(script, run, tmp_path, capsys, monkeypatch):
    forbid_model_clients(monkeypatch)
    source = _copy(run["paths"], tmp_path / "cli")
    out = tmp_path / "private" / "report.json"
    assert script.main([str(source), "--out", str(out), "--as-of", "2027-01-15T00:00:00Z"]) == 0
    printed = capsys.readouterr().out
    payload = json.loads(out.read_text(encoding="utf-8"))
    attempt_ids = set(payload["values"]["a_today"]["surprise"])
    vault = load_vault(source, load_environment=False)
    forbidden = attempt_ids | set(vault.practice_items) | set(vault.learning_objects)
    forbidden |= {item.prompt for item in vault.practice_items.values()}
    assert attempt_ids and not [token for token in forbidden if token in printed]
    assert "mastery changed" in printed and "queue:" in printed
    with pytest.raises(SystemExit):
        script.main([str(source), "--out", str(source / "inside.json")])
    assert not (source / "inside.json").exists()
