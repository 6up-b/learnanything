"""Reader workbench RW3b: the holdout and the impressions (spec_reader_workbench_v1 §6.2 item 6, §6.3; G14).

An eligible discovered cue is withheld by a seeded draw: the logged propensity
equals the draw's probability and the seed reproduces the draw; Guide cues are
never held out; a cue cut by the density budget, the spacing rule or the
restored-line rule is not a holdout, and its impression says why. The server
records what it decides (holdout, density) whatever the client claims, and
the seed, propensity, ``p_open`` and density come from its own computation.
Only a cue the density budget admits is randomized (Codex review F4): a cut
one carries no propensity. Fakes only.
"""

from __future__ import annotations

import hashlib

import pytest

from learnloop.db.stores import reader_cue_links as store
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.source_retrieval import passage_cues as PC
from learnloop_sidecar.errors import SidecarError
from tests.passage_cue_fakes import build_cue_vault, guide_cue, loaded, seed_link, set_config, snake, target
from tests.recap_fixtures import call, context


def test_the_seed_reproduces_the_draw_and_the_propensity_is_the_draws_probability():
    for index in range(200):
        link_id = f"plink_{index}"
        first, again = PC.holdout_draw(link_id, 0.1), PC.holdout_draw(link_id, 0.1)
        assert first == again
        assert first["seed"] == hashlib.sha256(f"{PC.HOLDOUT_SALT}:{link_id}".encode()).hexdigest()[:16]
        assert first["held_out"] == (int(first["seed"], 16) / float(1 << 64) < 0.1)
        assert first["propensity"] == (0.1 if first["held_out"] else 0.9)


def test_the_draw_withholds_about_the_rate_and_rate_zero_withholds_nothing():
    draws = [PC.holdout_draw(f"plink_rate_{index}", 0.25) for index in range(4000)]
    share = sum(draw["held_out"] for draw in draws) / len(draws)
    assert abs(share - 0.25) < 0.03
    assert not any(PC.holdout_draw(f"plink_{index}", 0.0)["held_out"] for index in range(500))
    assert all(PC.holdout_draw(f"plink_{index}", 0.0)["propensity"] == 1.0 for index in range(50))


def _merged(tmp_path, monkeypatch, *, rate: float, targets, links, guide=None, density="more"):
    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    if guide:
        guide_cue(paths, repository, guide)
    set_config(paths, "cues", holdout_rate=rate, density=density)
    ids = [seed_link(repository, t, span) for t, span in links]
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: list(targets))
    vault = loaded(paths)
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text",
                          plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    return paths, repository, cues, ids


def test_a_held_out_cue_is_not_shown_and_carries_its_seed_and_propensity_guide_cues_never_are(tmp_path, monkeypatch):
    targets = [target("hypothesis", f"h{index}", p_open=0.5) for index in range(8)]
    spans = ["t1", "t3", "t4", "t5", "t6", "t7", "t8", "t9"]
    _paths, _repository, cues, ids = _merged(tmp_path, monkeypatch, rate=0.95, targets=targets,
                                             links=list(zip(targets, spans)), guide=["t2"])
    held = cues["discovery"]["held_out"]
    expected = {link_id for link_id in ids if PC.holdout_draw(link_id, 0.95)["held_out"]}
    assert {entry["link_id"] for entry in held} == expected and expected
    for entry in held:
        draw = PC.holdout_draw(entry["link_id"], 0.95)
        assert entry["seed"] == draw["seed"] and entry["propensity"] == pytest.approx(0.95)
    shown_ids = {mark.get("link_id") for mark in cues["marks"]}
    assert not shown_ids & expected
    # The Guide's own mark is shown whatever the rate (never held out).
    assert any(mark["found_by"] == "guide" and mark["span_id"] == "t2" for mark in cues["marks"])
    assert all(mark["found_by"] == "guide" or mark["propensity"] == pytest.approx(0.05) for mark in cues["marks"])


def test_rate_zero_turns_the_holdout_off(tmp_path, monkeypatch):
    targets = [target("hypothesis", f"h{index}", p_open=0.5) for index in range(4)]
    _paths, _repository, cues, _ids = _merged(tmp_path, monkeypatch, rate=0.0, targets=targets,
                                              links=list(zip(targets, ["t1", "t3", "t5", "t7"])))
    assert cues["discovery"]["held_out"] == [] and cues["withheld"]["holdout"] == 0
    assert all(mark["propensity"] == 1.0 for mark in cues["marks"])


# -- the impressions RPC: the server records what it decides ------------------------------------


def _ctx_with_cues(tmp_path, monkeypatch, *, rate: float, density: str = "fewer"):
    targets = [target("hypothesis", f"h{index}", p_open=0.9 - index * 0.1) for index in range(6)]
    paths, repository, _cues, ids = _merged(tmp_path, monkeypatch, rate=rate, targets=targets,
                                            links=list(zip(targets, ["t1", "t3", "t5", "t7", "t8", "t9"])),
                                            guide=["t2"], density=density)
    ctx = context(paths.root)
    plan = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))
    return ctx, repository, plan["cues"], ids


