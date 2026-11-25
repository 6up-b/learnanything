"""Arms (e) and (f) of the difficulty replay (scripts/difficulty_four_way.py; H3's design note §2.2, §10): surprise
read from the forecast AD recorded when it served the item, mastery's own prediction where no receipt applies, on a
synthetic vault answered from plan presentations whose serve AD's own hook recorded. No model is called."""

from __future__ import annotations

import math
from contextlib import closing
from datetime import UTC, datetime

import pytest

from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases

from tests.difficulty_replay_helpers import (
    HISTORY,
    RETRY,
    UNBOUND,
    build_vault,
    file_digests,
    forbid_model_clients,
    load_script,
)

AS_OF = datetime(2027, 1, 15, tzinfo=UTC)
E, F = "e_surprise_from_receipt", "f_label_off_and_receipt"


@pytest.fixture(scope="module")
def script():
    return load_script("difficulty_four_way")


@pytest.fixture(scope="module")
def run(script, tmp_path_factory):
    paths = build_vault(tmp_path_factory.mktemp("receipt-arms") / "vault", served=True)
    before = file_digests(paths.root)
    with pytest.MonkeyPatch.context() as monkeypatch:
        forbid_model_clients(monkeypatch)
        report = script.run_four_way(paths.root, as_of=AS_OF, top_k=(3,))
    return {"paths": paths, "report": report, "before": before, "after": file_digests(paths.root)}


def _logit(p: float) -> float:
    return math.log(p / (1.0 - p))


def test_the_receipt_rule_picks_the_first_bound_attempt_with_a_valid_subject_view_receipt(run, script):
    with closing(connect(run["paths"].sqlite_path, read_only=True)) as connection:
        receipts = script.receipt_predictions(connection)
        order = [str(r[0]) for r in connection.execute("SELECT id FROM practice_attempts ORDER BY created_at, id")]
    assert len(order) == len(HISTORY)
    tiers = {index: (receipts[attempt].tier, receipts[attempt].reason) for index, attempt in enumerate(order)}
    for index in UNBOUND:
        assert tiers[index] == ("fallback", "unbound")
    # The live door does not bind a second answer to an answered presentation: the retry is unbound.
    assert tiers[RETRY] == ("fallback", "unbound")
    served = [index for index in range(len(HISTORY)) if index not in UNBOUND and index != RETRY]
    assert {tiers[index][0] for index in served} == {"receipt"}
    # A never-attempted item's serve and a repeat's serve each have their subject-view forecast.
    assert {tiers[index][1] for index in served} == {"ad_threshold@subject", "ad_threshold_repeat@subject"}
    assert run["report"]["receipts"]["tiers"] == {"fallback": len(UNBOUND) + 1, "receipt": len(served)}


def test_the_arms_run_on_scratch_copies_and_the_input_is_never_written(run):
    report = run["report"]
    assert report["arms"][E]["surprise_source"] == "receipt" and report["arms"][F]["surprise_source"] == "receipt"
    assert report["arms"][F]["applied_overrides"] == {"algorithms.algorithm_version": "mvp-0.71"}
    assert report["arms"][E]["applied_overrides"] == {}
    assert report["input_databases_unchanged"] is True
    assert run["after"] == run["before"]


def test_surprise_reads_the_receipt_and_mastery_never_does(run):
    report = run["report"]
    values = report["values"]
    receipts = report["receipts"]["per_attempt"]
    # The surprise source never reaches mastery or the queue.
    assert values[E]["mastery"] == values["a_today"]["mastery"]
    assert values[F]["mastery"] == values["b_label_off_mastery"]["mastery"]
    assert report["comparisons"][E]["queue"]["same_order"] is True
    for arm, mastery_arm in ((E, "a_today"), (F, "b_label_off_mastery")):
        patch = report["arms"][arm]["surprise_patch"]
        fallback, receipt = ("mastery", "serve_receipt") if arm == F else ("fallback", "receipt")
        assert patch["tiers"] == {fallback: len(UNBOUND) + 1, receipt: len(HISTORY) - len(UNBOUND) - 1}
        assert patch["outside_grade"] == 0
        for attempt_id, row in values[arm]["surprise"].items():
            entry = receipts[attempt_id]
            if entry["tier"] == "receipt":
                # The stored prediction is the receipt's p (no receipt-covered attempt here is primed).
                if arm == F:
                    assert row["expected_correctness"] == values[mastery_arm]["surprise"][attempt_id]["expected_correctness"]
                scored = row["p_scored"] if arm == F else row["expected_correctness"]
                assert math.isclose(_logit(scored), _logit(entry["p"]), abs_tol=1e-9)
            else:
                # Where no receipt applies the row is the mastery path's own, exactly.
                baseline = values[mastery_arm]["surprise"][attempt_id]
                if arm == F:
                    baseline = {**baseline, "prediction_source": "mastery", "p_scored": baseline["expected_correctness"]}
                assert row == baseline
    assert report["comparisons"][E]["surprise"]["changed"] > 0


