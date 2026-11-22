"""A section's end finishes it, and a quick check's close does not (algorithm tag mvp-0.63;
``docs/reviews/algorithm-mvp-0.63.md``).

Through the real progress report (``reader.mark_section_progress``), at both tags:

* at mvp-0.63 an acknowledged end observation (the section's last readable passage, observed during the learner's
  own reading, ``reachedEnd``) finishes the section once, through the same operation as the learner's explicit
  completion; the completion stores its cause and the tag it was written under; a second report returns the
  original completion, ends no second plan block and queues no second piece of work;
* at mvp-0.63 closing a quick check (``completedBy: check_closed``) and choosing what to do with its idea
  (``idea_chosen``) finish nothing;
* below the tag (mvp-0.62) every completion the Reader sends finishes the section as before, an end finishes
  nothing, and no cause or tag is stored;
* the upgrade turns no end recorded before it into a completion and leaves every recorded completion as it was; a
  whole-vault rebuild leaves them too.

The books: ``tests/mobile_v4_reader_helpers.py``'s three sections (``u1`` is b0-b2, ``u2`` b3-b4, ``u3`` b5-b6,
held out), through the desktop's handler and the phone host; ``tests/part_read_helpers.py``'s eigen book built
through Add (its later finish); ``tests/daily_plan_reading_helpers.py``'s plan with a reading block.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop.algorithm_versions import (
    COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SECTION_END_ALGORITHM_VERSION,
    SECTION_END_VERSIONS,
    SUCCESSOR_CHAIN,
    section_end_on,
)
from learnloop.db.repositories import Repository
from learnloop.reader.section_generation import DEFERRED_TO_PRIMARY
from tests.helpers import create_basic_vault, set_algorithm_version
from tests.mobile_host_helpers import HOSTNAME, Phone, pair, rows
from tests.ih2_lessons_compete_helpers import draw  # noqa: F401 - a fixture, used by parameter name
from tests.mobile_v4_reader_helpers import EXTRACTION, READER_APP, add_book, call, desktop, host, job

pytest.importorskip("starlette")

OLD, NEW = COMMITTED_CHECK_DELIVERY_ALGORITHM_VERSION, SECTION_END_ALGORITHM_VERSION
BOTH = pytest.mark.parametrize("tag", [OLD, NEW])


def test_the_tag():
    assert NEW == "mvp-0.63" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert SUCCESSOR_CHAIN[-2] == OLD == "mvp-0.62"
    assert SECTION_END_VERSIONS == frozenset({NEW})
    for version, on in ((OLD, False), (NEW, True)):
        assert section_end_on(SimpleNamespace(algorithms=SimpleNamespace(algorithm_version=version))) is on
    assert section_end_on(SimpleNamespace()) is False


@pytest.fixture
def tag():
    return NEW


@pytest.fixture
def world(tmp_path, tag):
    """The three-section book on a vault at ``tag`` (the latest unless a test parametrizes it), with the phone."""

    paths = create_basic_vault(tmp_path / "vault")
    if tag != LATEST_ALGORITHM_VERSION:
        set_algorithm_version(paths, tag)
    repository = Repository(paths.sqlite_path)
    add_book(paths.root, repository)
    device = pair(repository)
    app = host(paths.root, tmp_path / "pages")
    with TestClient(app, base_url=f"https://{HOSTNAME}") as client:
        yield {"phone": Phone(client, device, capabilities=READER_APP), "root": paths.root, "repo": repository}


@pytest.fixture
def started(monkeypatch):
    """Every start of a finished section's questions, in order (the real start is not run)."""

    import learnloop_sidecar.section_questions as section_questions

    calls: list[tuple] = []

    def start(ctx, vault, repository, extraction, section, **kwargs):
        # The real start claims the section with its stamp (a batch id), so a repeated finish never starts it again.
        calls.append((section,))
        repository.mark_section_generation(extraction_id=extraction, section_id=section, batch_id=f"batch_{section}")
        return f"batch_{section}"

    monkeypatch.setattr(section_questions, "start_section_questions", start)
    return calls


@pytest.fixture
def told(monkeypatch):
    """What the plan was told for every report (``note_reading_progress``'s keywords)."""

    import learnloop.daily_plan.engine as engine

    notes: list[dict] = []
    real = engine.note_reading_progress
    monkeypatch.setattr(engine, "note_reading_progress", lambda env, **kwargs: notes.append(kwargs) or real(env, **kwargs))
    return notes


