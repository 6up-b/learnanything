"""Owner decision 2026-11-23, "carried questions: Teacher context only": a lesson's brief carries the learner's open
carried questions (their words, since when, the passage beside them; let-go and fruitful ones out; a question beside
protected material out whole); with none open the lesson's prompt is byte for byte what it was; the router never
reads them."""

from __future__ import annotations

import json
from contextlib import closing
from typing import Any

from learnloop.db.connection import connect
from learnloop.teacher import carried as CQ
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients


def _rows(repository: Any, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _first_span(repository: Any, extraction_id: str) -> str:
    return _rows(repository, "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? "
                             "AND block_type = 'Text' ORDER BY ordinal LIMIT 1", (extraction_id,))[0][0]


# -- 2: carried questions in the Teacher's brief --------------------------------------------------------------------


def _carry(repository: Any, carried_id: str, text: str, anchor: dict[str, Any] | None = None) -> None:
    from learnloop.pads import carried as P

    P.carry(repository, carried_id=carried_id, text=text, origin_kind="typed", origin_ref=None, anchor=anchor,
            desk_id=None)


def _open(paths: Any, repository: Any) -> tuple[TeacherFake, dict[str, Any]]:
    from learnloop.teacher import service as S

    fake = TeacherFake([{"message": "Hello."}])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    return fake, view


def _teacher_prompt(fake: TeacherFake) -> str:
    return next(prompt for purpose, prompt in fake.prompts if purpose == "teacher_turn")


def _brief(fake: TeacherFake) -> dict[str, Any]:
    return fake.contexts[0]["brief"]


def test_a_lesson_with_no_open_carried_question_is_unchanged(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "a")
    plain, _view = _open(paths, repository)
    # A question let go and one that bore fruit are not open: the brief and prompt are the plain lesson's.
    other_paths, other_repository = build_teacher_vault(tmp_path / "b")
    from learnloop.pads import carried as P

    _carry(other_repository, "cq_gone", "what is a defective matrix?")
    _carry(other_repository, "cq_done", "why do rows swap signs?")
    P.mark(other_repository, event_id="ev_1", carried_id="cq_gone", event="let_go", expected_version=1, ref=None)
    P.mark(other_repository, event_id="ev_2", carried_id="cq_done", event="fruitful", expected_version=1, ref=None)
    closed, _view = _open(other_paths, other_repository)
    assert "carried_questions" not in _brief(plain) and "carried_questions" not in _brief(closed)
    for fake in (plain, closed):
        prompt = _teacher_prompt(fake)
        assert CQ.PROMPT_SUFFIX not in prompt and CQ.PARAGRAPH not in prompt
    assert _teacher_prompt(plain) == _teacher_prompt(closed)


def test_a_lesson_carries_the_learners_open_questions_with_the_passages_they_sit_beside(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    span = _first_span(repository, "ext_book")
    _carry(repository, "cq_1", "why is the determinant the product of the eigenvalues?",
           {"extraction_id": "ext_book", "span_id": span})
    _carry(repository, "cq_2", "does every matrix have an eigenvector?")
    from learnloop.pads import carried as P

    _carry(repository, "cq_later", "what about complex roots?")
    P.mark(repository, event_id="ev_n", carried_id="cq_later", event="not_now", expected_version=1, ref=None)
    fake, _view = _open(paths, repository)
    entry = _brief(fake)["carried_questions"]
    assert entry["version"] == CQ.VERSION and entry["about"] == CQ.ABOUT
    texts = [question["text"] for question in entry["questions"]]
    assert texts == ["why is the determinant the product of the eigenvalues?",
                     "does every matrix have an eigenvector?", "what about complex roots?"]
    beside = entry["questions"][0]["beside"]
    assert (beside["extraction_id"], beside["span_id"]) == ("ext_book", span) and beside["book"]
    assert entry["questions"][1]["beside"] is None and all(question["since"] for question in entry["questions"])
    prompt = _teacher_prompt(fake)
    assert CQ.PARAGRAPH in prompt and CQ.PROMPT_SUFFIX in prompt


def test_a_question_beside_protected_material_is_left_out_whole(tmp_path):
    from tests.source_retrieval_fakes import EXAM_QUESTION

    paths, repository = build_teacher_vault(tmp_path / "vault")
    exam_span = _first_span(repository, "ext_exam")
    _carry(repository, "cq_exam", "is this the exam's trick?", {"extraction_id": "ext_exam", "span_id": exam_span})
    _carry(repository, "cq_ok", "how do I find eigenvalues fast?")
    fake, _view = _open(paths, repository)
    entry = _brief(fake)["carried_questions"]
    assert [question["text"] for question in entry["questions"]] == ["how do I find eigenvalues fast?"]
    assert entry["left_out_protected"] == 1
    assert "exam's trick" not in fake.all_prompts() and exam_span not in json.dumps(entry)
    assert EXAM_QUESTION not in fake.all_prompts()


def test_the_router_reaches_no_carried_question_through_any_import():
    """Teacher context only: no router, plan, objective or serving module reaches a carried question."""

    import grimp

    graph = grimp.build_graph("learnloop", include_external_packages=False)
    sources = [module for module in graph.modules
               if module.split(".")[:2] in (["learnloop", "router"], ["learnloop", "router_objective"],
                                            ["learnloop", "daily_plan"], ["learnloop", "scheduling"])
               or module == "learnloop.router_objective_switches"]
    assert sources
    for forbidden in ("learnloop.teacher.carried", "learnloop.pads.carried"):
        assert not [module for module in sources if graph.chain_exists(importer=module, imported=forbidden)]
    # And lint-imports holds it from here on.
    from pathlib import Path

    assert 'id = "carried-questions-are-teacher-context-only"' in (
        Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
