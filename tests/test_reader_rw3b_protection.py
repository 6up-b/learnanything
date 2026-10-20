"""Reader workbench RW3b: held-out protection, display only and wording (G13, G16; orchestrator notes 1-2).

* **Held-out sentinel.** A passage in a held-out unit never reaches the cue
  judge's prompt, a stored quote or a rendered cue, though it is the best
  keyword match; a reading held out whole is never searched; the protection
  is the shared helpers' (``teaching_exclusions``, ``held_out_material``,
  ``model_reader_withheld``), never a second leak check.
* **Display only (G13).** Discovery, the merged plan, taps and impressions
  write no evidence, mastery, FSRS, attempt or plan row: only the ledger's
  verdicts, the links, the impressions, salience-only events and the paid
  call's own receipts.
* **Wording (G16).** Every discovered template and every rendered note and
  "because" line is a fixed template with no trait or verdict word.
Fakes only.
"""

from __future__ import annotations

import json
import re

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.stores import reader_cue_links as store
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.source_retrieval import passage_cues as PC
from tests.passage_cue_fakes import CueJudgeFake, build_cue_vault, loaded, set_config, snake
from tests.recap_fixtures import call, context
from tests.test_reader_inquiry_status import table_counts

#: Words only the row-swap passage (t3) says: the held-out sentinel.
SENTINEL = "multiplies its determinant by -1"
BANNED = re.compile(
    r"\b(weak|you don'?t understand|you struggle|you always|wrong|error|errors|mistake|mistakes|"
    r"confused|failed|failure|overdue)\b",
    re.IGNORECASE,
)


def _hold_out_chapter_5(repository) -> None:
    save_unit_selection(repository, "ext_text", ["ch5", "worked", "exercises", "solutions"],
                        exam_use_modes={"ch5": "held_out_evaluation"})


def test_a_held_out_passage_never_reaches_the_judge_a_quote_or_a_cue(tmp_path):
    paths, repository, spans = build_cue_vault(tmp_path / "v")
    _hold_out_chapter_5(repository)
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = fake = CueJudgeFake()
    job = snake(call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"}))
    assert job["state"] == "done"
    assert fake.prompts, "the target was judged over the passages that are not held out"
    assert all(SENTINEL not in prompt for prompt in fake.prompts)
    assert all(candidate["passage"].find(SENTINEL) < 0 for context_ in fake.contexts
               for candidate in context_["candidates"])
    with repository.connection() as connection:
        links = store.links_for_extraction(connection, "ext_text")
    assert all(SENTINEL not in link["quote"] and link["span_id"] not in spans["ch5"] for link in links)
    cues = call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"})["cues"]
    assert SENTINEL not in json.dumps(cues)
    assert not {mark["spanId"] for mark in cues["marks"]} & set(spans["ch5"])


def test_a_link_made_before_its_passage_was_held_out_is_never_shown_or_tapped(tmp_path):
    import pytest

    from learnloop_sidecar.errors import SidecarError

    paths, repository, spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = CueJudgeFake()
    call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"})
    before = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]["marks"]
    on_ch5 = [mark for mark in before if mark["span_id"] in spans["ch5"]]
    assert on_ch5
    _hold_out_chapter_5(repository)
    after = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]["marks"]
    assert not {mark["span_id"] for mark in after} & set(spans["ch5"])
    with pytest.raises(SidecarError):
        call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": on_ch5[0]["cue_id"], "action": "opened",
                                     "plan_id": "p"})


def test_a_reading_held_out_whole_is_never_searched(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    fake = CueJudgeFake()
    out = PC.discover(vault, repository, "ext_exam", client=fake)
    assert out["status"] in ("withheld", "done") and fake.prompts == []


def test_discovery_cues_and_taps_write_no_evidence_mastery_fsrs_attempt_or_plan_row(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = CueJudgeFake()
    before = table_counts(repository)
    call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"})
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    marks = cues["marks"]
    assert marks
    cue_id = marks[0]["cue_id"]
    call(ctx, "reader.cue_impressions", {"extraction_id": "ext_text", "visit_id": "v1",
                                         "plan_id": cues["discovery"]["plan_id"],
                                         "entries": [{"cue_id": cue_id, "shown": True}]})
    for action in ("opened", "not_relevant", "not_relevant_undone"):
        call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": cue_id, "action": action,
                                     "visit_id": "v1", "plan_id": cues["discovery"]["plan_id"],
                                     "text": "about something else" if action == "not_relevant" else None})
    after = table_counts(repository)
    changed = {name for name in after if after[name] != before.get(name)}
    allowed = {"judgment_ledger", "passage_links", "reader_cue_impressions", "model_call_receipts",
               "model_work_checkpoints", "agent_runs", "ai_usage_events"}
    assert changed <= allowed, changed - allowed
    for table in ("practice_attempts", "grading_evidence", "error_events", "facet_mastery_state", "fsrs_state",
                  "learning_object_mastery", "daily_plans", "attention_blocks", "router_decisions"):
        if table in after:
            assert after[table] == before[table], table


def test_not_relevant_text_is_judge_feedback_never_learner_text(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    ctx = context(paths.root)
    ctx.cue_discovery_inline = True
    ctx.cue_judge_client = CueJudgeFake()
    call(ctx, "reader.cue_discovery", {"extraction_id": "ext_text", "source_open_id": "open_1"})
    cues = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]
    cue_id = cues["marks"][0]["cue_id"]
    call(ctx, "reader.cue_tap", {"extraction_id": "ext_text", "cue_id": cue_id, "action": "not_relevant",
                                 "visit_id": "v1", "text": "this passage is about eigenvalues",
                                 "plan_id": cues["discovery"]["plan_id"]})
    with repository.connection() as connection:
        events = [row[0] for row in connection.execute("SELECT payload_json FROM interaction_events")]
        gaps = connection.execute("SELECT COUNT(*) FROM learner_text_gaps").fetchone()[0]
        jobs = connection.execute("SELECT COUNT(*) FROM learner_text_gap_jobs").fetchone()[0]
        (impression,) = store.impressions(connection)
    assert all("eigenvalues" not in payload for payload in events)
    assert gaps == 0 and jobs == 0
    assert impression["response"] == "not_relevant" and impression["response_text_hash"]
    # Not relevant withholds that cue until it is undone.
    marks = snake(call(ctx, "reader.guide_plan", {"extraction_id": "ext_text"}))["cues"]["marks"]
    assert cue_id not in {mark["cue_id"] for mark in marks}


def test_every_discovered_template_and_rendered_line_is_free_of_trait_and_verdict_words(tmp_path):
    for template in PC.DISCOVERED_TEMPLATES:
        assert not BANNED.search(template), template
    assert all(template.endswith("found by LearnLoop's model, not by a test")
               for template in (PC.BECAUSE_WORK, PC.BECAUSE_QUESTION, PC.BECAUSE_SHOWN))
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", holdout_rate=0.0, density="more")
    vault = loaded(paths)
    PC.discover(vault, repository, "ext_text", client=CueJudgeFake())
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text",
                          plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    assert cues["marks"]
    for mark in cues["marks"]:
        line = f"{mark['note']} {mark['because']} {mark['label']}"
        assert not BANNED.search(line), line
        assert mark["earlier"]["statement"] not in mark["note"] + mark["because"]
