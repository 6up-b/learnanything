"""What other test files use from ``tests/test_learner_data_relax_2.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build_figure_vault,
    flagship,
    rows,
    seed_probability_book,
    set_config,
    upsert_source_set,
)
from tests.mcp_world import LO, _attempt, build_world


#: Newer than every ordinary answer, each on protected work: they must be
#: skipped (the two shown answers are older, unprotected ones).
NEWER_EXAM = "NEWER_EXAM_WORK_8812 eigenvalues five and two"
NEWER_COLD = "NEWER_COLD_ANSWER_4471 any row works"
NEWER_RESERVED = "NEWER_RESERVED_ANSWER_3302"
EXAM_DERIVED = "EXAM_DERIVED_MISCONCEPTION_7710 thinks eigenvalues add"
SOURCE_SET = {
    "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
    "members": [
        {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
        {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
        {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"},
        {"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "primary_textbook"},
    ],
}


def _link(repository, lo_id: str = LO, span_id: str = "p3") -> None:
    """The passage teaches ``lo_id`` (a current primary source link)."""

    from learnloop.ingest.locators import format_block_span

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO entity_source_links (id, entity_type, entity_id, source_id, revision_id, locator, relation, "
            "extraction_id, status, created_at) VALUES (?, 'learning_object', ?, 'src_prob', 'rev_prob', ?, "
            "'primary', ?, 'current', '2026-09-01T00:00:00Z')",
            (f"esl_{lo_id}_{span_id}", lo_id, format_block_span(EXTRACTION, span_id), EXTRACTION))
        connection.commit()


def _history_world(tmp_path, *, switch: bool | None = None, rich: bool = False):
    """The chat frontend's seeded world (protected work planted with
    distinctive strings) plus the probability book, whose §5.4 equation
    block teaches its LO; newer protected answers and an exam-derived
    misconception on top."""

    world = build_world(tmp_path / "w")
    paths, repository = world.paths, world.repository
    values = {"sketch_enabled": False, "rich_tiers_enabled": rich}
    if rich:
        values["manim_opt_in"] = "standing"
    if switch is not None:
        values["author_learner_state"] = switch
    set_config(paths, "figures", **values)
    seed_probability_book(repository)
    upsert_source_set(paths.root, SOURCE_SET)
    _link(repository)
    with repository.connection() as connection:
        _attempt(connection, "att_new_exam", "pi_own", "2026-09-20T09:00:00Z", answer=NEWER_EXAM, correctness=1.0,
                 attempt_type="exam_attempt")
        _attempt(connection, "att_new_cold", "pi_cold", "2026-09-21T09:00:00Z", answer=NEWER_COLD, correctness=1.0)
        _attempt(connection, "att_new_reserved", "pi_reserved", "2026-09-22T09:00:00Z", answer=NEWER_RESERVED,
                 correctness=1.0)
        connection.execute(
            "INSERT INTO error_events(id, attempt_id, learning_object_id, error_type, severity, is_misconception, "
            "status, created_at, misconception_id, misconception_statement) VALUES ('e_exam', 'att_exam', ?, "
            "'misconception', 0.7, 1, 'active', '2026-09-23T00:00:00Z', 'mc_exam', ?)", (LO, EXAM_DERIVED))
        connection.execute(
            "INSERT INTO misconceptions(id, learning_object_id, statement, severity, status, "
            "source_error_event_ids_json, created_at, updated_at) VALUES ('mc_exam', ?, ?, 0.7, 'active', "
            "'[\"e_exam\"]', '2026-09-23T00:00:00Z', '2026-09-23T00:00:00Z')", (LO, EXAM_DERIVED))
        connection.commit()
    return world


def _plain_vault(tmp_path, *, switch: bool | None = None):
    """The figure tests' vault (no answers, no statements) with the same link."""

    paths, repository = build_figure_vault(tmp_path / "plain")
    if switch is not None:
        set_config(paths, "figures", author_learner_state=switch)
    _link(repository)
    return paths, repository


def _rich_history_rig(tmp_path, monkeypatch):
    """The history world with Manim figures on (the rich job rig's runner and fakes)."""

    from learnloop.content.pipeline.runner import IngestRunner, RunnerServices
    from tests import rich_fixtures as RF
    from tests.figure_rich_job_helpers import WHY, _Rig

    world = _history_world(tmp_path, rich=True)
    RF.ready_manim(monkeypatch)
    rig = _Rig.__new__(_Rig)
    rig.paths, rig.repository = world.paths, world.repository
    rig.author = AuthorFake([("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    rig.rich_author = RF.RichAuthorFake()
    rig.renders = RF.Renders()
    rig.functions = RF.InProcessRunner()
    rig.ingest = IngestRunner(rig.repository, vault_root=rig.paths.root, worker_id="w1", services=RunnerServices(
        figure_rich_client_factory=lambda ctx: rig.rich_author, figure_rich_renderer=rig.renders,
        figure_function_runner=rig.functions))
    rig.batches = []
    return rig


def _switch_off(paths) -> None:
    """``figures.author_learner_state = false`` in place (the section exists)."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    if "author_learner_state = true" in text:
        text = text.replace("author_learner_state = true", "author_learner_state = false")
    else:
        text = text.replace("\n[figures]\n", "\n[figures]\nauthor_learner_state = false\n", 1)
    config.write_text(text, encoding="utf-8")
    assert "author_learner_state = false" in text


def _make_exam_material(rig, item_id: str = "pi_edited") -> None:
    """The item the shown answers were on now comes from the exam source."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    path = rig.paths.practice_item_path("linear-algebra", item_id)
    item = read_yaml(path)
    item["provenance"] = {"origin": "human", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": "src_exam", "extraction_id": "ext_exam", "span_ids": ["s2"]}]}
    write_yaml(path, item)


def _rich_row(repository) -> dict:
    from learnloop.db.stores import figures as store

    (row,) = [found for found in rows(repository, "interactive_figures") if found["tier"] == "manim"]
    with repository.connection() as connection:
        return store.figure(connection, row["id"])