def _report(ctx, section: str = "u1", *, ids=None, end: bool = False, **fields):
    params = {"extractionId": EXTRACTION, "sectionId": section, **fields}
    if ids is not None:
        params["seenSpanIds"] = ids
    if end:
        params["reachedEnd"] = True
    return call(ctx, "reader.mark_section_progress", params)


def _row(world, section: str = "u1") -> dict:
    return world["repo"].reader_section_progress_row(EXTRACTION, section) or {}


def _completion(world, section: str = "u1") -> tuple:
    row = _row(world, section)
    return row.get("completed_at") is not None, row.get("completion_cause"), row.get("completion_algorithm_version")


# -- the end, at both tags ---------------------------------------------------------------------------------------------


@BOTH
def test_both_tags_reading_to_the_end(world, tag, started, told):
    ctx = desktop(world["root"])
    _report(ctx, ids=["b0", "b1"], spansSeen=2, spanCount=3)
    reply = _report(ctx, ids=["b2"], end=True, spansSeen=3, spanCount=3)
    if tag == NEW:
        # Finished once by its end: the cause and the tag are stored, the questions are started, the plan is told.
        assert _completion(world) == (True, "reached_end", NEW)
        assert reply["progress"]["completedAt"] == _row(world)["completed_at"]
        assert started == [("u1",)]
        assert [note["completed"] for note in told] == [False, True]
    else:
        # mvp-0.62 exactly: the end is recorded and finishes nothing.
        assert _completion(world) == (False, None, None)
        assert reply["progress"]["completedAt"] is None and reply["enqueuedGeneration"] is False
        assert started == [] and [note["completed"] for note in told] == [False, False]
    # The end itself is recorded the same way at both tags.
    assert [(row["section_id"], row["span_id"]) for row in rows(world["repo"], "SELECT * FROM reader_section_ends")] == [
        ("u1", "b2")]


@BOTH
@pytest.mark.parametrize("by", ["check_closed", "idea_chosen"])
def test_both_tags_closing_a_quick_check_or_choosing_its_ideas_fate(world, tag, by, started, told):
    ctx = desktop(world["root"])
    reply = _report(ctx, completed=True, completedBy=by)
    if tag == NEW:
        assert _completion(world) == (False, None, None)
        assert reply["progress"]["completedAt"] is None and reply["enqueuedGeneration"] is False
        assert started == [] and [note["completed"] for note in told] == [False]
    else:
        # mvp-0.62 exactly: either finishes the section (no cause, no tag stored), and its questions start.
        assert _completion(world) == (True, None, None)
        assert started == [("u1",)] and [note["completed"] for note in told] == [True]


@BOTH
@pytest.mark.parametrize("by", [None, "learner"])
def test_both_tags_the_learner_says_they_read_it(world, tag, by, started):
    ctx = desktop(world["root"])
    # A short section that needs no scrolling: no passage, no end, only the learner's word.
    _report(ctx, "u2", completed=True, **({"completedBy": by} if by else {}))
    assert _completion(world, "u2") == ((True, "learner_said", NEW) if tag == NEW else (True, None, None))
    assert started == [("u2",)]


def test_the_end_and_the_explicit_completion_are_one_completion(world, started, told):
    ctx = desktop(world["root"])
    first = _report(ctx, ids=["b0", "b1", "b2"], end=True, spansSeen=3, spanCount=3)
    stamped = _row(world)
    # The learner presses "I've read this section" too, and the end is reported again (a retried save):
    again = _report(ctx, completed=True)
    replay = _report(ctx, ids=["b2"], end=True, spansSeen=3, spanCount=3)
    # The original completion, its cause and tag; one start of its questions; one completion told to the plan.
    assert _row(world)["completed_at"] == stamped["completed_at"] == first["progress"]["completedAt"]
    assert again["progress"]["completedAt"] == replay["progress"]["completedAt"] == stamped["completed_at"]
    assert _completion(world) == (True, "reached_end", NEW)
    assert started == [("u1",)]
    assert [note["completed"] for note in told] == [True, False, False]


