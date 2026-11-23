"""A due check's protection over follow-along and the video chapters (spec §12.6.1, decision D15): while a cold check
is due on an LO, nothing ``reader.follow_along`` or the ``chapters.*`` RPCs return names or describes it: not the
accepted chapter's title (the chip shows it, the book linked or not), not the transcript section's label, not an LO
tag or a correspondent passage's title. The masking is the goal lens's own (``curriculum.goal_lens``, the same due-LO
set and neutral words); every model is a fake."""
from __future__ import annotations

import re
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from learnloop.curriculum import commitments as C
from learnloop.curriculum import goal_lens as GL
from learnloop.source_retrieval import deliverable_path as DP
from tests.reader_rd10_helpers import VIDEO, ChaptersJudgeFake, build_video_vault
from tests.reading_path_fixtures import call, context

X = "Eigenvalues"
P = GL.Protection.of(["lo_x"], [X], ["ext_vid/v_x", "ext_book/ch_x"])
SECTIONS = [("v_intro", 0.0, 20.0), ("v_x", 20.0, 40.0), ("v_y", 40.0, 60.0)]


def _strings(value: Any, path: str = "") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, dict):
        return [found for key, child in value.items() for found in _strings(child, f"{path}.{key}" if path else key)]
    if isinstance(value, list):
        return [found for index, child in enumerate(value) for found in _strings(child, f"{path}[{index}]")]
    return []


def _identifier(path: str) -> bool:
    return re.search(r"(_id|Id|_ids|Ids)(\[\d+\])?$", path) is not None


def _at(reply: Any, path: str) -> Any:
    value = reply
    for part in path.replace("]", "").replace("[", ".").split("."):
        value = value[int(part)] if part.isdigit() else value[part]
    return value


def _follow() -> dict[str, Any]:
    return {"video_extraction_id": "ext_vid", "book_extraction_id": "ext_book", "t": 25.0, "status": "following",
            "section": {"section_id": "v_x", "title": f"{X} by hand", "t0": 20.0, "t1": 40.0},
            "chapter": {"chapter_id": "vc_1", "title": "the spectrum", "t0": 20.0, "t1": 40.0, "learning_object_ids": ["lo_x"]},
            "learning_objects": [
                {"learning_object_id": "lo_x", "title": X, "sections": [{"section_id": "ch_x", "title": f"Chapter 5 {X}", "jump_span_id": "s1"}]},
                {"learning_object_id": "lo_y", "title": "Determinants", "sections": [
                    {"section_id": "ch_x", "title": "Chapter 5", "jump_span_id": "s2"},
                    {"section_id": "ch_y", "title": "Chapter 3 Determinants", "jump_span_id": "s3"}]}]}


def _chapters() -> list[dict[str, Any]]:
    def chapter(cid: str, t0: float, t1: float, title: str, los: list[str]) -> dict[str, Any]:
        return {"chapter_id": cid, "extraction_id": "ext_vid", "t0": t0, "t1": t1, "title": title, "learning_object_ids": los,
                "learning_objects": [{"learning_object_id": lo, "title": X if lo == "lo_x" else "Determinants"} for lo in los],
                "state": "accepted"}
    return [chapter("vc_tag", 40.0, 60.0, "a worked case", ["lo_x", "lo_y"]),   # tagged with the held LO
            chapter("vc_span", 10.0, 30.0, "warming up", []),                    # spans the section treating it
            chapter("vc_name", 55.0, 60.0, f"more {X.lower()}", []),            # its title names it
            chapter("vc_clean", 40.0, 60.0, "determinants", ["lo_y"])]


FOLLOW_TABLE = [
    ("chapter.title", GL.NEUTRAL_SECTION), ("chapter.held", True), ("section.title", GL.NEUTRAL_SECTION),
    ("learning_objects[0].title", GL.NEUTRAL_LO), ("learning_objects[0].sections[0].title", GL.NEUTRAL_SECTION),
    ("learning_objects[1].title", "Determinants"), ("learning_objects[1].sections[0].title", GL.NEUTRAL_SECTION),
    ("learning_objects[1].sections[1].title", "Chapter 3 Determinants"),
    ("learning_objects[0].sections[0].jump_span_id", "s1"), ("chapter.chapter_id", "vc_1"),
]
CHAPTER_TABLE = [
    ("[0].title", GL.NEUTRAL_SECTION), ("[0].learning_objects[0].title", GL.NEUTRAL_LO),
    ("[0].learning_objects[1].title", "Determinants"), ("[1].title", GL.NEUTRAL_SECTION),
    ("[2].title", GL.NEUTRAL_SECTION), ("[3].title", "determinants"), ("[0].t0", 40.0), ("[0].chapter_id", "vc_tag"),
]