def _rows(repository) -> list[dict]:
    with repository.connection() as connection:
        return store.impressions(connection)


def test_impressions_record_shown_holdout_density_and_the_clients_restraint_reasons(tmp_path, monkeypatch):
    ctx, repository, cues, _ids = _ctx_with_cues(tmp_path, monkeypatch, rate=0.5)
    held = cues["discovery"]["held_out"]
    density = cues["discovery"]["suppressed"]
    assert held and density
    marks = cues["marks"]
    entries = [{"cue_id": marks[0]["cue_id"], "shown": True}]
    if len(marks) > 1:
        entries.append({"cue_id": marks[1]["cue_id"], "shown": False, "reason": "spacing"})
    # The client claims a held-out cue and a density cut were shown: the server records its own reason.
    entries += [{"cue_id": held[0]["cue_id"], "shown": True}, {"cue_id": density[0]["cue_id"], "shown": True}]
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "visit_1",
                                         "plan_id": cues["discovery"]["plan_id"], "entries": entries})
    rows = {row["cue_id"]: row for row in _rows(repository)}
    assert rows[marks[0]["cue_id"]]["shown"] is True and rows[marks[0]["cue_id"]]["suppressed_reason"] is None
    assert rows[held[0]["cue_id"]]["suppressed_reason"] == "holdout" and rows[held[0]["cue_id"]]["shown"] is False
    assert rows[held[0]["cue_id"]]["propensity"] == pytest.approx(0.5) and rows[held[0]["cue_id"]]["seed"] == held[0]["seed"]
    assert rows[density[0]["cue_id"]]["suppressed_reason"] == "density"
    if len(marks) > 1:
        assert rows[marks[1]["cue_id"]]["suppressed_reason"] == "spacing"
    for row in rows.values():
        assert row["density"] == "fewer" and row["visit_id"] == "visit_1"
        source = next(cue for cue in [*marks, *held, *density] if cue["cue_id"] == row["cue_id"])
        assert row["p_open"] == source["p_open"] and row["p_open_source"] == source["p_open_source"]
        if source["found_by"] == "guide":
            assert row["link_id"] is None and row["propensity"] is None and row["seed"] is None
        else:
            # A density cut was never randomized (Codex review F4): no propensity.
            assert row["link_id"] == source["link_id"] and row["propensity"] == source.get("propensity")


def test_one_impression_per_visit_and_cue_and_the_client_cannot_invent_one(tmp_path, monkeypatch):
    ctx, repository, cues, _ids = _ctx_with_cues(tmp_path, monkeypatch, rate=0.0, density="more")
    plan_id = cues["discovery"]["plan_id"]
    cue_id = cues["marks"][0]["cue_id"]
    for _ in range(2):
        call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": plan_id,
                                             "entries": [{"cue_id": cue_id, "shown": True}]})
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v2", "plan_id": plan_id,
                                         "entries": [{"cue_id": cue_id, "shown": False, "reason": "restored_line"}]})
    assert [(row["visit_id"], row["shown"], row["suppressed_reason"]) for row in _rows(repository)] == [
        ("v1", True, None), ("v2", False, "restored_line")]
    for bad in ({"cue_id": "dcue_forged", "shown": True}, {"cue_id": cue_id, "shown": False, "reason": "holdout"},
                {"cue_id": cue_id, "shown": False, "reason": "skim"}):
        with pytest.raises(SidecarError):
            call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v3", "plan_id": plan_id,
                                                 "entries": [bad]})
    assert len(_rows(repository)) == 2


def test_fewer_marks_like_this_is_the_impressions_response_written_once(tmp_path, monkeypatch):
    ctx, repository, cues, _ids = _ctx_with_cues(tmp_path, monkeypatch, rate=0.0, density="more")
    plan_id = cues["discovery"]["plan_id"]
    cue_id = next(mark["cue_id"] for mark in cues["marks"] if mark["found_by"] == "model")
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": plan_id,
                                         "entries": [{"cue_id": cue_id, "shown": True}]})
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1", "plan_id": plan_id,
                                         "entries": [{"cue_id": cue_id, "response": "fewer"}]})
    call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": cue_id, "action": "opened",
                                 "visit_id": "v1"})
    (row,) = _rows(repository)
    assert row["response"] == "fewer" and row["responded_at"]


def test_the_impressions_rpcs_refuse_while_discovery_is_off(tmp_path):
    paths, _repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", discovery_enabled=False)
    ctx = context(paths.root)
    for name, params in (("reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v", "plan_id": "p",
                                                  "entries": []}),
                         ("reader.cue_tap", {"extraction_id": "ext_text", "cue_id": "x", "action": "opened"}),
                         ("reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "o"}),
                         ("reader.cue_discovery_job", {"job_id": "cjob_x"})):
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "cues_disabled"