@BOTH
def test_the_reply_and_the_progress_read_say_how_the_section_was_finished(world, tag, started):
    """The Reader shows a section finished by its end as read to its end (its position reaches the end, and the
    control's place says the reading finished it), after a restart too: the reply and ``reader.get_progress`` carry the
    stored cause. Below the tag nothing is stored, so nothing is said."""

    ctx = desktop(world["root"])
    ended = _report(ctx, ids=["b0", "b1", "b2"], end=True, spansSeen=3, spanCount=3)
    said = _report(ctx, "u2", completed=True)
    listed = {row["sectionId"]: row for row in call(ctx, "reader.get_progress", {"extractionId": EXTRACTION})["sections"]}
    if tag == NEW:
        assert ended["progress"]["completionCause"] == listed["u1"]["completionCause"] == "reached_end"
        assert said["progress"]["completionCause"] == listed["u2"]["completionCause"] == "learner_said"
    else:
        assert ended["progress"]["completionCause"] is None and listed["u1"]["completionCause"] is None
        assert said["progress"]["completionCause"] is None and listed["u2"]["completionCause"] is None


def test_the_learner_first_then_the_end_keeps_the_learners_completion(world, started):
    ctx = desktop(world["root"])
    _report(ctx, completed=True)
    _report(ctx, ids=["b0", "b1", "b2"], end=True, spansSeen=3, spanCount=3)
    assert _completion(world) == (True, "learner_said", NEW) and started == [("u1",)]


def test_no_end_no_finish(world, started):
    """Only the end observation finishes: a full count (the "left after 60 %" shortcut can fill it), every passage
    seen without an end, an end whose last passage was never seen, and a reveal finish nothing."""

    ctx = desktop(world["root"])
    _report(ctx, spansSeen=3, spanCount=3)
    _report(ctx, ids=["b0", "b1", "b2"], spansSeen=3, spanCount=3)
    _report(ctx, "u2", ids=["b3"], end=True, spansSeen=1, spanCount=2)
    _report(ctx, "u2", revealed=True)
    assert _completion(world) == (False, None, None) and _completion(world, "u2") == (False, None, None)
    assert started == []


def test_an_end_on_a_section_already_finished_below_the_tag_changes_nothing(tmp_path, started):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    repository = Repository(paths.sqlite_path)
    add_book(paths.root, repository)
    _report(desktop(paths.root), completed=True, completedBy="check_closed")
    before = repository.reader_section_progress_row(EXTRACTION, "u1")
    set_algorithm_version(paths, NEW)
    _report(desktop(paths.root), ids=["b0", "b1", "b2"], end=True, spansSeen=3, spanCount=3)
    after = repository.reader_section_progress_row(EXTRACTION, "u1")
    # The original completion (written below the tag, so without a cause or tag) is the one kept; nothing starts again.
    kept = ("completed_at", "completion_cause", "completion_algorithm_version", "generation_batch_id")
    assert {key: after[key] for key in kept} == {key: before[key] for key in kept}
    assert after["completion_cause"] is None and len(started) == 1


# -- the phone ---------------------------------------------------------------------------------------------------------


def test_the_phones_end_finishes_the_section_once_for_the_desktop_to_write(world):
    params = {"extractionId": EXTRACTION, "sectionId": "u2", "seenSpanIds": ["b3", "b4"], "reachedEnd": True,
              "spansSeen": 2, "spanCount": 2}
    job(world["phone"], "reader.mark_section_progress", params, "end_u2")
    first = _row(world, "u2")
    assert _completion(world, "u2") == (True, "reached_end", NEW)
    # The phone host leaves the writing to the desktop, as a finish there always has.
    assert first["generation_batch_id"] == DEFERRED_TO_PRIMARY
    # A duplicate delivery (the same intent again) and a later report carrying the end again change nothing.
    job(world["phone"], "reader.mark_section_progress", params, "end_u2")
    job(world["phone"], "reader.mark_section_progress", params, "end_u2_again")
    assert _row(world, "u2")["completed_at"] == first["completed_at"]
    assert _row(world, "u2")["generation_batch_id"] == DEFERRED_TO_PRIMARY
    assert len(rows(world["repo"], "SELECT * FROM reader_section_ends WHERE section_id = 'u2'")) == 1


