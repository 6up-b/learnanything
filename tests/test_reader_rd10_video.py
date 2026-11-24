"""Reader workbench v2 RD10 (spec §7.5, §7.9): follow-along through judged correspondents (no hand maps) and suggested
video chapters as a polled, cancellable, vault-scoped judged job whose acceptance is stored. Every model is a fake; no
network."""

from __future__ import annotations

import time

import pytest

from learnloop.source_retrieval import follow_along as FA
from learnloop.source_retrieval import video_chapters as VC
from learnloop.vault.loader import load_vault
from tests.reader_rd10_helpers import VIDEO, ChaptersJudgeFake, build_video_vault
from tests.reading_path_fixtures import call, context, table_counts


def test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.handlers import video as H
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert H.VIDEO_RPCS == ("reader.follow_along", "chapters.list", "chapters.suggest", "chapters.job",
                            "chapters.cancel", "chapters.decide")
    for name in H.VIDEO_RPCS:
        assert name in METHOD_REGISTRY and name not in ALLOWLIST
    with pytest.raises(ValueError):
        H.FollowAlongInput.model_validate({"extractionId": "e", "t": 1, "bookExtractionId": "b", "extra": 1})
    with pytest.raises(ValueError):
        H.FollowAlongInput.model_validate({"extractionId": "e", "t": -1, "bookExtractionId": "b"})
    with pytest.raises(ValueError):
        H.ChaptersDecideInput.model_validate({"chapterId": "c", "decision": "maybe"})


