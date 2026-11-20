"""The G2 comparison report (``scripts/probe_router_report.py``, step 5) on the diagnosis journeys' vaults and on
its synthetic journeys.

It reads a vault without writing anything; it classifies every recorded post-miss decision by lane, with the
predecessor's answer, the successor's information class and each payload input's coverage (never filling in a
missing input, never reading a row stamped after the decision); its output carries no id or text; and on the
synthetic journeys it computes both answers and the evaluator's cost.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sqlite3
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from tests.diagnosis_journey_helpers import run_case

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def report():
    spec = importlib.util.spec_from_file_location("probe_router_report", ROOT / "scripts" / "probe_router_report.py")
    module = importlib.util.module_from_spec(spec)
    # Its dataclasses resolve their annotations through the module's entry in sys.modules.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _vault(case: str, root: Path, monkeypatch) -> Path:
    root.mkdir()
    journey = run_case(case, root, monkeypatch)
    return Path(journey.repository.sqlite_path)


def _state(database: Path) -> tuple[str, list[str]]:
    return hashlib.sha256(database.read_bytes()).hexdigest(), sorted(p.name for p in database.parent.iterdir())


def _ids(database: Path) -> set[str]:
    """Every id a decision row of these journeys carries (its own, its subject's, and each ``*_id`` in its facts), and
    the hypotheses' labels, for the leak check."""

    connection = sqlite3.connect(database)
    found: set[str] = set()
    for table, columns in (("decision_records", ("id", "subject_id", "facts_json")),
                           ("causal_probe_decision_receipts", ("id", "factor_id", "attempt_id", "misconception_id",
                                                               "candidate_id", "learning_object_id")),
                           ("followup_workflows", ("id", "source_attempt_id", "factor_id", "learning_object_id")),
                           ("hypothesis_sets", ("id", "learning_object_id", "hypotheses_json"))):
        for column in columns:
            for (value,) in connection.execute(f"SELECT {column} FROM {table}"):
                if value is None:
                    continue
                if column == "facts_json":
                    found.update(str(v) for k, v in json.loads(value).items() if k.endswith("_id") and v)
                elif column == "hypotheses_json":
                    found.update(str(h["label"]) for h in json.loads(value) if h.get("label"))
                else:
                    found.add(str(value))
    connection.close()
    return found


def test_the_journeys_vaults_are_read_without_a_write_and_reported_by_lane(report, tmp_path, monkeypatch):
    """Each lane's opportunities with the predecessor's recorded answer; the successor's information class from the
    recorded facts alone (a hard stop, one repair for every cause, a channel missing because the automatic lane
    decides before it writes the probe); the numeric choice not computable (no vault stores the frozen inputs); and
    the database byte-identical with nothing beside it."""

    asked = _vault("fg1_ask_now", tmp_path / "asked", monkeypatch)
    refused = _vault("fg1_refused_before_authoring", tmp_path / "refused", monkeypatch)
    learner = _vault("causal_reread_and_request", tmp_path / "learner", monkeypatch)
    common = _vault("causal_safe_common_repair_available", tmp_path / "common", monkeypatch)
    before = {path: _state(path) for path in (asked, refused, learner, common)}

    (one,) = [o for o in report.vault_opportunities(asked) if o["lane"] == report.AUTOMATIC]
    assert (one["predecessor"], one["predecessor_rule"], one["information"]) == ("ask_now", "no_plan",
                                                                                 "none_missing_channel")
    assert one["inputs"]["channel"] == report.EXACT and one["inputs"]["locked_set"] == report.MISSING
    assert one["inputs"]["frozen_inputs"] == report.MISSING and one["successor_numeric"] == report.NOT_COMPUTABLE
    (stop,) = [o for o in report.vault_opportunities(refused) if o["lane"] == report.AUTOMATIC]
    assert (stop["predecessor"], stop["information"]) == ("refused", "excluded_hard_stop")

    lane = [o for o in report.vault_opportunities(learner) if o["lane"] == report.LEARNER]
    # Two status reads and the held repair request: one receipt each, every one an offer by the gate.
    assert [o["predecessor"] for o in lane] == ["probe_now"] * 3
    assert {o["information"] for o in lane} == {"not_computable_channel"}
    assert {o["inputs"]["prior"] for o in lane} == {report.AS_OF}
    assert {o["inputs"]["channel"] for o in lane} == {report.MISSING}
    (settled,) = [o for o in report.vault_opportunities(common) if o["lane"] == report.LEARNER]
    assert (settled["predecessor"], settled["information"]) == ("skip_common_repair", "none_one_repair")

    totals = report.aggregate([*report.vault_opportunities(asked), *report.vault_opportunities(learner)])
    assert totals["lanes"][report.LEARNER]["receipts_per_factor"] == {3: 1}
    assert all(entry["successor_numeric_computable"] == 0 for entry in totals["lanes"].values())
    assert {path: _state(path) for path in before} == before


def test_a_row_stamped_after_the_decision_is_not_read(report, tmp_path, monkeypatch):
    """The locked set's prior is the receipt's only as-of read: restamped after the receipts, it is missing, never
    read anyway."""

    learner = _vault("causal_reread_and_request", tmp_path / "learner", monkeypatch)
    connection = sqlite3.connect(learner)
    connection.execute("UPDATE hypothesis_sets SET created_at = '2099-01-01T00:00:00Z'")
    connection.commit()
    connection.close()
    lane = [o for o in report.vault_opportunities(learner) if o["lane"] == report.LEARNER]
    assert {o["inputs"]["prior"] for o in lane} == {report.MISSING}


def test_the_output_carries_no_id_or_text(report, tmp_path, monkeypatch):
    """The rendered report and its JSON hold counts, classes and timings: no id, label or text a row holds."""

    paths = [_vault(case, tmp_path / case, monkeypatch) for case in ("fg1_ask_now", "causal_reread_and_request")]
    ids = set().union(*(_ids(path) for path in paths))
    assert ids
    for path in paths:
        out = io.StringIO()
        with redirect_stdout(out):
            assert report.main(["--vault", str(path), "--json"]) == 0
        text = out.getvalue() + report.render(report.aggregate(report.vault_opportunities(path)), title="t")
        assert json.loads(out.getvalue())["vault 1"]["lanes"]
        assert str(path) not in text and tmp_path.name not in text
        assert [value for value in ids if value in text] == []
    with pytest.raises(SystemExit):
        report.main([])


def test_the_synthetic_journeys_compute_both_answers_and_the_cost(report):
    """On complete snapshots both sides answer: a missing channel and an exposed answer earn nothing; a flat channel
    earns zero; a perfect channel with an illustrative learned gap slope changes the repair with the result; a hard
    stop excludes the probe; no room to wait no longer forces it (decision 3); the lesson's declined probe is
    exposed. Every case is computed and timed."""

    names = {"missing/different/H3", "flat/different/H3", "perfect/different/H3/learned_gap",
             "informative/exposed/H3", "not_now/H3", "no_room/missing/H3", "lesson_declined/perfect/H3/learned_gap"}
    cases = [case for case in report.synthetic_cases() if case.name in names]
    assert len(cases) == len(names)
    rows = {row["case"]: row for row in report.synthetic_opportunities(draws=4, cases=cases)}
    assert rows["missing/different/H3"]["information"] == "none_missing"
    assert rows["flat/different/H3"]["information"] == "zero"
    assert rows["flat/different/H3"]["predecessor_gate"] == "skip_no_discrimination"
    learned = rows["perfect/different/H3/learned_gap"]
    assert learned["information"] == "positive" and learned["policy_changes_with_result"] is True
    assert learned["predecessor_gate"] == "probe_now" and learned["illustrative"] is True
    assert rows["informative/exposed/H3"]["information"] == "none_exposed"
    assert rows["not_now/H3"]["information"] == "excluded_hard_stop" and not rows["not_now/H3"]["successor_asks"]
    no_room = rows["no_room/missing/H3"]
    assert no_room["predecessor_asks"] is True and no_room["successor_asks"] is False
    assert rows["lesson_declined/perfect/H3/learned_gap"]["information"] == "none_exposed"
    totals = report.aggregate(list(rows.values()))
    assert sum(entry["successor_numeric_computable"] for entry in totals["lanes"].values()) == len(names)
    assert all(row["cost"]["ms"] > 0 and row["cost"]["predecessor_probe_ms"] > 0 for row in rows.values())
    table = report.case_table(list(rows.values()))
    assert [row["case"] for row in table] == [row["case"] for row in rows.values()]


def test_the_synthetic_journeys_cover_the_behaviour_steps_cases(report):
    """The full list covers what the evaluator can see of the behaviour step's journeys: missing, flat and
    discriminating channels; common and different repairs; held and exposed answers; the hard stops; no plan and no
    room; a lesson declined at the boundary; the recent-burden rule; one to five named causes."""

    cases = report.synthetic_cases()
    assert {case.channel for case in cases} == {"missing", "flat", "informative", "perfect"}
    assert {case.repairs for case in cases} == {"different", "common"}
    assert {case.exposed for case in cases} == {False, True}
    assert {case.hard_stop for case in cases} == {None, "learner_preference", "machine_checks", "episode_conflict"}
    assert {case.path for case in cases} == {"plan", "no_plan", "no_room"}
    assert any(case.offer for case in cases) and any(case.recent for case in cases) and any(case.slip for case in cases)
    assert {case.hypotheses for case in cases} == {2, 3, 4, 6}
    assert len({case.name for case in cases}) == len(cases)
