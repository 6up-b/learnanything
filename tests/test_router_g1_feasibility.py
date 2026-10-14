"""Router R2a gate G1 (constraints): an infeasible candidate can never be served.

The staged frame (``staged_frame_v1``) runs the P4 constraint engine over every
item of Today's pool against one bounded controller snapshot per boundary and
drops an item a hard constraint refuses before DL1's packing, logging the
refusal on the ``plan_block`` row under ``exclusions_json.named.<constraint>``.
The engine's closed-choice guard stays the backstop: a chooser naming an
unknown or infeasible id falls back to ``lane_quota_v1`` (DL1 rule 2).

Fail-first (plan §9 R2a, item 3): a diagnostic probe whose surface the learner
has already seen (an exact exposure in the one exposure ledger) is served in a
DL1 block today; under R2a it is refused with its named reason.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from learnloop.daily_plan.engine import DEFAULT_POLICY, advance, build_plan, decide
from learnloop.daily_plan.types import BlockChoice
from learnloop.substrate.activities import open_administration, resolve_legacy_item
from learnloop.vault.loader import load_vault

from tests.daily_plan_fakes import MovableClock, make_env, scheduled, seed_due
from tests.helpers import NOW_ISO, append_config_toml, create_daily_plan_vault, write_yaml

PAST = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
LAST = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)
PROBE = "pi_probe_seen"


def _probe_item(paths, item_id: str, lo_id: str = "lo_m1") -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1, "id": item_id, "learning_object_id": lo_id, "subjects": None,
            "practice_mode": "diagnostic_probe", "attempt_types_allowed": ["diagnostic_probe"],
            "evidence_facets": ["recall"], "evidence_weights": {"recall": 1.0},
            "prompt": f"Probe {item_id}.", "expected_answer": "It.", "difficulty": 0.4, "tags": [],
            "expected_minutes": 1.5,
            "grading_rubric": {"max_points": 1, "criteria": [{"id": "c1", "points": 1, "description": "Right."}]},
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO, "updated_at": NOW_ISO,
        },
    )


def _world(tmp_path, *, version: str, toml: str | None = None, seen: bool = True):
    paths = create_daily_plan_vault(
        tmp_path / "vault", learning_objects={"lo_m1": [("pi_m1a", 2.0), ("pi_m1b", 2.0)]}, version=version,
    )
    _probe_item(paths, PROBE)
    if toml:
        append_config_toml(paths.root, toml)
    items = [
        scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6),
        scheduled(PROBE, "lo_m1", forgetting_risk=0.6),
        scheduled("pi_m1b", "lo_m1", forgetting_risk=0.6),
    ]
    env = make_env(paths.root, items, clock=MovableClock(), session_id="s1")
    for item in ("pi_m1a", "pi_m1b", PROBE):
        seed_due(env.repository, item, due=PAST, last=LAST)
    if seen:
        # The same question was rendered before (as ordinary practice): its
        # surface is in the one exposure ledger, so it is not fresh evidence.
        vault = load_vault(paths.root)
        resolved = resolve_legacy_item(vault, env.repository, vault.practice_items[PROBE], purpose="practice")
        open_administration(env.repository, resolved=resolved)
    return env


def _planned(record) -> list[str]:
    return [item.practice_item_id for block in record.blocks for item in block.items]


def _plan_block_rows(env) -> list[dict]:
    with env.repository.connection() as connection:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM router_decisions WHERE decision_kind = 'plan_block' ORDER BY created_at, id"
        )]
    for row in rows:
        row["exclusions_json"] = json.loads(row["exclusions_json"])
        row["candidates_json"] = json.loads(row["candidates_json"])
    return rows


def test_a_seen_probe_is_served_by_dl1_and_refused_by_the_staged_frame(tmp_path):
    # Today (DL1's pair): the seen probe is planned in the maintain block.
    dl1 = _world(tmp_path / "dl1", version="mvp-0.22")
    assert dl1.policy is DEFAULT_POLICY
    record = build_plan(dl1, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert PROBE in _planned(record)

    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.daily_plan.policy import policy_for

    env = _world(tmp_path / "r2a", version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert PROBE not in _planned(record)
    assert {"pi_m1a", "pi_m1b"} <= set(_planned(record))
    [row] = _plan_block_rows(env)
    assert row["exclusions_json"]["named"]["hard_exposure_collision"] == [PROBE]
    assert (row["mode"], row["policy"]) == ("staged", "staged_v1")
    frame = json.loads(row["detail_json"])["staged_frame"]
    [refusal] = frame["refused"][PROBE]
    assert (refusal["constraint_key"], refusal["reason"]) == ("hard_exposure_collision", "exact_surface_collision")


def test_an_unseen_probe_stays_in_the_plan(tmp_path):
    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.daily_plan.policy import policy_for

    env = _world(tmp_path, version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION, seen=False)
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert PROBE in _planned(record)
    [row] = _plan_block_rows(env)
    assert "hard_exposure_collision" not in row["exclusions_json"].get("named", {})


def test_a_reserved_assessment_surface_is_refused_on_today(tmp_path):
    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.daily_plan.policy import policy_for
    from learnloop.substrate.activities import reserve_surface

    env = _world(tmp_path, version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION, seen=False)
    vault = load_vault(env.vault.root)
    resolved = resolve_legacy_item(vault, env.repository, vault.practice_items["pi_m1b"], purpose="assessment")
    reserve_surface(env.repository, surface_id=resolved.surface_id, purpose="assessment")
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert "pi_m1b" not in _planned(record)
    [row] = _plan_block_rows(env)
    assert row["exclusions_json"]["named"]["assessment_reservation"] == ["pi_m1b"]


def test_a_chooser_naming_an_infeasible_or_unknown_id_falls_back(tmp_path):
    """The container's closed choice is G1's backstop under any chooser."""

    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.daily_plan.policy import policy_for

    env = _world(tmp_path, version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock)

    class Rogue:
        name = "rogue"

        def choose(self, state, feasible):
            return BlockChoice(candidate_id="maintain:not-a-candidate", chosen_by="staged", propensity=1.0,
                               why="", why_kind="computed")

    from dataclasses import replace

    env.policy = replace(policy, chooser=Rogue())
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    [block] = record.blocks
    assert block.chosen["fallback"] is True and block.chosen["fallback_reason"] == "not_offered"
    assert PROBE not in _planned(record)  # the frame's refusal holds under the fallback too


def test_the_staged_frame_keeps_refusals_through_the_projection(tmp_path):
    """The view's projected blocks use the same source, so a refused item is
    never projected either (the projection chooser stays lane_quota_v1)."""

    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.daily_plan.policy import policy_for

    env = _world(tmp_path, version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock)
    assert env.policy.projection_chooser.name == "lane_quota_v1"
    record = build_plan(env, kind="normal", budget=40.0, remembered=40, minutes_source="chip")
    record, step = advance(env, serve=False)
    from learnloop.daily_plan.engine import _context, _live_context  # noqa: F401 - the view's own path

    context, _built = _live_context(env, record)
    decision = decide(record, context, env.policy.projection())
    assert all(PROBE not in candidate.item_ids for candidate in decision.candidates)


# -- review F2: a failure never erases a hard constraint --------------------------


def _reserved_world(tmp_path):
    """The router world with ``pi_m1b`` on a live assessment reservation and the
    seen probe in the pool: two items the frame must refuse."""

    from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
    from learnloop.daily_plan.policy import policy_for
    from learnloop.substrate.activities import reserve_surface

    env = _world(tmp_path, version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    vault = load_vault(env.vault.root)
    resolved = resolve_legacy_item(vault, env.repository, vault.practice_items["pi_m1b"], purpose="assessment")
    reserve_surface(env.repository, surface_id=resolved.surface_id, purpose="assessment")
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock)
    return env


def _boom(*_args, **_kwargs):
    raise RuntimeError("read failed")


def test_an_annotation_failure_keeps_every_refusal(tmp_path, monkeypatch):
    """Codex review F2: the cold-check and ladder reads are annotations. When
    one raises after the constraints were evaluated, the refusals stand (the
    reserved item and the seen probe stay out), and the failure is named."""

    from learnloop.daily_plan import staged_frame as SF

    env = _reserved_world(tmp_path)
    monkeypatch.setattr(SF.StagedFrame, "_cold_items", _boom)
    monkeypatch.setattr(SF.StagedFrame, "_ladder", _boom)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert "pi_m1b" not in _planned(record) and PROBE not in _planned(record)
    assert "pi_m1a" in _planned(record)
    [row] = _plan_block_rows(env)
    assert row["exclusions_json"]["named"]["assessment_reservation"] == ["pi_m1b"]
    assert row["exclusions_json"]["named"]["hard_exposure_collision"] == [PROBE]
    frame = json.loads(row["detail_json"])["staged_frame"]
    assert "cold_checks" in frame["error"] and "ladder" in frame["error"]
    # A cold-check read that failed leaves reversibility unknown: an item
    # block is never in a draw's support (G2).
    item_blocks = {c["ref"] for c in row["candidates_json"] if c.get("item_ids")}
    assert item_blocks
    assert not item_blocks & set(json.loads(row["detail_json"])["router"].get("draw_support", []))


def test_a_snapshot_failure_fails_closed_only_where_a_constraint_cannot_be_established(tmp_path, monkeypatch):
    """Without the controller snapshot (the exposure ledger) a quick check's
    freshness cannot be established: it is refused, as P4 refuses unknown
    freshness. The reservation is its own read, so the reserved item is still
    refused, and ordinary practice is still planned."""

    from learnloop.scheduling import controller_snapshot as cs

    env = _reserved_world(tmp_path)
    monkeypatch.setattr(cs, "build_snapshot", _boom)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert "pi_m1b" not in _planned(record) and PROBE not in _planned(record)
    assert "pi_m1a" in _planned(record)
    [row] = _plan_block_rows(env)
    assert row["exclusions_json"]["named"]["assessment_reservation"] == ["pi_m1b"]
    frame = json.loads(row["detail_json"])["staged_frame"]
    [refusal] = frame["refused"][PROBE]
    assert (refusal["constraint_key"], refusal["reason"]) == ("hard_exposure_collision", "freshness_unknown")
    assert "snapshot" in frame["error"]


def test_without_the_constraints_inputs_every_item_is_refused(tmp_path, monkeypatch):
    """When the reservations themselves cannot be read, no item's hard
    constraints can be established: each is refused with a named reason
    (fail closed), never served unchecked."""

    env = _reserved_world(tmp_path)
    monkeypatch.setattr(type(env.repository), "reserved_assessment_surfaces", _boom)
    record = build_plan(env, kind="normal", budget=15.0, remembered=15, minutes_source="chip")
    assert not {"pi_m1a", "pi_m1b", PROBE} & set(_planned(record))
    [row] = _plan_block_rows(env)
    assert row["exclusions_json"]["named"]["constraints_unavailable"] == sorted(["pi_m1a", "pi_m1b", PROBE])