def test_follow_along_maps_the_playing_cue_to_the_books_correspondent_passage(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    before = table_counts(repository)
    # 25 s is the eigenvalues section's (cues c3, c4: 20 s to 40 s).
    found = FA.follow(vault, repository, VIDEO, 25.0, "ext_book")
    assert table_counts(repository) == before
    assert found["status"] == "following"
    assert found["section"] == {"section_id": "v_eigen", "title": "Section v_eigen", "t0": 20.0, "t1": 40.0}
    # The bounds run to the next section's start (the last section's are open), so the desk asks once per section.
    assert FA.follow(vault, repository, VIDEO, 59.0, "ext_book")["section"]["t1"] is None
    eigen = next(group for group in found["learning_objects"] if group["learning_object_id"] == "lo_eigen")
    assert eigen["sections"] and all(section["jump_span_id"] for section in eigen["sections"])
    # The introduction treats no LO: nothing in the book corresponds, and nothing scrolls.
    intro = FA.follow(vault, repository, VIDEO, 5.0, "ext_book")
    assert intro["status"] == "no_passage" and intro["section"]["section_id"] == "v_intro"
    assert intro["learning_objects"] == []


def test_follow_along_through_the_rpc_and_with_no_coverage(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    ctx = context(paths.root)
    reply = call(ctx, "reader.follow_along", {"extraction_id": VIDEO, "t": 25, "book_extraction_id": "ext_book"})
    # No judged coverage: no hand map stands in, so there is no passage here.
    assert reply["status"] == "no_passage" and reply["learningObjects"] == []
    assert reply["section"]["sectionId"] == "v_eigen"


def _wait(ctx, job_id):
    deadline = time.monotonic() + 20
    while True:
        reply = call(ctx, "chapters.job", {"job_id": job_id})
        if reply["done"] or time.monotonic() > deadline:
            return reply
        time.sleep(0.05)


def test_chapters_are_judged_once_stored_suggested_and_accepting_stores(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault")
    fake = ChaptersJudgeFake()
    ctx = context(paths.root, video_chapters_client=fake)
    assert call(ctx, "chapters.list", {"extraction_id": VIDEO})["chapters"] == []
    started = call(ctx, "chapters.suggest", {"extraction_id": VIDEO})
    finished = _wait(ctx, started["jobId"])
    assert finished["status"] == "done", finished
    result = finished["result"]
    assert result["status"] == "ready"
    titles = [(chapter["title"], chapter["t0"], chapter["t1"], chapter["learningObjectIds"]) for chapter in result["chapters"]]
    assert titles == [("introduction", 0.0, 20.0, []), ("eigenvalues", 20.0, 40.0, ["lo_eigen"]),
                      ("determinants", 40.0, 60.0, ["lo_det"])]
    assert fake.calls == 1
    # The prompt holds the transcript and the LOs it is judged against, never the held-out sentinel.
    assert [candidate["from"] for candidate in fake.contexts[0]["candidates"]] == [0.0, 20.0, 40.0]
    assert "HELDOUTSENTINEL" not in fake.prompts[0]
    # The same request again is answered from the ledger, with no call; the chapters are the same rows.
    again = _wait(ctx, call(ctx, "chapters.suggest", {"extraction_id": VIDEO})["jobId"])
    assert again["result"]["status"] == "ready" and fake.calls == 1
    listed = call(ctx, "chapters.list", {"extraction_id": VIDEO})["chapters"]
    assert [chapter["state"] for chapter in listed] == ["suggested"] * 3
    eigen = listed[1]
    accepted = call(ctx, "chapters.decide", {"chapter_id": eigen["chapterId"], "decision": "accept"})["chapter"]
    assert accepted["state"] == "accepted" and accepted["decidedAt"]
    # Deciding it the same way again answers it; the other way is refused.
    assert call(ctx, "chapters.decide", {"chapter_id": eigen["chapterId"], "decision": "accept"})["chapter"]["state"] == "accepted"
    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError) as refused:
        call(ctx, "chapters.decide", {"chapter_id": eigen["chapterId"], "decision": "dismiss"})
    assert refused.value.code == "already_decided"
    dismissed = call(ctx, "chapters.decide", {"chapter_id": listed[0]["chapterId"], "decision": "dismiss"})["chapter"]
    assert dismissed["state"] == "dismissed"
    shown = call(ctx, "chapters.list", {"extraction_id": VIDEO})["chapters"]
    assert [(chapter["title"], chapter["state"]) for chapter in shown] == [("eigenvalues", "accepted"),
                                                                           ("determinants", "suggested")]
    # A new run replaces only what is still suggested; the decisions stay.
    vault = load_vault(paths.root)
    VC.store_suggestions(repository, VIDEO, "src_vid", [])
    assert [(c["title"], c["state"]) for c in VC.list_chapters(vault, repository, VIDEO, states=VC.STATES)] == [
        ("introduction", "dismissed"), ("eigenvalues", "accepted")]
    # The accepted chapter names what follow-along follows in its range.
    assert FA.follow(vault, repository, VIDEO, 25.0, "ext_book")["chapter"]["title"] == "eigenvalues"


def test_a_cancelled_suggestion_sends_nothing_more_and_a_failure_keeps_nothing(tmp_path):
    from learnloop.ai.errors import AIProviderUnavailable

    paths, repository = build_video_vault(tmp_path / "vault")
    failing = ChaptersJudgeFake(fail=AIProviderUnavailable("down"))
    ctx = context(paths.root, video_chapters_client=failing)
    finished = _wait(ctx, call(ctx, "chapters.suggest", {"extraction_id": VIDEO})["jobId"])
    assert finished["done"] and finished["result"]["status"] in {"failed", "unavailable"}
    assert call(ctx, "chapters.list", {"extraction_id": VIDEO})["chapters"] == []
    # Cancelling a finished job keeps its outcome; an unknown job is not found.
    cancelled = call(ctx, "chapters.cancel", {"job_id": finished["jobId"]})
    assert cancelled["done"]
    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError) as missing:
        call(ctx, "chapters.job", {"job_id": "vch_unknown"})
    assert missing.value.code == "job_not_found"


def test_chapters_are_off_with_the_curriculum(tmp_path):
    from tests.ux_phase1_support import set_config

    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    set_config(paths.root, {("curriculum", "enabled"): False})
    result = VC.suggest(load_vault(paths.root), repository, VIDEO, client=ChaptersJudgeFake())
    assert result.status == "unavailable" and result.reason == "curriculum_disabled"


def test_the_chapters_are_assembled_from_the_judged_boundaries():
    sections = [VC.TranscriptSection("a", "0:00–0:20", 0.0, 20.0, ("c1",)),
                VC.TranscriptSection("b", "0:20–0:40", 20.0, 40.0, ("c2",)),
                VC.TranscriptSection("c", "0:40–1:00", 40.0, 60.0, ("c3",))]
    prompt = VC.Prompt(text="", refs={"s1": "a", "s2": "b", "s3": "c"}, learning_objects={"l1": "lo_x"})
    rows = {"a": {"id": "j1", "verdict": "continues", "rationale": '{"title": "", "learning_objects": []}'},
            "b": {"id": "j2", "verdict": "continues", "rationale": '{"title": "", "learning_objects": []}'},
            "c": {"id": "j3", "verdict": "starts", "rationale": '{"title": "the end", "learning_objects": ["l1", "l9"]}'}}
    chapters = VC.assemble("ext", sections, prompt, rows)
    # The first section always starts one (titled from its section when the judge gave none); an unlisted LO ref drops.
    assert [(c["title"], c["t0"], c["t1"], c["learning_object_ids"]) for c in chapters] == [
        ("0:00–0:20", 0.0, 40.0, []), ("the end", 40.0, 60.0, ["lo_x"])]
    assert VC.section_at(sections, 25.0).section_id == "b" and VC.section_at(sections, 999).section_id == "c"
    assert chapters[0]["chapter_id"] == VC.chapter_id("ext", 0.0, 40.0, "0:00–0:20")


def test_a_saved_chapter_names_nothing_once_its_video_is_marked_exam_material(tmp_path):
    """Protection is read at every delivery: a chapter judged before its video was marked as exam material keeps its
    times and ids, its title and tags neutral."""
    from learnloop.content.synthesis.source_unit_selection import save_unit_selection
    from learnloop.curriculum import goal_lens as GL

    paths, repository = build_video_vault(tmp_path / "vault")
    ctx = context(paths.root, video_chapters_client=ChaptersJudgeFake())
    _wait(ctx, call(ctx, "chapters.suggest", {"extraction_id": VIDEO})["jobId"])
    listed = call(ctx, "chapters.list", {"extraction_id": VIDEO})["chapters"]
    assert [chapter["title"] for chapter in listed] == ["introduction", "eigenvalues", "determinants"]
    save_unit_selection(repository, VIDEO, [], role_override="exam")
    listed = call(ctx, "chapters.list", {"extraction_id": VIDEO})["chapters"]
    assert [(chapter["title"], chapter["held"], chapter["t0"]) for chapter in listed] == [
        (GL.NEUTRAL_SECTION, True, 0.0), (GL.NEUTRAL_SECTION, True, 20.0), (GL.NEUTRAL_SECTION, True, 40.0)]
    assert all(tag["title"] == GL.NEUTRAL_LO for chapter in listed for tag in chapter["learningObjects"])
