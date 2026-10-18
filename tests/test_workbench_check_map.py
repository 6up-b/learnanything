"""Reader workbench RW2b + hints H3: "Check my work" reads the approach map (spec_reader_workbench_v1 §5.2; G38).

For each step the check marks valid, it names the map node and route the step
reaches, validated against the map by the hint service (an unknown node is
dropped; a valid step on no route is ``new_route``). The map's nodes never
reach the learner (they contain the solution): the check's view carries no
node. With ``hints.maps.enabled`` off the check names none. Fakes only.
"""

from __future__ import annotations

import json

from tests.workbench_help_fakes import CheckFake, call, check_answer, help_rows, open_problem, run_job, sidecar


def _verdicts(paths, wb):
    [row] = [row for row in help_rows(paths, wb) if row["assist_kind"] == "check"]
    return json.loads(row["step_verdicts_json"])


def test_a_valid_step_is_placed_on_the_node_and_route_it_reaches(tmp_path):
    paths, ctx, _session = sidecar(tmp_path)
    wb, chains = open_problem(ctx)
    result = run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    first, second = _verdicts(paths, wb)
    assert (first["chain_id"], first["map_node_id"], first["route_id"]) == (chains[0], "cdf", "r_ref")
    # A questionable step is never placed.
    assert (second["map_node_id"], second["route_id"]) == (None, None)
    # Nothing new is shown: the learner's view has no node or route.
    assert "cdf" not in json.dumps(result["check"]) and "r_ref" not in json.dumps(result["check"])


def test_an_unknown_node_is_dropped_and_a_valid_step_off_the_map_is_a_new_route(tmp_path):
    def answer(context):
        payload = check_answer(context)
        payload["steps"][0]["map"] = {"node_id": "nowhere", "route_id": "r_ref"}
        payload["steps"][1] = {**payload["steps"][1], "verdict": "valid", "map": {"node_id": "", "route_id": "new_route"}}
        return payload

    paths, ctx, _session = sidecar(tmp_path, check=CheckFake([answer]))
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    first, second = _verdicts(paths, wb)
    assert (first["map_node_id"], first["route_id"]) == (None, None)
    assert (second["map_node_id"], second["route_id"]) == (None, "new_route")


def test_with_the_maps_off_the_check_names_no_node_and_sends_no_map(tmp_path):
    fake = CheckFake()
    paths, ctx, _session = sidecar(tmp_path, check=fake, map_=False, maps_enabled=False)
    wb, _chains = open_problem(ctx)
    run_job(ctx, call(ctx, "workbench.check", {"sessionId": wb}))
    assert fake.contexts[0]["approach_map"] is None
    assert all(entry["map_node_id"] is None for entry in _verdicts(paths, wb))