def test_the_receipt_is_compared_with_ads_prediction_replayed_to_the_attempt(run):
    against = run["report"]["receipts"]["against_prefix"]
    assert against["both"] == len(HISTORY) - len(UNBOUND) - 1
    assert against["abs_p_difference"]["n"] == against["both"]


def test_without_any_receipt_the_arms_are_the_mastery_paths_own(script, tmp_path, monkeypatch):
    forbid_model_clients(monkeypatch)
    copy = build_vault(tmp_path / "none", served=False).root
    arms = {arm.name: arm for arm in script.ARMS}
    report = script.run_four_way(copy, as_of=AS_OF, arms=(arms["a_today"], arms["b_label_off_mastery"], arms[E],
                                                          arms[F]))
    values = report["values"]
    assert report["arms"][F]["surprise_patch"]["tiers"] == {"mastery": len(HISTORY)}
    assert values[E]["surprise"] == values["a_today"]["surprise"]
    assert values[F]["surprise"] == {
        attempt: {**row, "prediction_source": "mastery", "p_scored": row["expected_correctness"]}
        for attempt, row in values["b_label_off_mastery"]["surprise"].items()
    }


def test_stdout_reports_the_receipt_counts_and_no_id(script, run, tmp_path, capsys, monkeypatch):
    from learnloop.vault.loader import load_vault

    forbid_model_clients(monkeypatch)
    source = tmp_path / "cli"
    copy_tree_with_databases(run["paths"].root, source)
    assert script.main([str(source), "--out", str(tmp_path / "private" / "r.json"),
                        "--as-of", "2027-01-15T00:00:00Z"]) == 0
    printed = capsys.readouterr().out
    vault = load_vault(source, load_environment=False)
    forbidden = set(run["report"]["values"]["a_today"]["surprise"]) | set(vault.practice_items)
    forbidden |= {item.prompt for item in vault.practice_items.values()} | {"pp_h3_", "blk_h3_"}
    assert not [token for token in forbidden if token in printed]
    assert "receipts: tiers" in printed and "above the follow-up threshold" in printed


@pytest.mark.parametrize("version", ["mvp-0.71", "mvp-0.72"])
def test_arm_f_matches_production_with_all_three_receipt_sources(tmp_path, script, monkeypatch, version):
    from learnloop.adaptive_difficulty import surprise_forecast
    from tests.ux_phase1_support import set_config

    forbid_model_clients(monkeypatch)
    real = surprise_forecast.safe_grade_receipt

    def sometimes_missing(*args, **kwargs):
        return None if kwargs["practice_item_id"] == HISTORY[UNBOUND[0]][0] else real(*args, **kwargs)

    monkeypatch.setattr(surprise_forecast, "safe_grade_receipt", sometimes_missing)
    paths = build_vault(tmp_path / "vault", served=True, version=version)
    set_config(paths.root, {("mastery", "irt", "difficulty_default"): 1.5})
    report = script.run_four_way(paths.root, as_of=AS_OF, arms=(script.ARMS[0], script.ARMS[-1]))
    expected = report["values"]["a_today"]
    actual = report["values"][F]
    assert actual["surprise"] == expected["surprise"]
    assert actual["mastery"] == expected["mastery"]
    assert {r["prediction_source"] for r in actual["surprise"].values()} == {"serve_receipt", "grade_receipt", "mastery"}
    assert set(report["arms"][F]["surprise_patch"]["tiers"]) == {"serve_receipt", "grade_receipt", "mastery"}