@pytest.mark.parametrize(("path", "expected"), FOLLOW_TABLE)
def test_every_text_bearing_follow_along_field_is_masked(path, expected):
    assert _at(GL.protect_follow(_follow(), P, SECTIONS), path) == expected


@pytest.mark.parametrize(("path", "expected"), CHAPTER_TABLE)
def test_every_text_bearing_chapter_field_is_masked(path, expected):
    assert _at({"c": GL.protect_chapters(_chapters(), P, SECTIONS)}, "c" + path) == expected


def test_nothing_left_names_the_held_lo_and_nothing_changes_without_a_due_check():
    masked = [GL.protect_follow(_follow(), P, SECTIONS), GL.protect_chapters(_chapters(), P, SECTIONS)]
    assert [(p, t) for p, t in _strings(masked) if X.casefold() in t.casefold() and not _identifier(p)] == []
    assert GL.protect_follow(_follow(), GL.Protection(), SECTIONS) == _follow()
    assert GL.protect_chapters(_chapters(), GL.Protection(), SECTIONS) == _chapters()


# -- the RPCs, end to end -------------------------------------------------------------------------------------------

def _due_check(repository, lo_id, *, days: int = -1) -> None:
    day = (datetime.now(UTC) + timedelta(days=days)).strftime("%Y-%m-%d")
    C.create_commitment(
        repository, action="test_me_later", intent_text=f"check {lo_id}", depth_preset=DP.READY_DEPTH_PRESET,
        targets=[{"target_kind": "learning_object", "target_ref": lo_id, "role": "required"}],
        client_idempotency_key=f"rd10fix:{lo_id}:{days}", due_hint=day, provenance={"via": "deliverable_ready"})


def _wait(ctx, job_id):
    deadline = time.monotonic() + 20
    while True:
        reply = call(ctx, "chapters.job", {"job_id": job_id})
        if reply["done"] or time.monotonic() > deadline:
            return reply
        time.sleep(0.05)


def _leaks(reply: Any) -> list[tuple[str, str]]:
    return [(p, t) for p, t in _strings(reply) if "eigen" in t.casefold() and not _identifier(p)]


def test_follow_along_and_the_chapters_name_nothing_of_a_topic_whose_check_is_due(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault")
    ctx = context(paths.root, video_chapters_client=ChaptersJudgeFake())
    job = _wait(ctx, call(ctx, "chapters.suggest", {"extraction_id": VIDEO})["jobId"])
    eigen = next(chapter for chapter in job["result"]["chapters"] if chapter["title"] == "eigenvalues")
    call(ctx, "chapters.decide", {"chapter_id": eigen["chapterId"], "decision": "accept"})
    follow = {"extraction_id": VIDEO, "t": 25, "book_extraction_id": "ext_book"}
    assert call(ctx, "reader.follow_along", follow)["chapter"]["title"] == "eigenvalues"  # nothing due yet
    _due_check(repository, "lo_eigen")
    replies = {
        "follow": call(ctx, "reader.follow_along", follow),
        "list": call(ctx, "chapters.list", {"extraction_id": VIDEO}),
        "job": call(ctx, "chapters.job", {"job_id": job["jobId"]}),
        "decide": call(ctx, "chapters.decide", {"chapter_id": eigen["chapterId"], "decision": "accept"}),
    }
    assert {name: _leaks(reply) for name, reply in replies.items()} == {name: [] for name in replies}
    assert replies["follow"]["chapter"]["title"] == GL.NEUTRAL_SECTION
    assert replies["follow"]["status"] == "following"  # the passage is still followed, by id
    # Determinants, with no check due, keeps its words.
    titles = [chapter["title"] for chapter in replies["list"]["chapters"]]
    assert "determinants" in titles and GL.NEUTRAL_SECTION in titles


def test_the_replies_say_when_the_next_check_falls_due(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault")
    ctx = context(paths.root)
    follow = {"extraction_id": VIDEO, "t": 25, "book_extraction_id": "ext_book"}
    assert call(ctx, "reader.follow_along", follow)["nextCheckDue"] is None
    _due_check(repository, "lo_det", days=2)
    assert call(ctx, "reader.follow_along", follow)["nextCheckDue"] is not None
    assert call(ctx, "chapters.list", {"extraction_id": VIDEO})["nextCheckDue"] is not None