@pytest.mark.parametrize("tag", [OLD])
def test_below_the_tag_the_phones_end_finishes_nothing(world, tag):
    job(world["phone"], "reader.mark_section_progress",
        {"extractionId": EXTRACTION, "sectionId": "u2", "seenSpanIds": ["b3", "b4"], "reachedEnd": True,
         "spansSeen": 2, "spanCount": 2}, "end_u2")
    assert _completion(world, "u2") == (False, None, None) and _row(world, "u2")["generation_batch_id"] is None


# -- the plan's reading block ------------------------------------------------------------------------------------------


def _plan_ctx(tmp_path, monkeypatch, draw, tag):
    from tests.daily_plan_reading_helpers import DAY1, _Clock, _seed_as_you_read
    from tests.helpers import create_daily_plan_vault
    from tests.ih2_lessons_compete_helpers import QUIET

    draw.never_stop, draw.avoid = True, ("lesson_offer:",)
    paths = create_daily_plan_vault(tmp_path / "vault", plan_toml=QUIET)
    if tag != LATEST_ALGORITHM_VERSION:
        set_algorithm_version(paths, tag)
    _seed_as_you_read(paths)
    _Clock(monkeypatch, DAY1)
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    call(ctx, "set_plan_minutes", {"minutes": 40})
    session_id = call(ctx, "start_session", {"availableMinutes": 40})["sessionId"]
    for _ in range(20):
        step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
        if step["kind"] == "reading":
            return ctx, session_id, step["reading"]
        assert step["kind"] != "done", "no reading step"
        call(ctx, "next_plan_item", {"sessionId": session_id, "skipPracticeItemId": step["practiceItemId"]})
    raise AssertionError("no reading step")


def _block_ends(ctx) -> list[str]:
    return [row["detail_json"] for row in rows(ctx.repository,
            "SELECT detail_json FROM attention_block_events WHERE kind = 'block_ended' ORDER BY rowid")]


@BOTH
def test_both_tags_the_end_and_the_learners_word_end_one_reading_block(tmp_path, monkeypatch, draw, tag):
    from tests.daily_plan_reading_helpers import _sections

    ctx, session_id, reading = _plan_ctx(tmp_path, monkeypatch, draw, tag)
    section = next(row for row in _sections(ctx.repository, "ext_book") if row["id"] == reading["sectionId"])
    spans = list(section["span_ids"])
    params = {"extractionId": "ext_book", "sectionId": reading["sectionId"], "spansSeen": len(spans),
              "spanCount": len(spans), "seenSpanIds": spans, "reachedEnd": True}
    before = len(_block_ends(ctx))
    call(ctx, "reader.mark_section_progress", params)
    ended_by_the_end = len(_block_ends(ctx)) - before
    call(ctx, "reader.mark_section_progress", {"extractionId": "ext_book", "sectionId": reading["sectionId"],
                                               "completed": True})
    call(ctx, "reader.mark_section_progress", params)
    ends = _block_ends(ctx)[before:]
    # One ending at both tags: by the end at mvp-0.63, by the learner's word below it.
    assert ended_by_the_end == (1 if tag == NEW else 0)
    assert len(ends) == 1 and "section_completed" in ends[0]
    plan = call(ctx, "next_plan_item", {"sessionId": session_id})["plan"]
    block = next(block for block in plan["blocks"] if block["reading"])
    assert block["outcome"] == "section_completed" and block["status"] == "done"


# -- the later finish, and an end before the build ---------------------------------------------------------------------


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


def _read_to_the_end(book, *names):
    from tests.part_read_helpers import build
    from tests.ux_phase1_add_source_helpers import call as add_call

    spans = book.spans()
    section = spans[names[0]][0]
    reply = add_call(book.ctx, "reader.mark_section_progress", {
        "extractionId": book.extraction_id, "sectionId": section, "spansSeen": 6, "spanCount": 6,
        "seenSpanIds": [spans[name][1] for name in names], "reachedEnd": True})
    build(book)
    return reply


