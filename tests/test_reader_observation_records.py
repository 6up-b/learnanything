"""Reader workbench RW6a: the session's formative records (spec_reader_workbench_v1
§9.1, ``ReaderObservationV1``; gate G50; W1's tier 2).

One record per tier-2 signal, typed (never prose), copied from its row,
``authority: "routing_only"``. Today's only source is RW1a's reconnect *still
unclear*; RW1b's next-step / why-step / assumption misses and RW5a's missed
predictions have their builders ready and read nothing until those phases
write rows. Deterministic from the ledgers, and read by nothing that writes
evidence (an import-linter contract). Fakes only.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from learnloop.reader import reader_observations as RO
from learnloop.reader import reader_sessions as RS
from learnloop.reader import recap as RC
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import EXT, T0, ask, still_unclear, table_counts, visit
from tests.test_reader_dialogue import _setup

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PACKAGES = (
    "learnloop.substrate", "learnloop.learner", "learnloop.attempts", "learnloop.scheduling",
    "learnloop.goals", "learnloop.diagnosis", "learnloop.placement", "learnloop.field", "learnloop.router",
)
RECORD_MODULES = ("learnloop.reader.reader_observations", "learnloop.reader.reader_sessions",
                  "learnloop.reader.recap")


def _now(minutes):
    from datetime import timedelta

    return T0 + timedelta(minutes=minutes)


def _seed(tmp_path):
    vault, repo = _setup(tmp_path)
    visit(repo, "v1", 0, 30)
    root = ask(vault, repo, "Why are the densities weighted by p?", 2)
    answer = still_unclear(repo, root["reader_answer_event_id"], 5)
    follow_up = ask(vault, repo, "why does differentiating keep the weights?", 6,
                    parent=root["reader_answer_event_id"])
    return vault, repo, root, answer, follow_up


def _reconnect_event_id(repo) -> str:
    [event] = [e for e in repo.reader_interaction_events(kind="reader_action_invoked")
               if (e["payload"] or {}).get("event") == "reconnect_answered"]
    return str(event["id"])


def test_still_unclear_becomes_one_routing_only_record(tmp_path):
    vault, repo, root, _answer, _follow_up = _seed(tmp_path)
    session = RS.sessions_for_source(repo, EXT)[0]
    summary = RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now(100))
    [record] = summary["observations"]
    assert record["kind"] == "still_unclear"
    assert record["authority"] == "routing_only" == RO.ROUTING_ONLY
    assert record["source_event_ids"] == [_reconnect_event_id(repo)]
    assert record["span_ids"] == ["s1"]
    assert record["item_id"] is None and record["step_id"] is None
    assert record["observed"] == {"answer": "still_unclear", "via": "inline"}
    assert record["assistance"] == {"level": None, "reveal": False}
    assert record["root_exchange_id"] == root["reader_answer_event_id"]
    assert isinstance(record["facet_candidates"], list) and isinstance(record["hypotheses"], list)
    # Typed, never prose: the learner's words stay with learner-text gaps.
    assert "weighted" not in json.dumps(record) and "differentiating" not in json.dumps(record)


def test_records_are_deterministic_and_only_of_the_spec_kinds(tmp_path):
    vault, repo, *_rest = _seed(tmp_path)
    session = RS.sessions_for_source(repo, EXT)[0]
    first = RO.observations_for_session(vault, repo, extraction_id=EXT, session=session)
    again = RO.observations_for_session(load_vault(vault.root), type(repo)(repo.sqlite_path),
                                        extraction_id=EXT, session=RS.sessions_for_source(repo, EXT)[0])
    assert [r.as_dict() for r in first] == [r.as_dict() for r in again]
    assert RO.OBSERVATION_KINDS == (
        "still_unclear", "next_step_missed", "why_step_missed", "assumption_missed", "prediction_missed",
        "check_questionable", "hint_taken", "doesnt_connect", "discriminate_answer",
    )
    assert all(r.kind in RO.OBSERVATION_KINDS and r.authority == "routing_only" for r in first)


def test_a_record_outside_its_session_is_not_its_sessions(tmp_path):
    vault, repo, *_rest = _seed(tmp_path)
    visit(repo, "v2", 200, 230)
    later = RS.sessions_for_source(repo, EXT)[1]
    assert RO.observations_for_session(vault, repo, extraction_id=EXT, session=later) == []


def test_the_formative_builders_for_later_phases_read_nothing_today(tmp_path):
    vault, repo, *_rest = _seed(tmp_path)
    session = RS.sessions_for_source(repo, EXT)[0]
    # RW1b (next-step, why-step, assumption) and RW5a (predictions) add their
    # rows later; the reads exist and return nothing on today's schema.
    assert RO.formative_answer_observations(repo, extraction_id=EXT, session=session) == []
    assert RO.prediction_observations(repo, extraction_id=EXT, session=session) == []


def test_building_the_records_writes_nothing(tmp_path):
    vault, repo, *_rest = _seed(tmp_path)
    before = table_counts(repo)
    session = RS.sessions_for_source(repo, EXT)[0]
    RO.observations_for_session(vault, repo, extraction_id=EXT, session=session)
    RC.session_summary(vault, repo, extraction_id=EXT, session=session, now=_now(100))
    assert table_counts(repo) == before


def test_nothing_that_writes_evidence_reads_the_records():
    """G50: an import-linter contract, plus a direct scan for anyone naming them."""

    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    contracts = {c["id"]: c for c in config["tool"]["importlinter"]["contracts"]}
    contract = contracts["evidence-never-reads-reader-observations"]
    assert contract["type"] == "forbidden"
    assert set(EVIDENCE_PACKAGES) <= set(contract["source_modules"])
    assert set(RECORD_MODULES) <= set(contract["forbidden_modules"])
    assert contract.get("allow_indirect_imports") is False

    offenders = []
    for package in EVIDENCE_PACKAGES:
        directory = ROOT / "src" / Path(*package.split("."))
        for path in directory.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "ReaderObservationV1" in text or "reader_observations" in text or "reader.recap" in text:
                offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
