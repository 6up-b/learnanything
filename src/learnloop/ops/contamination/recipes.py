"""Declared embedding recipes for Slice 2 T4's contamination record kinds (R3).

Each record kind names the exact canonical or LLM-written text it embeds. Three
are read from the vault database, so they live here rather than in the default
vault-content registry (``learnloop.vault.embedding_recipes``): they are
embedded only by ``learnloop contamination embed``, never by the default
backfill. ``item/stem`` is the Phase 1 recipe itself, shared so one command
embeds everything the report reads.

No recipe reads a learner's question, response, grade or learner state: the
tutor and reader answers are the model's own text.
"""
from __future__ import annotations

from collections.abc import Iterator, Mapping
import json
from types import MappingProxyType
from typing import Any

from learnloop.content.authoring.practice_leakage import held_out_spans
from learnloop.db.repositories import Repository
from learnloop.reader.reader_dialogue import surface_statement_text
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, EmbeddingRecipe
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.paths import VaultPaths


def expected_answer_text(item: PracticeItem) -> str:
    """The canonical expected answer: authored text, or sorted JSON for a dict."""

    expected = item.expected_answer
    if isinstance(expected, str):
        return expected
    return json.dumps(expected, sort_keys=True, ensure_ascii=False)


def read_only_repository(loaded: LoadedVault) -> Repository | None:
    """Attach without migrating; ``None`` before the vault has a database."""

    path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if not path.exists():
        return None
    return Repository.attach(path, read_only=True)


def answered_question_events(repository: Repository) -> list[dict]:
    """Answered tutor turns T4 scans: item-bound, or in the reader context."""

    return [
        event for event in repository.question_events(answer_status="answered")
        if (event.get("answer_md") or "").strip()
        and (event.get("practice_item_id") or event.get("context") == "reader")
    ]


def _expected_answers(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    for item_id, item in sorted(loaded.practice_items.items()):
        if item.status != "retired":
            yield item_id, expected_answer_text(item)


def _question_event_answers(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    repository = read_only_repository(loaded)
    if repository is None:
        return
    for event in answered_question_events(repository):
        yield str(event["id"]), str(event["answer_md"])


def assessment_reservations(repository: Repository) -> list[dict[str, Any]]:
    """Every assessment reservation, live or closed, with its immutable surface.

    Rows are ``{"reservation": ..., "surface": ...}`` in surface, then
    reservation order. A surface's text never changes (surfaces are
    content-addressed), so the text a reader answer is compared with is the
    one that was reserved at the time."""

    with repository.connection() as connection:
        rows = connection.execute(
            "SELECT r.id AS r_id, r.status AS r_status, r.reserved_at AS r_reserved_at, "
            "r.closed_at AS r_closed_at, r.administration_id AS r_administration_id, s.* "
            "FROM activity_surface_reservations r JOIN activity_surfaces s ON s.id = r.surface_id "
            "WHERE r.purpose = 'assessment' ORDER BY s.id, r.reserved_at, r.id"
        ).fetchall()
    result = []
    for row in rows:
        values = dict(row)
        reservation = {key[2:]: values.pop(key) for key in list(values) if key.startswith("r_")}
        values["surface"] = json.loads(values.get("surface_json") or "{}")
        result.append({"reservation": reservation, "surface": values})
    return result


def _assessment_surfaces(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    repository = read_only_repository(loaded)
    if repository is None:
        return
    seen: set[str] = set()
    for row in assessment_reservations(repository):
        surface = row["surface"]
        if str(surface["id"]) not in seen:
            seen.add(str(surface["id"]))
            yield str(surface["id"]), surface_statement_text(surface)


def _held_out_exam_spans(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    repository = read_only_repository(loaded)
    if repository is None:
        return
    for span in held_out_spans(loaded, repository):
        yield span.key, span.text


#: Slice 2 T4 record kinds, plus the shared Phase 1 ``item/stem`` recipe.
CONTAMINATION_RECIPES: Mapping[str, EmbeddingRecipe] = MappingProxyType({
    "item/stem": EMBEDDING_RECIPES["item/stem"],
    "item/expected_answer": EmbeddingRecipe(
        "item", "expected_answer", 1,
        "Canonical practice item expected answer only (authored text, or sorted "
        "JSON for a structured answer); excludes retired items, the prompt, hints, "
        "rubric and learner responses.",
        _expected_answers,
    ),
    "question_event/answer": EmbeddingRecipe(
        "question_event", "answer", 1,
        "The tutor's own answer text (answer_md) of an answered question event "
        "bound to a practice item or asked in the reader; excludes the learner's "
        "question, the item and any grading material.",
        _question_event_answers,
    ),
    "surface/statement": EmbeddingRecipe(
        "surface", "statement", 1,
        "The reserved assessment surface text the reader reveal floor compares "
        "against (prompt, statement, question and expected answer); every surface "
        "that has held an assessment reservation, live or closed, so reader answers "
        "given while it was reserved can still be audited.",
        _assessment_surfaces,
    ),
    "exam_span/text": EmbeddingRecipe(
        "exam_span", "text", 1,
        "The block text of each held-out exam span (exam-role units' held-out "
        "assessment signals and whole held_out_evaluation units), keyed "
        "extraction/span.",
        _held_out_exam_spans,
    ),
})
