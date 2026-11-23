"""Builders and fakes for Reader workbench v2 RD10's tests (follow-along and suggested chapters; no network).

``build_video_vault`` is curriculum C0b's deliverable vault (the book ``ext_book``, the second book ``ext_lay``) plus a
video ``src_vid`` whose reading ``ext_vid`` has three timed transcript sections: an introduction, one on eigenvalues
and one on determinants (``VIDEO``; cue ``i`` spans ``t=(i-1)*10``..``i*10``). With ``cover`` the coverage judge's fake
judges the LOs, so the video's eigenvalues section and the book's eigen chapter correspond.

``ChaptersJudgeFake`` answers the chapters judge from its prompt: a chapter starts at the first section and at every
section whose words name an LO's first word, titled with that word, tagged with that LO.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learnloop.ai.execution import report_call_usage
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, STRUCTURED_COMPLETION
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from tests.deliverable_fixtures import build_deliverable_vault, cover_all
from tests.desk_helpers import seed_reading
from tests.structured_ai import StructuredClientFake

VIDEO = "ext_vid"
VIDEO_SECTIONS = [("v_intro", ["c1", "c2"]), ("v_eigen", ["c3", "c4"]), ("v_det", ["c5", "c6"])]
VIDEO_TEXTS = {
    "c1": "Welcome to this video on square matrices.", "c2": "We start with a picture of a transformation.",
    "c3": "Eigenvalues of a square matrix are the roots of its characteristic polynomial.",
    "c4": "Eigenvalues tell you how much the eigenvectors are stretched.",
    "c5": "Determinants measure how a matrix scales area.", "c6": "A determinant of zero means the matrix squashes space.",
}


def build_video_vault(root: Path, *, cover: bool = True) -> tuple[VaultPaths, Repository]:
    paths, repository = build_deliverable_vault(root, prerequisite=True)
    seed_reading(repository, source_id="src_vid", revision_id="rev_vid", extraction_id=VIDEO,
                 spans=[span for _section, spans in VIDEO_SECTIONS for span in spans], texts=VIDEO_TEXTS,
                 sections=VIDEO_SECTIONS, timed=True)
    with repository.connection() as connection:
        connection.execute("UPDATE source_artifacts SET display_title = 'Matrices, a video', reader_enabled = 1, "
                           "current_revision_id = 'rev_vid' WHERE id = 'src_vid'")
        connection.commit()
    vault = load_vault(paths.root)
    members = [member.model_dump(mode="json") for member in next(s for s in vault.source_sets if s.id == "sset_la").members]
    members.append({"source_id": "src_vid", "revision_id": "rev_vid", "default_role": "primary_textbook"})
    upsert_source_set(paths.root, {"id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
                                   "members": members})
    if cover:
        cover_all(paths, repository, "lo_eigen", "lo_det")
    return paths, repository


def prompt_context(prompt: str) -> dict[str, Any]:
    start = prompt.index("{", prompt.index("prompt_version"))
    return json.loads(prompt[start:])["context"]


class ChaptersJudgeFake(StructuredClientFake):
    provider_name = "fake_chapters_judge"
    provider_type = "codex_sdk"
    model = "fake-chapters-model"

    def __init__(self, *, fail: Exception | None = None) -> None:
        self.fail = fail
        self.contexts: list[dict[str, Any]] = []
        self.prompts: list[str] = []

    def supports(self, capability: str) -> bool:
        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION, ISOLATED_TURN, TOOL_FREE}

    def complete(self, request: Any) -> Any:
        context = prompt_context(request.prompt)
        self.contexts.append(context)
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 80, "resolved_model": self.model})
        if self.fail is not None:
            raise self.fail
        judgments = []
        for index, candidate in enumerate(context["candidates"]):
            words = candidate["words"].casefold()
            named = [lo for lo in context["learning_objects"] if lo["title"].split()[0].casefold()[:6] in words]
            starts = index == 0 or bool(named)
            judgments.append({
                "ref": candidate["ref"], "boundary": "starts" if starts else "continues",
                "rationale": "a new topic" if starts else "more of the same",
                "title": (named[0]["title"].casefold() if named else "introduction") if starts else "",
                "learning_objects": [lo["ref"] for lo in named][:1] if starts else [],
            })
        return request.result_model.model_validate({"judgments": judgments, "picks": []})

    @property
    def calls(self) -> int:
        return len(self.contexts)
