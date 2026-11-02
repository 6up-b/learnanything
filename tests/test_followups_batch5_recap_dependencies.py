"""Follow-ups batch 5, Codex review (job 20261102-102846-iWwlFV): an earlier lesson's recap carries the
protection dependencies of everything it could have been written from.

* F1: a recap inherited from an earlier lesson (through the brief's ``last_lessons`` or a ``read_history``
  result) is part of what a lesson relied on: lesson 2 quotes lesson 1's recap of passage P without reading
  P itself; once P is held out, a fresh lesson leaves out lesson 2's recap as well as lesson 1's. Checked
  transitively, memoized, and fail closed when an inherited recap's lesson cannot be found.
* F2: a Reader note the lesson was given (its header in ``your_notes``, its text through ``read_note``) is
  part of it too: once only the note's own source becomes protected, the recap is left out. The note is
  resolved from its link row (append-only), so later link changes cannot drop the dependency.

Real brief, protection, gate and prompt builders; synthetic vaults; every model a fake.
"""

from __future__ import annotations

import json

from learnloop.algorithm_versions import TEACHER_ALGORITHM_VERSION
from learnloop.teacher import brief as B
from learnloop.teacher import notes as TN
from learnloop.teacher import service as S
from learnloop.vault.loader import load_vault
from tests.helpers import set_algorithm_version
from tests.notes_fixtures import add_annotation
from tests.reading_path_fixtures import call
from tests.section_coverage_fixtures import hold_out
from tests.teacher_fakes import TeacherFake, build_teacher_vault, clients, close_turn
from tests.test_notes_linked import _deliverable

PASSAGE = "The eigenvalues of A are the roots of the characteristic equation det(A - tI) = 0."
PASSAGE_WORDS = "roots of the characteristic equation"
READ_LAY = {"message": "Let me read.", "requests": [{"action": "read_source", "refs": ["ext_lay/lay_char"]}]}


def _lesson(paths, repository, opening, recap):
    fake = TeacherFake(list(opening))
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    fake.turns = [close_turn(recap=recap)]
    closed = S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action="stop", payload={},
                         clients=clients(fake))
    assert closed["closed"]
    return fake, view["lesson_id"]


def _prior(fake, lesson_id):
    return next(entry for entry in fake.contexts[0]["brief"]["last_lessons"] if entry["id"] == f"l:{lesson_id}")


def _chain(tmp_path):
    """Lesson 1 reads P and recaps it; lesson 2 never reads Lay, is given lesson 1's recap and quotes it."""

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _fake1, first = _lesson(paths, repository, [READ_LAY, {"message": "Read it."}], f"Remember: {PASSAGE}")
    fake2, second = _lesson(paths, repository, [{"message": "Hello again."}], f"Carried over: {PASSAGE}")
    # Lesson 2 was given lesson 1's recap (protection unchanged then) and read nothing from Lay itself.
    assert _prior(fake2, first)["recap"] == f"Remember: {PASSAGE}"
    book = S.load_state(repository, second).book
    assert all(p["extraction_id"] != "ext_lay" for p in book.passages.values())
    return paths, repository, first, second


def _open_payload(repository, lesson_id):
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT p.turn_id, p.payload_json FROM lesson_turn_payloads p JOIN lesson_turns t ON t.id = p.turn_id "
            "WHERE t.lesson_id = ? AND t.action = 'open'", (lesson_id,)).fetchone()
    return row[0], json.loads(row[1])


def _rewrite_open(repository, lesson_id, change):
    turn_id, payload = _open_payload(repository, lesson_id)
    change(payload)
    with repository.atomic():
        repository.connection().execute("UPDATE lesson_turn_payloads SET payload_json = ? WHERE turn_id = ?",
                                        (json.dumps(payload), turn_id))


# --- F1: inherited recaps ----------------------------------------------------------------------------


def test_f1_a_recap_inherited_through_last_lessons_is_left_out_with_its_source(tmp_path):
    paths, repository, first, second = _chain(tmp_path)
    hold_out(repository, "lay_char")
    fake = TeacherFake([{"message": "Fresh start."}])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake))
    assert not view["closed"]
    assert _prior(fake, first)["recap"] is None
    later = _prior(fake, second)
    assert later["recap"] is None and later["recap_omitted"] == B.RECAP_OMITTED
    assert all(PASSAGE_WORDS not in prompt for _purpose, prompt in fake.prompts)


