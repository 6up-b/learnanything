"""Refactor B9 (strategy §3.6, test 2): the owner's four real cases, read by ``why`` from a backup taken after Nov 8.

The four events happened before their decision records existed, so on such a backup ``why`` answers from the rows
they left, through the reader labelled ``reconstructed`` (``learnloop.why.reconstructed``). Each case is found by its
date and shape on ``arxiv_v2`` and read back through ``learnloop why --json`` alone:

1. a Nov 7-8 ``router_decisions`` row whose LLM answer timed out: its receipts joined through the boundary key, each
   with its output present or the reason it's absent, and the late ones listed as discarded;
2. the Nov 8 ``expired`` response with ``forced_items``: the forced items, the next decision and the workflow rows,
   labelled inferred;
3. a Nov 8 ``interactive_figures`` row with ``verification = 'failed'``: its typed reason and its call rows;
4. the pre-build decisions: the skips before the first non-skip, per trigger kind, and the first measured latency.
   The test reports whether the count is 12 and whether the measurement falls between (the strategy's hypothesis);
   it does not fail on either, because the answer is for the owner.

A later backup, taken after these boundaries have written native records, finds those instead, and each case then
asserts the answer carries no ``reconstructed`` label.

Run it only on backup-API copies (``tests/owner_vaults.py``); never on a live vault. A failure prints ids and field
names only: ``why --json`` holds ids, numbers and codes, never a payload, and nothing here is written to a file.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance
from tests.owner_vaults import owner_vault, owner_vaults

pytestmark = owner_vaults

VAULT = owner_vault("arxiv_v2")
CASE_DAYS = ("2026-11-07", "2026-11-09")  # Nov 7 and 8, as ISO bounds


def why(*args: str) -> dict[str, Any]:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", *args, "--json", "--vault", str(VAULT)])
    assert result.exit_code == 0, f"why {' '.join(args)} exited {result.exit_code}"
    return json.loads(result.output)


def _rows(sql: str, args: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    loaded = load_vault(VAULT, load_environment=False)
    path = VaultPaths(loaded.root, loaded.config).sqlite_path
    with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as connection:
        try:
            return connection.execute(sql, args).fetchall()
        except sqlite3.OperationalError as exc:
            pytest.fail(f"the backup lacks a table or column the case reads: {type(exc).__name__}")


def _native(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [decision for decision in payload.get("decisions") or () if decision["kind"] == kind]


def _rebuilt(payload: dict[str, Any], kind: str, row_id: str) -> dict[str, Any]:
    found = [item for item in payload["reconstructed"] if item["kind"] == kind]
    assert found, f"no reconstructed {kind} for {row_id}"
    assert all(item["label"] == "reconstructed" for item in found), f"{kind} for {row_id}: label"
    return found[0]


def _codes_only(payload: dict[str, Any], where: str) -> None:
    cleaned, withheld = __import__("learnloop.why.reader", fromlist=["codes_only"]).codes_only(payload)
    assert not withheld, f"{where}: fields holding text: {withheld}"


def test_case_1_the_router_llm_answer_discarded_by_the_timeout():
    found = _rows("SELECT id FROM router_decisions WHERE created_at >= ? AND created_at < ? AND "
                  "json_extract(detail_json, '$.mixture.models.llm.status') = 'timeout' ORDER BY created_at, id",
                  CASE_DAYS)
    assert found, "no router decision with an LLM timeout on Nov 7-8"
    decision_id = str(found[0][0])
    payload = why(decision_id)
    _codes_only(payload, f"case 1 {decision_id}")
    native = _native(payload, "plan_block")
    if native:  # a later backup: the record answers
        assert payload["reconstructed"] == [], f"case 1 {decision_id}: native and reconstructed"
        assert native[0]["inputs"].get("timeout_s") is not None, f"case 1 {decision_id}: inputs.timeout_s"
        return
    answer = _rebuilt(payload, "plan_block", decision_id)
    assert answer["row"]["id"] == decision_id, f"case 1 {decision_id}: row.id"
    llm = [component for component in answer["components"] if component["component"] == "llm"]
    assert llm and llm[0]["status"] == "timeout", f"case 1 {decision_id}: components.llm.status"
    assert answer["inputs"]["boundary_key"], f"case 1 {decision_id}: inputs.boundary_key"
    assert answer["inputs"]["timeout_s_basis"] == "not_stored", f"case 1 {decision_id}: inputs.timeout_s_basis"
    assert answer["calls"], f"case 1 {decision_id}: calls (joined through the boundary key)"
    for call in answer["calls"]:
        assert call["output"] == "present" or call["output_absent_reason"], \
            f"case 1 {decision_id}: call {call['call_id']} output_absent_reason"
    assert answer["discarded"], f"case 1 {decision_id}: discarded"
    assert all(entry["late_ms"] is None or entry["late_ms"] > 0 for entry in answer["discarded"]), \
        f"case 1 {decision_id}: discarded.late_ms"
    assert "discarded" in answer["inferred"], f"case 1 {decision_id}: inferred"
    print(f"case 1: decision {decision_id}; calls {len(answer['calls'])}; discarded "
          f"{[(entry['call_id'], entry['late_ms'], entry['output']) for entry in answer['discarded']]}")


def test_case_2_the_offer_withdrawn_with_forced_items():
    found = _rows("SELECT decision_id, id FROM router_suggestion_responses WHERE response = 'expired' AND "
                  "json_extract(detail_json, '$.withdrawn') = 'forced_items' AND responded_at >= ? AND "
                  "responded_at < ? ORDER BY responded_at, id", ("2026-11-08", CASE_DAYS[1]))
    assert found, "no expired response with forced_items on Nov 8"
    decision_id, response_id = (str(value) for value in found[0])
    payload = why(f"offer:{decision_id}")
    _codes_only(payload, f"case 2 {decision_id}")
    native = _native(payload, "offer_withdrawn")
    if native:
        assert payload["reconstructed"] == [], f"case 2 {decision_id}: native and reconstructed"
        assert native[0]["rule"] == "forced_items" and native[0]["alternatives"], f"case 2 {decision_id}: alternatives"
        return
    answer = _rebuilt(payload, "offer_withdrawn", decision_id)
    assert answer["row"] == {"table": "router_suggestion_responses", "id": response_id}, f"case 2 {response_id}: row"
    assert (answer["status"], answer["rule"]) == ("withdrawn", "forced_items"), f"case 2 {response_id}: status, rule"
    assert answer["parent"] == {"table": "router_decisions", "id": decision_id}, f"case 2 {response_id}: parent"
    assert answer["next"].get("next_decision"), f"case 2 {response_id}: next.next_decision"
    assert answer["alternatives"], f"case 2 {response_id}: alternatives (the forced items)"
    for name in ("alternatives", "inputs.forced", "inputs.workflows", "next.next_decision"):
        assert name in answer["inferred"], f"case 2 {response_id}: inferred {name}"
    inputs = answer["inputs"]
    print(f"case 2: offer {decision_id}, response {response_id}; forced {inputs['forced']}; workflows "
          f"{inputs['workflows']}; source attempts {inputs['source_attempts']}; opened "
          f"{[(row['workflow'], row['state'], row['source_attempt']) for row in inputs['opened_between']]}; generated "
          f"{[(row['job'], row['kind'], row['need']) for row in inputs['generated_between']]}; alternatives "
          f"{answer['alternatives']}; next {answer['next']['next_decision']['decision_id']}")


def test_case_3_the_figure_stored_failed():
    found = _rows("SELECT id FROM interactive_figures WHERE verification = 'failed' AND created_at >= ? AND "
                  "created_at < ? ORDER BY created_at, id", ("2026-11-08", CASE_DAYS[1]))
    assert found, "no failed figure on Nov 8"
    rules = []
    for (figure_id,) in found:
        payload = why(f"figure:{figure_id}")
        _codes_only(payload, f"case 3 {figure_id}")
        native = _native(payload, "figure_author")
        if native:
            assert payload["reconstructed"] == [], f"case 3 {figure_id}: native and reconstructed"
            rules.append(native[-1]["rule"])
            continue
        answer = _rebuilt(payload, "figure_author", str(figure_id))
        assert answer["status"] == "failed", f"case 3 {figure_id}: status"
        assert answer["rule"] and provenance.is_code(answer["rule"]), f"case 3 {figure_id}: rule"
        assert answer["inputs"]["problems"], f"case 3 {figure_id}: inputs.problems"
        assert answer["versions"]["prompt_version"] and answer["versions"]["model"], f"case 3 {figure_id}: versions"
        assert answer["calls"], f"case 3 {figure_id}: calls"
        rules.append(answer["rule"])
        if len(rules) == 1:
            print(f"case 3: figure {figure_id}; rule {answer['rule']}; problems {answer['inputs']['problems']}; paths "
                  f"{answer['inputs']['problem_paths']}; author calls {answer['inputs']['author_calls_n']}; calls "
                  f"{[(call['call_id'], call['purpose'], call['status']) for call in answer['calls']]}")
    print(f"case 3: {len(found)} failed figures; rules {sorted(set(rules))}; prediction_invalid "
          f"{rules.count('prediction_invalid')}")


def test_case_4_prebuilds_after_a_run_of_skips():
    payload = why("--kind", "figure_prebuild", "--first-build")
    _codes_only(payload, "case 4")
    built = payload["first_build"]
    assert built, "no pre-build decisions"
    if built["label"] == "native":
        assert built["last_skip"] and built["first_build"], "case 4: last_skip, first_build"
        return
    assert built["label"] == "reconstructed", "case 4: label"
    for name in ("skips_before_first_build", "skips_before_first_non_skip", "by_trigger_kind", "first_measurement",
                 "measurement_between", "last_skip", "first_build"):
        assert name in built, f"case 4: {name}"
    count = built["skips_before_first_non_skip"]
    report = {
        "skips_before_first_non_skip": count, "is_12": count == 12,
        "skips_before_first_build": built["skips_before_first_build"],
        "by_trigger_kind": {kind: value["skips_before_first_non_skip"] for kind, value in built["by_trigger_kind"].items()},
        "first_measurement": {"kind": built["first_measurement"]["kind"], "at": built["first_measurement"]["at"],
                              "row": built["first_measurement"]["row"]} if built["first_measurement"] else None,
        "last_skip_at": built["last_skip"]["created_at"] if built["last_skip"] else None,
        "first_build_at": built["first_build"]["created_at"] if built["first_build"] else None,
        "measurement_between": built["measurement_between"],
        "changed": sorted(built["changed"]),
    }
    print("case 4:", json.dumps(report, sort_keys=True))


@pytest.mark.parametrize("name", ("linear_algebra", "probability"))
def test_the_other_vaults_answer_latest_without_error(name):
    """The reader runs on every working vault copy: ``latest`` answers or says nothing, never raises."""

    from learnloop.cli import app

    vault = owner_vault(name)
    if not Path(vault).is_dir():
        pytest.skip(f"no {name} copy in the lane")
    result = CliRunner().invoke(app, ["why", "--json", "--vault", str(vault)])
    assert result.exit_code == 0, f"why latest on {name} exited {result.exit_code}"
