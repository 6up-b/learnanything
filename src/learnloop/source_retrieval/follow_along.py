"""Reader workbench v2 RD10 (spec §7.5): follow-along, book ↔ video. No hand maps: the playing cue's section (the
video's section map of ``t=`` cues), its LOs and their correspondent passages in the book come from judged coverage
(:func:`learnloop.source_retrieval.section_coverage.correspondents`, judged only, never the search fallback). The
desk prefers the goal path's primary section among them (it has the path); where the book has none, it says "no
passage here" and nothing scrolls. The chapter a chip names is the accepted chapter the time falls in, else the
transcript section's own label. No model call and no write.
"""
from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.source_retrieval import section_coverage as SC
from learnloop.source_retrieval import video_chapters as VC


def follow(vault: Any, repository: Repository, video_extraction_id: str, t: float, book_extraction_id: str, *,
           cache: SC.LibraryCache | None = None) -> dict[str, Any]:
    """What a book window follows at a video's time: ``status`` (``following``, ``no_passage``, ``no_section``,
    ``withheld``), the video's section with its time bounds (the desk asks again only once the time leaves them),
    the chapter, and per LO the book's correspondent sections (each with where it lands)."""

    sections = VC.transcript_sections(repository, video_extraction_id)
    section = VC.section_at(sections, float(t))
    chapter = VC.accepted_at(repository, video_extraction_id, float(t))
    out: dict[str, Any] = {"video_extraction_id": video_extraction_id, "book_extraction_id": book_extraction_id,
                           "t": float(t), "section": None, "chapter": None, "learning_objects": []}
    if chapter is not None:
        out["chapter"] = {"chapter_id": chapter["chapter_id"], "title": chapter["title"], "t0": chapter["t0"],
                          "t1": chapter["t1"]}
    if section is None:
        out["status"] = "no_section"
        return out
    out["section"] = {"section_id": section.section_id, "title": section.title, "t0": section.t0, "t1": section.t1}
    view = SC.correspondents(vault, repository, video_extraction_id, section.section_id, search_fallback=False,
                             cache=cache)
    if view.get("status") == "withheld":
        out["status"] = "withheld"
        return out
    groups = []
    for group in view.get("learning_objects") or ():
        found = []
        for source in group.get("sources") or ():
            for candidate in source.get("sections") or ():
                if candidate.get("extraction_id") != book_extraction_id:
                    continue
                jump = candidate.get("jump") or {}
                found.append({"section_id": candidate["section_id"], "title": candidate.get("title"),
                              "jump_span_id": jump.get("span_id")})
        if found:
            groups.append({"learning_object_id": group["learning_object_id"], "title": group.get("title"),
                           "sections": found})
    out["learning_objects"] = groups
    out["status"] = "following" if groups else "no_passage"
    return out


__all__ = ["follow"]