def test_f1_a_recap_inherited_through_read_history_is_left_out_with_its_source(tmp_path):
    paths, repository, first, _second = _chain(tmp_path)
    # Lesson 3 is given lesson 1's recap only through read_history (its brief's copy scrubbed), then quotes it.
    reads = {"message": "Let me look back.", "requests": [{"action": "read_history", "refs": [f"l:{first}"]}]}
    _fake3, third = _lesson(paths, repository, [reads, {"message": "Thanks."}], f"From history: {PASSAGE}")

    def scrub(payload):
        for entry in payload["brief"]["last_lessons"]:
            entry["recap"] = None
    _rewrite_open(repository, third, scrub)
    vault = load_vault(paths.root)
    assert B.recap_admissible(vault, repository, third)
    hold_out(repository, "lay_char")
    assert not B.recap_admissible(load_vault(paths.root), repository, third)


def test_f1_the_inherited_recap_stays_while_its_source_is_teachable(tmp_path):
    paths, repository, first, second = _chain(tmp_path)
    hold_out(repository, "lay_ortho")  # protection moved elsewhere: both recaps re-check clean
    fake = TeacherFake([{"message": "Fresh start."}])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake))
    assert _prior(fake, first)["recap"] == f"Remember: {PASSAGE}"
    assert _prior(fake, second)["recap"] == f"Carried over: {PASSAGE}"


def test_f1_an_inherited_recap_whose_lesson_cannot_be_found_fails_closed(tmp_path):
    paths, repository, first, second = _chain(tmp_path)

    def orphan(payload):
        for entry in payload["brief"]["last_lessons"]:
            if entry["id"] == f"l:{first}":
                entry["id"] = "l:les_missing"
    _rewrite_open(repository, second, orphan)
    assert B.recap_admissible(load_vault(paths.root), repository, second)  # unchanged protection: as recorded
    hold_out(repository, "lay_ortho")
    assert not B.recap_admissible(load_vault(paths.root), repository, second)


# --- F2: notes the lesson was given ------------------------------------------------------------------

LAY_SENTINEL = "LAYRECAPSENTINEL-5e07"


def _noted(tmp_path):
    """C4's deliverable vault with a Reader note beside Lay's eigenvector section (ext_lay s2) linked to
    lo_eigen by the path's judgment; the lesson's own book comes from ext_book."""

    paths, repository, ctx, goal_id, _corpus, _notes = _deliverable(tmp_path)
    key = "annotation:" + add_annotation(repository, f"Av = lv, in Lay's words: {LAY_SENTINEL}",
                                         extraction_id="ext_lay", span_id="s2", source_id="src_lay",
                                         revision_id="rev_lay")
    call(ctx, "notes.path", {"goal_id": goal_id})
    set_algorithm_version(paths, TEACHER_ALGORITHM_VERSION)
    return paths, repository, key


def _lay_note_id(context):
    return next(note["id"] for node in context["brief"]["nodes"] for note in node.get("your_notes") or []
                if LAY_SENTINEL in str(note.get("line")))


def _read_lay_note(context):
    return {"message": "Let me see what you wrote.", "requests": [{"action": "read_note",
                                                                   "refs": [_lay_note_id(context)]}]}


def _noted_lesson(paths, repository, opening):
    fake, lesson_id = _lesson(paths, repository, opening, f"Your note said: {LAY_SENTINEL}")
    book = S.load_state(repository, lesson_id).book
    assert all(p["extraction_id"] != "ext_lay" for p in book.passages.values())
    return fake, lesson_id


def test_f2_a_recap_after_read_note_is_left_out_once_only_the_note_s_source_is_protected(tmp_path):
    paths, repository, _key = _noted(tmp_path)
    fake1, first = _noted_lesson(paths, repository, [_read_lay_note, {"message": "Thanks."}])
    assert LAY_SENTINEL in json.dumps(fake1.contexts[1]["results"])  # the note's text reached the teacher
    assert B.recap_admissible(load_vault(paths.root), repository, first, notes_check=TN.notes_still_deliverable)
    hold_out(repository, "lay_eigen")
    fake = TeacherFake([{"message": "Fresh start."}])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake))
    prior = _prior(fake, first)
    assert prior["recap"] is None and prior["recap_omitted"] == B.RECAP_OMITTED
    assert all(LAY_SENTINEL not in prompt for _purpose, prompt in fake.prompts)


def test_f2_a_recap_after_a_your_notes_header_is_left_out_too(tmp_path):
    paths, repository, _key = _noted(tmp_path)
    fake1, first = _noted_lesson(paths, repository, [{"message": "Hello."}])
    assert LAY_SENTINEL in json.dumps(fake1.contexts[0]["brief"]["nodes"])  # the header's line carries it
    hold_out(repository, "lay_eigen")
    fake = TeacherFake([{"message": "Fresh start."}])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake))
    assert _prior(fake, first)["recap"] is None
    assert all(LAY_SENTINEL not in prompt for _purpose, prompt in fake.prompts)


