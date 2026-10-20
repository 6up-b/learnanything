"""Reader workbench RW3b: "Try this step first" (spec_reader_workbench_v1 §6.1, §6.2 item 3; G42).

A try-first cue appears only on a worked example or derivation for a target
that is an open question (a misconception, an open hypothesis, a named gap),
never for a shown skill; the judge proposing it elsewhere is overruled in
code. Pressing it is the learner's pick: one salience-only ``cue_try_first``
event, a ``learner_card`` verdict and the impression's response, and the
answer names the line where RW1b's "Let me try the next step" opens. With
``cues.try_first_enabled`` off no try-first cue shows. Fakes only.
"""

from __future__ import annotations

import pytest

from learnloop.attempts import salience_firewall as SF
from learnloop.db.stores import reader_cue_links as store
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.source_retrieval import passage_cues as PC
from learnloop_sidecar.errors import SidecarError
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, set_config, snake, target
from tests.recap_fixtures import call, context

#: Shares words with the worked example (t5) and with exercise 1 (t7).
SOLVE = "Solve for the eigenvalue by subtracting and dividing both sides"


def _links(repository) -> list[dict]:
    with repository.connection() as connection:
        return store.links_for_extraction(connection, "ext_text")


def test_try_first_is_kept_only_on_a_worked_example_for_an_open_target(tmp_path):
    paths, repository, spans = build_cue_vault(tmp_path / "v", statement=SOLVE)
    vault = loaded(paths)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(pick_try_first_everywhere=True))
    kept = {link["span_id"]: link["relation"] for link in _links(repository)}
    worked = spans["worked"][1]
    assert kept.get(worked) == "try_first"
    reasons = {entry["span_id"]: entry["reason"] for entry in out["targets"][0]["dropped"]}
    assert all(span not in kept for span in reasons)
    assert set(reasons.values()) <= {"try first fits only a worked example or derivation on an open question"}
    assert all(relation != "try_first" or span == worked for span, relation in kept.items())


def test_a_shown_skill_never_gets_a_try_first_cue(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    vault = loaded(paths)
    shown = target("demonstrated_facet", "facet_eigen", p_open=0.3, statement=SOLVE, source="predictor")
    listed = PC.shortlist(vault, repository, shown, "ext_text")
    judged = PC.judge_target(vault, repository, listed, "ext_text", client=CueJudgeFake(pick_try_first_everywhere=True))
    assert judged["links"] == []
    assert judged["dropped"] and {entry["relation"] for entry in judged["dropped"]} == {"try_first"}


def _try_first_ctx(tmp_path, *, config: dict | None = None):
    paths, repository, spans = build_cue_vault(tmp_path / "v", statement=SOLVE)
    set_config(paths, "cues", holdout_rate=0.0, density="more", **(config or {}))
    # Opening the vault may open a probe episode on the misconception (its
    # target is then that hypothesis): discovery runs where the Reader runs it.
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = CueJudgeFake(try_first=True)
    job = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text"}))
    assert job["state"] == "done" and job["result"]["links"] >= 1, job
    return ctx, repository, spans


def test_pressing_try_first_is_a_learner_pick_that_opens_the_next_step_at_that_line(tmp_path):
    ctx, repository, spans = _try_first_ctx(tmp_path)
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    (mark,) = [mark for mark in cues["marks"] if mark["kind"] == "try_first"]
    assert mark["span_id"] == spans["worked"][1]
    assert mark["note"] == PC.NOTE_TRY_FIRST == "Try the next step before reading it?"
    assert mark["because"].endswith("· found by LearnLoop's model, not by a test")
    answer = snake(call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": mark["cue_id"],
                                                "action": "try_first", "visit_id": "v1"}))
    assert answer["try_first"] == {"span_id": mark["span_id"]} and answer["verdict"] == "same"
    with repository.connection() as connection:
        event = connection.execute(
            "SELECT payload_json FROM interaction_events WHERE kind = 'reader_action_invoked' "
            "ORDER BY rowid DESC LIMIT 1").fetchone()[0]
        verdict = connection.execute(
            "SELECT verdict, right_kind, right_id FROM judgment_ledger WHERE judge = 'learner_card'").fetchone()
        (impression,) = store.impressions(connection)
    payload = __import__("json").loads(event)
    assert payload["event"] == "cue_try_first" and payload["authority_class"] == SF.SALIENCE_ONLY
    assert tuple(verdict)[:2] == ("same", PC.TARGET_RIGHT_KIND) and verdict[2] == mark["target_id"]
    assert mark["target_kind"] in ("hypothesis", "misconception")
    assert impression["response"] == "try_first" and impression["shown"] is True


def test_try_first_on_a_cue_that_does_not_offer_it_is_refused(tmp_path):
    ctx, _repository, _spans = _try_first_ctx(tmp_path)
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    other = next(mark for mark in cues["marks"] if mark["kind"] != "try_first")
    with pytest.raises(SidecarError):
        call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": other["cue_id"], "action": "try_first"})


def test_with_try_first_switched_off_no_try_first_cue_shows(tmp_path):
    ctx, _repository, _spans = _try_first_ctx(tmp_path, config={"try_first_enabled": False})
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    assert cues["marks"] and all(mark["kind"] != "try_first" for mark in cues["marks"])
    assert cues["discovery"]["try_first"] is False
