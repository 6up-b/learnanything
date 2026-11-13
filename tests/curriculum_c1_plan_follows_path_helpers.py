"""What other test files use from ``tests/test_curriculum_c1_plan_follows_path.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
from dataclasses import dataclass


from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
from learnloop.daily_plan import engine as E
from learnloop.db.repositories import Repository
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.vault.loader import load_vault

from tests.deliverable_fixtures import DeliverableFake, build_deliverable_vault, cover_all
from tests.helpers import append_config_toml, set_algorithm_version
from tests.reading_path_fixtures import FixedClock, PathJudgeFake, call, context


TAG = LATEST_ALGORITHM_VERSION
C1_OFF = "[curriculum]\nplan_uses_path = false\n"
CURRICULUM_OFF = "[curriculum]\nenabled = false\n"
RW7B_OFF = "[reading_paths]\nplan_uses_path = false\n"
GUIDE_OFF = "[reading_paths]\nenabled = false\n"
#: The deliverable's path: Determinants (a prerequisite) in the notes, then
#: eigenvalues (core) in Lay, the second book; the notes' eigenvalue chapter is an
#: alternate. The predecessor's order opens the notes' "Chapter 5 Eigenvalues".
PRIMARIES = {"Eigenvalues": "5.2 The characteristic equation", "Determinants": "Chapter 3 Determinants"}


@dataclass
class C1Vault:
    paths: object
    repository: Repository
    goal_id: str
    clock: FixedClock

    @property
    def vault(self):
        return load_vault(self.paths.root)


def _as_you_read(repository: Repository, extraction_id: str = "ext_book") -> None:
    """The notes are read as you go (DL1 §6.10): the predecessor's order reads them."""

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO synthesis_manifests(id, manifest_hash, extraction_ids_json, brief_json, created_at) "
            "VALUES (?, ?, ?, ?, '2026-10-01T09:00:00Z')",
            (f"man_{extraction_id}", f"hash_{extraction_id}", json.dumps([extraction_id]),
             json.dumps({"practice_items": "as_you_read"})))
        connection.execute(
            "INSERT INTO synthesis_runs(id, manifest_id, mode, status, created_at, completed_at) "
            "VALUES (?, ?, 'bootstrap', 'completed', '2026-10-01T09:00:00Z', '2026-10-01T09:05:00Z')",
            (f"run_{extraction_id}", f"man_{extraction_id}"))
        connection.commit()


def _deliverable(paths, repository, sentence="eigenvalues for my midterm", *, due_at=None,
                 depth="learn_to_use_it") -> str:
    goal_id = DL.create_deliverable(load_vault(paths.root), repository, sentence, due_at=due_at)["goal_id"]
    DL.resolve(load_vault(paths.root), repository, goal_id, client=DeliverableFake())
    if depth:
        DL.add_input(load_vault(paths.root), repository, goal_id, "depth", text=depth)
    return goal_id


def _judge(c1: C1Vault, goal_id: str | None = None, **fake) -> DeliverableFake:
    judge = DeliverableFake(primaries=PRIMARIES, **fake)
    result = DP.judge(c1.vault, c1.repository, goal_id or c1.goal_id, client=judge)
    assert result.status in ("ready", "fresh"), result
    return judge


def _c1(tmp_path, monkeypatch, name="vault", *, version=TAG, config="", due_at=None, judge=True,
        book_path: dict | None = None) -> C1Vault:
    """A deliverable vault at ``version`` whose notes are read as you go, with a deliverable
    ("eigenvalues for my midterm", needing Determinants first) judged across both books;
    ``book_path`` judges RW7b's own path for the notes too (labels by section id)."""

    clock = getattr(monkeypatch, "_c1_clock", None) or FixedClock(monkeypatch)
    monkeypatch._c1_clock = clock
    paths, repository = build_deliverable_vault(tmp_path / name, prerequisite=True)
    set_algorithm_version(paths, version)
    _as_you_read(repository)
    cover_all(paths, repository, "lo_eigen", "lo_det")
    goal_id = _deliverable(paths, repository, due_at=due_at)
    c1 = C1Vault(paths, repository, goal_id, clock)
    if judge:
        _judge(c1)
    if book_path is not None:
        ctx = context(paths.root, reading_path_judge_client=PathJudgeFake(book_path), reading_path_inline=True)
        assert call(ctx, "reader.reading_path_set_depth",
                    {"extractionId": "ext_book", "depth": "learn_to_use_it"})["status"] == "ready"
    if config:  # last: C0a's coverage and C0b's judge are curriculum.enabled's
        append_config_toml(paths.root, config)
    return c1


def _step(c1: C1Vault, *, from_furthest=True, exam=None, allowed=None):
    env = E.PlanEnv(c1.vault, c1.repository)
    return E._reading_on_path(env, extraction_ids=None, from_furthest=from_furthest, exam=exam, allowed=allowed)


def _splits(repository) -> list[dict]:
    with repository.connection() as connection:
        return [json.loads(row[0]) for row in connection.execute(
            "SELECT split_json FROM daily_plans ORDER BY created_at, id")]


def _split(repository) -> dict:
    splits = _splits(repository)
    assert len(splits) == 1
    return splits[0]


def _complete(repository, extraction_id, *sections):
    for section in sections:
        repository.upsert_reader_section_progress(extraction_id=extraction_id, section_id=section, completed=True)


def _at(reading) -> tuple[str, str] | None:
    if reading is None:
        return None
    if isinstance(reading, dict):
        return (reading["extraction_id"], reading["section_id"])
    return (reading.extraction_id, reading.section_id)