def test_f2_the_note_dependency_outlives_a_later_link_change(tmp_path):
    paths, repository, key = _noted(tmp_path)
    fake1, first = _noted_lesson(paths, repository, [_read_lay_note, {"message": "Thanks."}])
    note_id = _lay_note_id(fake1.contexts[0])
    # The learner hides the link afterwards (an appended row); the delivered link row still names the note.
    from learnloop.db.stores import learner_notes as store

    with repository.atomic():
        row = dict(next(r for r in store.links(repository.connection(), note_key=key) if f"n:{r['id']}" == note_id))
        row.update({"id": "nl_hidden_b5", "authorship": "learner", "status": "rejected",
                    "created_at": "2026-11-02T12:00:00Z"})
        store.insert_link(repository.connection(), row)
    hold_out(repository, "lay_eigen")
    assert not B.recap_admissible(load_vault(paths.root), repository, first, notes_check=TN.notes_still_deliverable)


def test_f2_the_recap_stays_when_protection_moved_elsewhere(tmp_path):
    paths, repository, _key = _noted(tmp_path)
    _fake1, first = _noted_lesson(paths, repository, [_read_lay_note, {"message": "Thanks."}])
    hold_out(repository, "lay_ortho")
    fake = TeacherFake([{"message": "Fresh start."}])
    S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                  clients=clients(fake))
    assert _prior(fake, first)["recap"] == f"Your note said: {LAY_SENTINEL}"


def test_f2_without_the_notes_check_a_lesson_that_was_given_notes_fails_closed(tmp_path):
    paths, repository, _key = _noted(tmp_path)
    _fake1, first = _noted_lesson(paths, repository, [_read_lay_note, {"message": "Thanks."}])
    hold_out(repository, "lay_ortho")
    vault = load_vault(paths.root)
    assert not B.recap_admissible(vault, repository, first)
    assert B.recap_admissible(vault, repository, first, notes_check=TN.notes_still_deliverable)


# --- Codex re-review F3: a long chain of inherited recaps ---------------------------------------------


def _synthetic_chain(monkeypatch, length, *, last=None, back_edge=None):
    """``les_0`` <- ``les_1`` <- ... : each lesson was given only its predecessor's recap, under a recorded
    protection that no longer matches (so every link is re-checked). ``last``: what ``les_0`` was given;
    ``back_edge``: an extra inherited lesson for ``les_0`` (a cycle)."""

    def exposure(_repository, lesson_id):
        index = int(lesson_id.split("_")[1])
        if index >= length:
            return None
        lessons = {f"les_{index - 1}"} if index else set(filter(None, [last, back_edge]))
        return B._Exposure({"version": "older"}, B.SourceBook(), set(), lessons, set())

    monkeypatch.setattr(B, "_lesson_exposure", exposure)


def test_f3_a_chain_longer_than_the_recursion_limit_is_judged_without_crashing(tmp_path, monkeypatch):
    import sys

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    length = sys.getrecursionlimit() + 200
    _synthetic_chain(monkeypatch, length)
    memo: dict[str, bool] = {}
    assert B.recap_admissible(vault, repository, f"les_{length - 1}", memo=memo)
    assert len(memo) == length and all(memo.values())


def test_f3_a_missing_ancestor_at_the_bottom_of_a_long_chain_fails_every_recap_above_it(tmp_path, monkeypatch):
    import sys

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    length = sys.getrecursionlimit() + 200
    _synthetic_chain(monkeypatch, length, last="les_missing_x")
    monkeypatch.setattr(B, "_lesson_exposure", _missing_aware(B._lesson_exposure))
    memo: dict[str, bool] = {}
    assert not B.recap_admissible(vault, repository, f"les_{length - 1}", memo=memo)
    assert not any(memo.values())
    assert not B.recap_admissible(vault, repository, "les_5", memo=memo)  # memoized: same verdict


def test_f3_a_cycle_in_a_long_chain_fails_closed(tmp_path, monkeypatch):
    import sys

    paths, repository = build_teacher_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    length = sys.getrecursionlimit() + 200
    _synthetic_chain(monkeypatch, length, back_edge=f"les_{length - 1}")
    assert not B.recap_admissible(vault, repository, f"les_{length - 1}")


def _missing_aware(inner):
    def exposure(repository, lesson_id):
        return None if lesson_id.startswith("les_missing") else inner(repository, lesson_id)
    return exposure
