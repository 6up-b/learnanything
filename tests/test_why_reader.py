"""Refactor B9 (ADR-017): the one reader behind ``learnloop why``, ``why.get``, ``router trace`` and ``trace-evidence``.

* **Old rows answer, labelled.** Each of the four cases is staged as in ``tests/test_why_cases.py``, then the vault is
  aged to what a vault below migration 253 holds (no ``decision_records``, no ``trace_id`` on receipts). ``why``
  then answers from the rows themselves, every answer labelled ``reconstructed`` and its time-ordered fields named
  ``inferred``. Fail-first: before B9 a router decision id, an offer, a figure or ``--first-build`` on such a vault
  answered ``not_found`` (or had no option).
* **``why item:<id>`` degrades** instead of raising when a cold follow-up's stored context is malformed (B3's finding,
  main too): it names the bad row, never its content.
* **``why.get``** is registered, returns ids, numbers and codes only, never a payload, and is not on the phone's
  allowlist.
* **The views:** ``router trace`` and ``why`` name the same objective trace; ``trace-evidence`` and ``why attempt:``
  read the same observations.
* **The follow-up gate's late answers** are listed as discarded (B5's open item).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance
from learnloop.db.connection import connect
from learnloop.provenance import DecisionRecord
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.why import reader

from tests.helpers import create_basic_vault
from tests.test_ih2_lessons_compete import draw  # noqa: F401 - the fixture
from tests.test_te3b_offers import offerable  # noqa: F401 - the fixture
from tests.test_why_cases import of_kind, stage_case_1, stage_case_2, stage_case_3, stage_case_4, why

PLANTED = "the learner wrote about eigenvalues here"


def _sqlite(root: Path) -> Path:
    loaded = load_vault(root, load_environment=False)
    return VaultPaths(loaded.root, loaded.config).sqlite_path


def age(root: Path) -> None:
    """What a vault below migration 253 holds: no decision records, and no trace on any receipt."""

    with connect(_sqlite(root)) as connection:
        connection.execute("DROP TABLE decision_records")
        connection.execute("UPDATE model_call_receipts SET trace_id = NULL")
        connection.commit()


def why_exit(root: Path, *args: str) -> tuple[int, dict[str, Any]]:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", *args, "--json", "--vault", str(root)])
    return result.exit_code, json.loads(result.output)


def _only(payload: dict[str, Any], kind: str) -> dict[str, Any]:
    [found] = [item for item in payload["reconstructed"] if item["kind"] == kind]
    assert found["label"] == "reconstructed"
    return found


# -- the reconstructed reader, on the four cases aged below their records ------------------------------------------


def test_case_1_aged_the_timeout_and_the_late_answer_from_the_decision_row_and_its_receipts(tmp_path):
    root, trace = stage_case_1(tmp_path)
    [block] = of_kind(why(root, trace), "plan_block")[:1]
    decision_id = block["detail"]["id"]
    late_native = {entry["call_id"] for entry in block["discarded"]}
    # The app stamps the decision's row on the wall clock as it decides; this env's plan runs on a frozen clock, so
    # the row gets the moment its record took the models' answers, as a real row would hold.
    with connect(_sqlite(root)) as connection:
        for (trigger,) in connection.execute("SELECT name FROM sqlite_master WHERE type = 'trigger' AND "
                                             "tbl_name = 'router_decisions'").fetchall():
            connection.execute(f'DROP TRIGGER "{trigger}"')  # a test database: the ledger's append-only guard
        connection.execute("UPDATE router_decisions SET created_at = ? WHERE id = ?", (block["created_at"], decision_id))
        connection.commit()
    age(root)

    payload = why(root, decision_id)
    assert payload["source"] == "reconstructed" and payload["records"] == []
    answer = _only(payload, "plan_block")
    assert answer["row"] == {"table": "router_decisions", "id": decision_id}
    assert answer["chosen"] == block["chosen"] and answer["subject"] == block["subject"]
    assert answer["alternatives"] and all(alt["lost_by"] == "not_drawn" for alt in answer["alternatives"])
    [llm] = [component for component in answer["components"] if component["component"] == "llm"]
    assert llm["status"] == "timeout" and llm["decided_by"] == "router_llm"
    # The configured wait was never stored on old rows: said so, with the setting now beside it.
    inputs = answer["inputs"]
    assert inputs["timeout_s"] is None and inputs["timeout_s_basis"] == "not_stored" and inputs["timeout_s_now"] == 0.3
    assert inputs["waited_ms"] is not None and inputs["boundary_key"] == block["inputs"]["boundary_key"]
    assert answer["versions"]["seed"] and answer["versions"]["algorithm_version"]
    # Its receipts, joined by the boundary key (no trace): the late ones discarded, their output present.
    assert {call["owner_kind"] for call in answer["calls"]} == {"router_decision"}
    late = {entry["call_id"] for entry in answer["discarded"]}
    assert late and late == late_native and all(entry["late_ms"] > 0 for entry in answer["discarded"])
    # The router call's receipt holds the late answer; a call whose output is absent says why.
    assert any(entry["output"] == "present" for entry in answer["discarded"])
    assert all(call["output_absent_reason"] for call in answer["calls"] if call["output"] == "absent")
    assert "discarded" in answer["inferred"]
    assert PLANTED not in json.dumps(payload)
    # The same decision through its block, and as the latest.
    assert _only(why(root, f"block:{block['subject'].split(':', 1)[1]}"), "plan_block")["row"]["id"] == decision_id
    assert why(root)["reconstructed"]


@pytest.mark.usefixtures("offerable")
def test_case_2_aged_the_expired_row_its_forced_probe_and_the_next_decision_inferred(tmp_path, draw):
    root, step, workflow = stage_case_2(tmp_path, draw)
    offer_decision = step["offer"]["decision_id"]
    age(root)

    payload = why(root, f"offer:{offer_decision}")
    answer = _only(payload, "offer_withdrawn")
    assert (answer["status"], answer["rule"], answer["decided_by"]) == ("withdrawn", "forced_items", "plan")
    assert answer["parent"] == {"table": "router_decisions", "id": offer_decision}
    assert answer["row"]["table"] == "router_suggestion_responses"
    [forced] = answer["alternatives"]
    assert forced["ref"] == workflow["practice_item_id"] and forced["workflow"] == workflow["id"]
    assert forced["source_attempt"] == workflow["source_attempt_id"]
    assert answer["next"]["next_decision"]["decision_id"]
    assert {"alternatives", "inputs.forced", "next.next_decision"} <= set(answer["inferred"])
    # The offer's own decision answers beside it, with the expired response as what came next.
    drawn = _only(payload, "plan_block")
    assert drawn["row"]["id"] == offer_decision
    assert [response["withdrawn"] for response in drawn["next"]["responses"]] == ["forced_items"]


def test_case_3_aged_the_failed_figure_its_typed_codes_and_its_author_calls(tmp_path):
    from tests.figure_fixtures import half_density

    root, shown = stage_case_3(tmp_path, [half_density(), half_density()])
    age(root)
    answer = _only(why(root, f"figure:{shown['figureId']}"), "figure_author")
    assert answer["status"] == "failed" and answer["row"] == {"table": "interactive_figures", "id": shown["figureId"]}
    assert answer["rule"] in {"verification_failed", "prediction_invalid", "spec_invalid"}
    assert answer["inputs"]["problems"] and all(provenance.is_code(code) for code in answer["inputs"]["problems"])
    assert answer["versions"]["prompt_version"].startswith("figure_author")
    assert answer["versions"]["model"] == "fake-figure-model"
    assert answer["inputs"]["origin"] and answer["inputs"]["request_id"]


def test_reconstructed_problem_codes_name_a_bad_prediction_and_its_schema_path():
    from learnloop.why import reconstructed as R

    assert R.problem_code("predictions.0.change.param: Input should be a valid string") == R.PREDICTION_INVALID
    assert R.problem_code("prediction 2: changes 'q', which is not a parameter") == R.PREDICTION_INVALID
    assert R.problem_code("invariant 1: the density does not integrate to one") == R.VERIFICATION_FAILED
    assert R.problem_code("panels: at least one panel") == R.SPEC_INVALID
    assert R.problem_path("predictions.0.change.param: Input should be a valid string") == "predictions.0.change.param"
    assert R.problem_path("prediction 2: changes q") is None


def test_case_4_aged_first_build_counts_the_skips_and_places_the_measurement_between(tmp_path):
    root, skips, measured = stage_case_4(tmp_path)
    age(root)
    payload = why(root, "--first-build")
    built = payload["first_build"]
    assert built["label"] == "reconstructed" and built["skips_before_first_build"] == len(skips) == 2
    assert built["by_trigger_kind"]["offer"]["skips_before_first_non_skip"] == 2
    assert built["last_skip"]["verdict"] == "skip" and built["first_build"]["verdict"] == "build"
    assert built["changed"]["sampled_eu"][0] is None and built["changed"]["sampled_eu"][1] > 0
    assert built["first_measurement"]["row"] == {"table": "model_call_receipts", "id": measured}
    assert built["measurement_between"] is True and "measurement_between" in built["inferred"]
    # One pre-build decision as an old row: a skip with no EU is the one before any measured latency.
    skip = _only(why(root, f"decision:{skips[0]['id']}"), "figure_prebuild")
    assert skip["status"] == "excluded" and skip["rule"] == "no_measured_latency" and "rule" in skip["inferred"]
    assert skip["versions"]["seed"] is None and skip["versions"]["seed_basis"] == "not_stored"


def test_a_record_answers_natively_and_nothing_is_reconstructed_beside_it(tmp_path):
    root, trace = stage_case_1(tmp_path)
    payload = why(root, trace)
    assert payload["source"] == "decision_records" and payload["reconstructed"] == []
    assert all(decision["label"] == "native" for decision in payload["decisions"])
    decision_id = of_kind(payload, "plan_block")[0]["detail"]["id"]
    # A router decision with its record answers through it (its trace), not the old-row reader.
    assert why(root, f"block:{of_kind(payload, 'plan_block')[0]['subject'].split(':', 1)[1]}")["reconstructed"] == []
    assert decision_id


def test_an_unknown_target_is_still_not_found(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    code, payload = why_exit(paths.root, "no_such_thing")
    assert code == 1 and payload["error"] == "not_found"


# -- why item:<id> degrades on a malformed stored row --------------------------------------------------------------


def test_why_item_names_a_malformed_follow_up_row_instead_of_raising(tmp_path):
    """Fail-first: on main ``why item:<id>`` exits 1 with ``JSONDecodeError`` (B3's finding)."""

    from tests.ad23_fakes import cold_followup

    paths = create_basic_vault(tmp_path / "vault")
    task = cold_followup(paths, "pi_svd_define_001", context_json='{"note": "' + PLANTED + ' unterminated')
    code, payload = why_exit(paths.root, "item:pi_svd_define_001")
    assert code == 0, payload
    assert payload["source"] == "unavailable" and payload["practice_item_id"] == "pi_svd_define_001"
    error = payload["explanation_error"]
    assert error["type"] == "JSONDecodeError" and error["where"]
    assert {"table": "followup_tasks", "id": task, "column": "context_json"} in error["bad_rows"]
    assert "records" in payload and "slates" in payload
    assert PLANTED not in json.dumps(payload)


# -- why.get: the glass-box view's RPC ------------------------------------------------------------------------------


def _rpc(ctx: Any, name: str, params: dict[str, Any]) -> Any:
    import learnloop_sidecar.handlers  # noqa: F401 - populate METHOD_REGISTRY
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_why_get_returns_ids_numbers_and_codes_and_never_a_payload(tmp_path):
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.errors import SidecarError

    root, trace = stage_case_1(tmp_path)
    with connect(_sqlite(root)) as connection:
        planted = connection.execute("SELECT input_text, output_text FROM model_call_receipts WHERE trace_id = ? "
                                     "AND input_text IS NOT NULL LIMIT 1", (trace,)).fetchone()
    ctx = SidecarContext()
    ctx.load(root)
    reply = _rpc(ctx, "why.get", {"target": trace})
    body = json.dumps(reply)
    assert reply["why"]["source"] == "decision_records" and reply["why"]["decisions"]
    assert "payloads" not in reply["why"]
    assert planted[0]
    for text in planted:
        assert not text or text not in body
    _cleaned, withheld = reader.codes_only(reply["why"])
    assert withheld == []
    first = _rpc(ctx, "why.get", {"target": "latest", "firstBuild": True})
    assert "first_build" in first["why"]
    with pytest.raises(SidecarError):
        _rpc(ctx, "why.get", {"target": "no_such_thing"})


def test_why_get_withholds_an_items_reasons_and_says_where(tmp_path):
    from learnloop_sidecar.context import SidecarContext

    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    reply = _rpc(ctx, "why.get", {"target": "pi_svd_define_001"})
    assert reply["why"]["source"] == "current" and reply["why"]["practice_item_id"] == "pi_svd_define_001"
    assert reply["why"]["reasons"] and all(reason is None for reason in reply["why"]["reasons"])
    assert reply["withheld"] and all(path.startswith("reasons[") for path in reply["withheld"])


def test_why_get_is_registered_desktop_only_and_never_phone_allowed():
    import learnloop_sidecar.handlers  # noqa: F401 - populate METHOD_REGISTRY
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.why import WHY_RPCS
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert WHY_RPCS == ("why.get",)
    for name in WHY_RPCS:
        assert name in METHOD_REGISTRY and name not in ALLOWLIST


def test_the_phone_host_refuses_why_get(tmp_path):
    from learnloop_mobile.allowlist import validate_envelope

    name = validate_envelope({"method": "why.get", "params": {}})["method"]
    from learnloop_mobile.allowlist import ALLOWLIST

    assert name not in ALLOWLIST


def test_the_rpc_never_reads_payloads():
    source = Path(__file__).resolve().parents[1].joinpath("src/learnloop_sidecar/handlers/why.py").read_text()
    assert "payloads" not in source and "input_text" not in source and "output_text" not in source


def test_codes_only_keeps_ids_numbers_codes_and_times_and_names_what_it_drops():
    cleaned, withheld = reader.codes_only({
        "id": "01ABC", "at": "2026-11-08T18:09:10+00:00", "n": 3, "p": 0.5, "ok": True, "none": None,
        "reasons": ["This item is due because you missed it."], "nested": [{"rule": "forced_items"}],
        "a key with spaces": 1,
    })
    assert cleaned == {"id": "01ABC", "at": "2026-11-08T18:09:10+00:00", "n": 3, "p": 0.5, "ok": True, "none": None,
                       "reasons": [None], "nested": [{"rule": "forced_items"}]}
    assert withheld == ["reasons[0]", ".<key>"]


# -- the views: router trace and trace-evidence read through the same reader ---------------------------------------


def test_router_trace_and_why_name_the_same_objective_trace(tmp_path):
    from learnloop.cli import app

    root, trace = stage_case_1(tmp_path)
    block = of_kind(why(root, trace), "plan_block")[0]
    pointer = block["objective_trace"]
    assert pointer and pointer["decision_id"] == block["detail"]["id"]
    result = CliRunner().invoke(app, ["router", "trace", block["detail"]["id"], "--json", "--vault", str(root)])
    assert result.exit_code == 0, result.output
    shown = json.loads(result.output)
    assert shown["content_hash"] == pointer["content_hash"] and shown["trace_version"] == pointer["trace_version"]
    missing = CliRunner().invoke(app, ["router", "trace", "no_such_decision", "--json", "--vault", str(root)])
    assert missing.exit_code == 1 and json.loads(missing.output)["status"] == "invalid"


def test_trace_evidence_and_why_attempt_read_the_same_observations(tmp_path):
    from learnloop.cli import app

    paths = create_basic_vault(tmp_path / "vault")
    runner = CliRunner()
    attempt = runner.invoke(app, ["attempt", "pi_svd_define_001", "--vault", str(paths.root), "--answer", "U S V^T",
                                  "--criterion-points", "correctness=4", "--confidence", "5", "--json"])
    assert attempt.exit_code == 0, attempt.output
    attempt_id = json.loads(attempt.output)["attempt"]["attempt_id"]
    with connect(paths.sqlite_path) as connection:
        for index, (facet, scope) in enumerate((("f_a", "opportunistic"), ("f_b", "declared"))):
            connection.execute(
                "INSERT INTO trace_exercised_facets (id, attempt_id, facet_id, observation_scope, evidence, source, "
                "created_at) VALUES (?, ?, ?, ?, ?, 'grader_trace', '2026-11-10T10:00:00+00:00')",
                (f"tef_{index}", attempt_id, facet, scope, PLANTED))
        connection.commit()
    report = runner.invoke(app, ["trace-evidence", "--json", "--vault", str(paths.root)])
    assert report.exit_code == 0, report.output
    payload = json.loads(report.output)
    assert set(payload) == {"version", "attempts_with_observations", "declared_observations",
                            "opportunistic_observations", "distinct_opportunistic_facets",
                            "opportunistic_concentration", "top_opportunistic_facets", "unexercised_supporting_cells",
                            "unexercised_supporting_cell_count"}
    assert (payload["declared_observations"], payload["opportunistic_observations"]) == (1, 1)
    evidence = why(paths.root, f"attempt:{attempt_id}")["evidence"]
    assert [(row["facet_id"], row["observation_scope"]) for row in evidence] == [("f_a", "opportunistic"),
                                                                                  ("f_b", "declared")]
    assert PLANTED not in json.dumps(evidence)


# -- B5's open item: the follow-up gate's late answers --------------------------------------------------------------


def test_a_follow_up_gate_call_that_answered_after_the_gate_is_discarded(tmp_path):
    """Fail-first: before B9 only ``plan_block`` was a late-answer kind, so the gate's late call was not listed."""

    paths = create_basic_vault(tmp_path / "vault")
    with connect(paths.sqlite_path) as connection:
        with provenance.trace_scope("TRACE_GATE"):
            gate = provenance.write(connection, DecisionRecord(
                kind="followup_gate", status="chosen", decided_by="mixture", rule="drawn_llm",
                subject_kind="attempt", subject_id="att_1", facts={"boundary_key": "bk_gate", "workflow_id": "fw_1"},
                created_at="2026-11-10T10:00:05+00:00"))
        for call_id, finished in (("call_on_time", "2026-11-10T10:00:04+00:00"),
                                  ("call_late", "2026-11-10T10:00:09+00:00")):
            connection.execute(
                "INSERT INTO model_call_receipts (id, purpose, owner_kind, owner_id, status, started_at, finished_at, "
                "trace_id) VALUES (?, 'router_decision', 'router_decision', 'bk_gate', 'completed', "
                "'2026-11-10T10:00:00+00:00', ?, 'TRACE_GATE')", (call_id, finished))
        connection.commit()
    payload = why(paths.root, "TRACE_GATE")
    assert [(entry["record_id"], entry["call_id"], entry["late_ms"]) for entry in payload["discarded"]] == [
        (gate, "call_late", 4000)]
    [decision] = payload["decisions"]
    assert [entry["call_id"] for entry in decision["discarded"]] == ["call_late"]


def test_why_is_still_a_pure_read_with_the_new_options(tmp_path, monkeypatch):
    import hashlib
    import importlib

    cli_app = importlib.import_module("learnloop.cli.app")
    paths = create_basic_vault(tmp_path / "vault")
    assert CliRunner().invoke(cli_app.app, ["review", "--json", "--vault", str(paths.root)]).exit_code == 0

    def refused(*_args, **_kwargs):
        raise AssertionError("why wrote to the vault")

    monkeypatch.setattr(cli_app, "sync_vault_state", refused)
    monkeypatch.setattr(cli_app, "run_startup_maintenance", refused)

    def digest() -> str:
        out = hashlib.sha256()
        with connect(paths.sqlite_path, read_only=True) as connection:
            for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                for row in sorted(repr(tuple(row)) for row in connection.execute(f'SELECT * FROM "{table}"')):
                    out.update(row.encode())
        return out.hexdigest()

    before = digest()
    for args in (["--first-build"], ["latest", "--payload"], ["item:pi_svd_define_001"], ["block:none"]):
        result = CliRunner().invoke(cli_app.app, ["why", *args, "--json", "--vault", str(paths.root)])
        assert result.exit_code == 0, result.output
    assert digest() == before


# -- B8's subjects: goals and lessons ------------------------------------------------------------------------------


@pytest.mark.parametrize(("subject_kind", "kind"), [("goal", "curriculum_path_refresh"),
                                                    ("lesson", "spend_admission")])
def test_why_resolves_goal_and_lesson_subjects(tmp_path, subject_kind, kind):
    """Fail-first: before ``goal`` and ``lesson`` were subject kinds, ``why goal:<id>`` was read as a trace id and
    answered ``not_found`` (B8 writes records about both)."""

    paths = create_basic_vault(tmp_path / "vault")
    with connect(paths.sqlite_path) as connection:
        with provenance.trace_scope(f"TRACE_{subject_kind.upper()}"):
            written = provenance.write(connection, DecisionRecord(
                kind=kind, status="chosen", decided_by="test", rule="refreshed", subject_kind=subject_kind,
                subject_id=f"{subject_kind}_1"))
        connection.commit()
    assert subject_kind in provenance.SUBJECT_KINDS
    payload = why(paths.root, f"{subject_kind}:{subject_kind}_1")
    assert [record["id"] for record in payload["records"]] == [written]
    [decision] = payload["decisions"]
    assert decision["subject"] == f"{subject_kind}:{subject_kind}_1" and decision["kind"] == kind
    assert payload["reconstructed"] == []
    code, missing = why_exit(paths.root, f"{subject_kind}:no_such_{subject_kind}")
    assert code == 0 and missing["records"] == []