def test_reading_to_the_end_writes_only_the_topics_the_part_read_left(tmp_path, isolated_config):
    from tests.part_read_helpers import SeenWriter, book_ctx, build

    writer = SeenWriter()
    book = book_ctx(tmp_path, writer=writer)
    build(book)
    book.read("P1", "P2", "P3", "P4")
    first = sorted(topic for topics in writer.calls for topic in topics)
    assert first == ["lo_diagonalize_symmetric", "lo_early"]

    done = _read_to_the_end(book, "P5", "P6")

    assert done["enqueuedGeneration"] is True and done["progress"]["completedAt"] is not None
    assert book.claimed() == {"lo_diagonalize_symmetric": "part_read", "lo_early": "part_read",
                              "lo_straddle": "section_finished", "lo_late": "section_finished",
                              "lo_cross": "section_finished"}
    asked = [topic for topics in writer.calls for topic in topics]
    assert sorted(asked[2:]) == ["lo_cross", "lo_late", "lo_straddle"] and len(asked) == len(set(asked)) == 5
    section = book.spans()["P1"][0]
    assert book.repo.reader_section_progress_row(book.extraction_id, section)["completion_cause"] == "reached_end"
    # Reaching the end again, and pressing "I've read this section", ask nothing more.
    _read_to_the_end(book, "P6")
    book.finish("P1")
    assert len([topic for topics in writer.calls for topic in topics]) == 5


def test_reaching_the_end_before_the_build_waits_for_it_then_writes(tmp_path, isolated_config):
    from learnloop.reader.section_generation import WAITING_FOR_BUILD
    from tests.part_read_helpers import SeenWriter, book_ctx, build, build_until_synthesis

    writer = SeenWriter()
    book = book_ctx(tmp_path, writer=writer)
    build_until_synthesis(book)
    from tests.ux_phase1_add_source_helpers import call as add_call

    spans = book.spans()
    section = spans["P1"][0]
    reply = add_call(book.ctx, "reader.mark_section_progress", {
        "extractionId": book.extraction_id, "sectionId": section, "spansSeen": 6, "spanCount": 6,
        "seenSpanIds": [spans[name][1] for name in ("P1", "P2", "P3", "P4", "P5", "P6")], "reachedEnd": True})
    assert reply["progress"]["completedAt"] is not None and reply["waitingForBuild"] is True
    assert book.repo.reader_section_progress_row(book.extraction_id, section)["generation_batch_id"] == WAITING_FOR_BUILD
    assert writer.calls == []
    build(book)
    asked = sorted(topic for topics in writer.calls for topic in topics)
    assert set(asked) >= {"lo_early", "lo_straddle", "lo_late", "lo_cross"} and len(asked) == len(set(asked))


# -- the upgrade, and a rebuild ----------------------------------------------------------------------------------------


def _dump(repository: Repository, table: str) -> list[dict]:
    return rows(repository, f"SELECT * FROM {table} ORDER BY extraction_id, section_id")


def test_the_upgrade_finishes_nothing_recorded_before_it_and_a_new_end_finishes_once(tmp_path, started, told):
    from learnloop.ops.upgrades import upgrade
    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
    from learnloop.vault.loader import load_vault

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    repository = Repository(paths.sqlite_path)
    add_book(paths.root, repository)
    ctx = desktop(paths.root)
    # History below the tag: u1 finished by its quick check's close; u2 read to its end, never finished.
    _report(ctx, completed=True, completedBy="check_closed")
    _report(ctx, "u2", ids=["b3", "b4"], end=True, spansSeen=2, spanCount=2)
    progress, ends = _dump(repository, "reader_section_progress"), _dump(repository, "reader_section_ends")
    assert [row["section_id"] for row in progress if row["completed_at"]] == ["u1"]

    result = upgrade(paths.root, to=NEW)
    assert result.upgraded, result.problems
    # Nothing recorded is turned into a completion or reinterpreted, by the activation or by a whole-vault rebuild.
    assert _dump(repository, "reader_section_progress") == progress
    assert _dump(repository, "reader_section_ends") == ends
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert _dump(repository, "reader_section_progress") == progress
    assert _dump(repository, "reader_section_ends") == ends

    # A new end after the upgrade finishes u2, once, with its cause and the tag.
    after = desktop(paths.root)
    _report(after, "u2", ids=["b4"], end=True, spansSeen=2, spanCount=2)
    _report(after, "u2", ids=["b4"], end=True, spansSeen=2, spanCount=2)
    finished = [row for row in _dump(repository, "reader_section_progress") if row["completed_at"]]
    assert [(row["section_id"], row["completion_cause"], row["completion_algorithm_version"]) for row in finished] == [
        ("u1", None, None), ("u2", "reached_end", NEW)]
    assert started == [("u1",), ("u2",)]
    assert _dump(repository, "reader_section_ends") == ends  # the end row keeps its first time and origin
