"""Instruct hand-off IH7 (spec_instruct_handoff_v1 §7c): a lesson opened after a miss reads what the diagnosis points at.

The Nov 7 shape, synthetic: a decision-regions topic whose linked section is a short code listing, and a softmax
confusion that chapter 3 discusses. Fakes only; no model call (the retrieval is keyword-only).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.config import LearnLoopConfig
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.stores import hypothesis_marks as marks_store
from learnloop.db.stores import learner_gaps as gap_store
from learnloop.db.stores import router_suggestions as suggestions
from learnloop.db.stores.write_provenance import WriteRecord, record_text_write
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import lesson_sources_follow_diagnosis_on
from learnloop.source_retrieval.section_coverage import Library
from learnloop.teacher import service as S
from learnloop.teacher.brief import build_brief, recap_admissible, revoke_unteachable, SourceBook
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import write_yaml
from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version
from tests.practice_index_fakes import _learning_object
from tests.section_coverage_fixtures import HELD_OUT_SENTINEL, cite
from tests.source_retrieval_fakes import EXAM_QUESTION, seed_source
from tests.teacher_fakes import TeacherFake, _item, build_teacher_vault, clients, plan_turn
from tests.ux_phase1_support import set_config

TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
T0 = datetime(2026, 11, 7, 9, 0, tzinfo=UTC)
LO = "lo_regions"
LINKED = "ext_ml/ml_regions"
SOFTMAX = "ext_ml/ml_softmax"

SOFTMAX_TEXT = ("Softmax turns the logits into probabilities that sum to one. Unlike argmax, softmax keeps every "
                "class's score, so its output changes smoothly as the logits move.")
ML = {
    "ml_regions": ("2.9 Rendering decision regions", [
        ("Listing 2.9: grid = meshgrid(); region = argmax(model(grid)); plot(region).", 173)]),
    "ml_softmax": ("3.4 The softmax function", [(SOFTMAX_TEXT, 110)]),
    "ml_entropy": ("3.5 Cross entropy", [("Cross entropy compares two probability distributions.", 115)]),
}
CONFUSION = "Treats softmax and argmax as the same operation when drawing a region."


def _clock(minutes: float = 0.0) -> FrozenClock:
    return FrozenClock(T0 + timedelta(minutes=minutes))


def _rows(repository, sql, params=()):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def _open_payload(repository, lesson_id: str) -> dict[str, Any]:
    from learnloop.db.stores import lessons as store

    with repository.connection() as connection:
        opened = next(turn for turn in store.turns(connection, lesson_id) if turn["action"] == "open")
    return opened["payload"]


def _exec(repository, sql, params=()):
    with repository.connection() as connection:
        connection.execute(sql, params)
        connection.commit()


class World:
    def __init__(self, tmp_path: Path, *, version: str = TAG, config: str = "", reserved: bool = False) -> None:
        self.paths, self.repository = build_teacher_vault(tmp_path / "vault", reserved=reserved)
        seed_source(self.repository, source_id="src_ml", revision_id="rev_ml", extraction_id="ext_ml",
                    title="Deep Learning Notes", units=ML, furniture=False)
        upsert_source_set(self.paths.root, {"id": "sset_la", "subject_id": "linear-algebra",
                                            "title": "Linear algebra sources", "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_lay", "revision_id": "rev_lay", "default_role": "primary_textbook"},
            {"source_id": "src_ml", "revision_id": "rev_ml", "default_role": "primary_textbook"}]})
        lo = _learning_object(LO, "Rendering decision regions")
        lo["summary"] = "Render a classifier's decision regions over a grid of inputs."
        write_yaml(self.paths.learning_object_path("linear-algebra", LO), lo)
        cite(self.paths, LO, "src_ml", "ext_ml", "s2")
        write_yaml(self.paths.practice_item_path("linear-algebra", "pi_regions"),
                   _item("pi_regions", LO, "Render the regions of a three-class classifier.", "argmax over the logits"))
        set_algorithm_version(self.paths, version)
        if config:
            append_config_toml(self.paths.root, config)
        self.vault = load_vault(self.paths.root)

    def reload(self) -> None:
        self.vault = load_vault(self.paths.root)

    # -- the miss, its diagnosis, the offer -------------------------------------------------------------

    def miss(self, *, minutes: float = 0.0, points: int = 0, item: str = "pi_regions", stuck: bool = False) -> str:
        attempt = complete_self_graded_attempt(
            self.vault, self.repository,
            AttemptDraft(practice_item_id=item, learner_answer_md="I applied softmax to get the region.",
                         attempt_type="independent_attempt", evidence_origin="human", declared_stuck=stuck),
            SelfGradeInput(criterion_points={"correctness": points}, confidence=3), clock=_clock(minutes))
        return attempt.attempt_id

    def diagnose(self, attempt_id: str, *, status: str = "completed", statements=(CONFUSION,), hypo_status="candidate",
                 minutes: float = 1.0, statuses=()) -> list[dict[str, Any]]:
        _exec(self.repository,
              "INSERT INTO attempt_diagnoses (id, attempt_id, diagnosis_prompt_version, mode, history_mode, status, "
              "proposal_json, created_at) VALUES (?, ?, 'v', 'live', 'full', ?, ?, ?)",
              (f"dg_{attempt_id}_{status}", attempt_id, status,
               json.dumps({"analysis_md": "THEY WROTE argmax over the logits"}) if status == "completed" else None,
               (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")))
        rows = []
        for index, statement in enumerate(statements):
            rows.append(self.repository.append_causal_hypothesis(
                episode_key=f"ep_{attempt_id}_{index}", attempt_id=attempt_id, learning_object_id=LO,
                cause_scope="learner_state", statement=statement, statement_normalized=statement.lower(),
                status=statuses[index] if index < len(statuses) else hypo_status))
        return rows

    def offer(self, *, minutes: float = 2.0, kind: str = "plan_interrupt", los=(LO,)) -> str:
        decision_id = f"rd_{kind}_{minutes}"
        stamp = (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
        _exec(self.repository,
              "INSERT INTO router_decisions (id, receipt_key, decision_kind, surface, mode, policy, algorithm_version, "
              "log_version, snapshot_hash, candidates_json, exclusions_json, candidate_count, chosen_ref, "
              "propensity, propensity_kind, detail_json, created_at) VALUES (?, ?, ?, 'desktop', 'live', 'staged_v1', "
              "'mvp-0.55', 'v1', 'h', '[]', '[]', 0, ?, 1.0, 'deterministic', '{}', ?)",
              (decision_id, f"k:{decision_id}", kind, f"lesson_offer:{los[0]}", stamp))
        with self.repository.atomic():
            suggestions.insert_response(self.repository.connection(), decision_id=decision_id, response="accepted",
                                        candidate_ref=f"lesson_offer:{los[0]}", learning_object_ids=list(los),
                                        responded_at=stamp, lesson_id=f"les_{decision_id}")
        return decision_id

    def brief(self, decision_id: str | None, *, origin: str | None = "router", selection=None, los=(LO,),
              vault=None) -> tuple[dict[str, Any], SourceBook, dict[str, Any]]:
        record: dict[str, Any] = {}
        brief, book = build_brief(
            vault or self.vault, self.repository, learning_object_ids=list(los), how={lo: "test" for lo in los},
            goal_text="Rendering decision regions", selection=selection, driver="desktop", lesson_id=None,
            constraints={}, origin=origin, origin_ref=decision_id, follow_record=record)
        return brief, book, record

    def ask(self, *, minutes: float = 2.0, kind: str = "lesson", lo: str = LO, preference_id: str = "pref_learn",
            attempt: str | None = None) -> str:
        """IH3's "learn this": the learner's preference for a lesson on ``lo`` (the row the desktop's choice writes),
        naming the attempt whose feedback it was tapped on (``attempt``), as ``learner_action.choose`` does."""

        stamp = (T0 + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
        _exec(self.repository,
              "INSERT INTO router_learner_preferences (id, decision_id, attempt_id, session_id, surface, offered_json, "
              "chosen_kind, chosen_ref, note_md, served_decision_id, algorithm_version, created_at) "
              "VALUES (?, NULL, ?, 's1', 'feedback', '{}', ?, ?, NULL, NULL, 'mvp-0.55', ?)",
              (preference_id, attempt, kind, f"lesson_offer:{lo}", stamp))
        return preference_id

    def pending(self, attempt_id: str) -> None:
        """The attempt's live diagnosis is still being written (a queued job)."""

        _exec(self.repository,
              "INSERT INTO post_attempt_jobs (id, attempt_id, kind, job_key, attempt_completed_at, state, payload_json, "
              "created_at, updated_at) VALUES (?, ?, 'diagnose', ?, '2026-11-07T09:00:00Z', 'queued', "
              "'{\"mode\": \"live\"}', '2026-11-07T09:00:00Z', '2026-11-07T09:00:00Z')",
              (f"j_{attempt_id}", attempt_id, f"k_{attempt_id}"))

    def asked_brief(self, preference_id: str | None, *, at_minutes: float = 5.0, selection=None, los=(LO,),
                    vault=None) -> tuple[dict[str, Any], SourceBook, dict[str, Any]]:
        record: dict[str, Any] = {}
        brief, book = build_brief(
            vault or self.vault, self.repository, learning_object_ids=list(los), how={lo: "test" for lo in los},
            goal_text="Rendering decision regions", selection=selection, driver="desktop", lesson_id=None,
            constraints={}, origin="learner_pick", origin_ref=None, follow_record=record, preference_ref=preference_id,
            opens_at=(T0 + timedelta(minutes=at_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        return brief, book, record

    def open(self, decision_id: str, **kwargs):
        return S.open_lesson(self.vault, self.repository, entry="learning_object", learning_object_ids=[LO],
                             clients=clients(TeacherFake([plan_turn])), origin="router", origin_ref=decision_id,
                             lesson_id=f"les_{decision_id}", clock=_clock(5), **kwargs)


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def _bytes(brief: dict[str, Any]) -> bytes:
    return json.dumps(brief, sort_keys=True, ensure_ascii=False).encode()


def _refs(brief: dict[str, Any]) -> list[str]:
    return [section["ref"] for section in brief["sources"]["sections"]]


def _diagnosed(world: World, **kwargs) -> str:
    attempt = world.miss()
    world.diagnose(attempt, **kwargs)
    return world.offer()


# -- the Nov 7 shape -----------------------------------------------------------------------------------------------


def test_a_softmax_confusion_brings_in_the_softmax_section_beside_the_linked_one(world):
    decision = _diagnosed(world)
    brief, book, record = world.brief(decision)
    assert _refs(brief) == [LINKED, SOFTMAX], "the topic's linked section first, the added one beside it"
    assert brief["sources"]["mode"] == "whole"
    softmax = brief["sources"]["sections"][1]
    assert softmax["passages"][0]["text"] == SOFTMAX_TEXT
    assert softmax["passages"][0]["alias"] in book.passages and book.passages[softmax["passages"][0]["alias"]][
        "section_ref"] == SOFTMAX
    # The teacher is told which statement found it.
    assert brief["sources"]["from_diagnosis"]["added"] == [
        {"ref": SOFTMAX, "title": "3.4 The softmax function", "found_by": [CONFUSION]}]
    # The cross-entropy section shares no word with the confusion, so only the softmax chapter came in.
    assert SOFTMAX in {e["ref"] for e in record["added"]} and "ext_ml/ml_entropy" not in _refs(brief)


def test_the_record_names_what_was_added_the_confusion_that_found_it_and_why(world):
    decision = _diagnosed(world)
    _brief, _book, record = world.brief(decision)
    assert record["version"] == "lesson_sources_follow_v1" and record["status"] == "added"
    assert record["miss"]["decision_id"] == decision and record["miss"]["learning_object_id"] == LO
    assert record["diagnosis_id"]
    [confusion] = record["confusions"]
    assert confusion["kind"] == "hypothesis" and confusion["text"] == CONFUSION and SOFTMAX in confusion["matched"]
    [added] = record["added"]
    assert added["ref"] == SOFTMAX and added["shown"] == "whole" and added["found_by"] == [CONFUSION]


def test_the_open_turn_keeps_the_record_where_it_can_be_read_later(world):
    decision = _diagnosed(world)
    view = world.open(decision)
    payload = _open_payload(world.repository, view["lesson_id"])
    assert payload["sources_follow"]["status"] == "added"
    assert payload["sources_follow"]["added"][0]["ref"] == SOFTMAX
    assert SOFTMAX in {s["ref"] for s in payload["brief"]["sources"]["sections"]}
    # Every added passage has its alias in the persisted book, which the recap and read_source read.
    aliases = {p["alias"] for s in payload["brief"]["sources"]["sections"] if s["ref"] == SOFTMAX for p in s["passages"]}
    assert aliases and aliases <= set(payload["book"]["passages"])


def test_a_reader_selection_stays_first(world):
    decision = _diagnosed(world)
    selection = {"extraction_id": "ext_book", "section_id": "ch_eigen"}
    brief, _book, record = world.brief(decision, selection=selection)
    assert _refs(brief)[0] == "ext_book/ch_eigen"
    assert _refs(brief).index(LINKED) < _refs(brief).index(SOFTMAX), "linked before added"
    assert _refs(brief)[-1] == SOFTMAX and record["status"] == "added"


def test_a_section_the_lesson_already_has_is_not_added_twice(world):
    attempt = world.miss()
    world.diagnose(attempt, statements=("Never read the listing: decision regions from a meshgrid and argmax.",))
    brief, _book, record = world.brief(world.offer())
    assert _refs(brief).count(LINKED) == 1
    assert LINKED not in {e["ref"] for e in record.get("added", [])}


def test_withheld_sections_stay_out(world):
    attempt = world.miss()
    world.diagnose(attempt, statements=(f"{HELD_OUT_SENTINEL} {EXAM_QUESTION} softmax",))
    brief, _book, record = world.brief(world.offer())
    assert "ext_lay/lay_held" not in {e["ref"] for e in record.get("added", [])} | set(_refs(brief))
    assert "ext_exam/exam_q" not in {e["ref"] for e in record.get("added", [])} | set(_refs(brief))
    # No withheld passage text reaches the sections the brief renders.
    rendered = " ".join(p["text"] for s in brief["sources"]["sections"] for p in s["passages"])
    assert "held-out midterm matrix" not in rendered and EXAM_QUESTION not in rendered
    assert SOFTMAX in _refs(brief)  # the one unprotected match still comes in


def test_a_section_held_out_after_the_fact_is_revoked_for_the_lesson(world):
    decision = _diagnosed(world)
    view = world.open(decision)
    lesson_id = view["lesson_id"]
    assert recap_admissible(world.vault, world.repository, lesson_id)
    save_unit_selection(world.repository, "ext_ml", list(ML), exam_use_modes={"ml_softmax": "held_out_evaluation"})
    library = Library(world.vault, world.repository)
    book = SourceBook.from_dict(_open_payload(world.repository, lesson_id)["book"])
    assert revoke_unteachable(library, book) and all(
        book.passages[alias]["section_ref"] == SOFTMAX for alias in book.revoked)
    # The recap of that lesson is no longer admissible: it may have been written from the softmax passages.
    assert not recap_admissible(world.vault, world.repository, lesson_id)


def test_a_lesson_without_added_sections_keeps_its_recap_when_the_same_section_is_held_out(tmp_path):
    plain = World(tmp_path)
    attempt = plain.miss()
    decision = plain.offer()  # no diagnosis: nothing added
    view = plain.open(decision)
    save_unit_selection(plain.repository, "ext_ml", list(ML), exam_use_modes={"ml_softmax": "held_out_evaluation"})
    assert recap_admissible(plain.vault, plain.repository, view["lesson_id"]), attempt


# -- the budget ----------------------------------------------------------------------------------------------------


def _linked_tokens(world: World) -> int:
    brief, _book, _record = world.brief(None, origin=None)
    return int(brief["sources"]["tokens"])


def test_over_budget_the_added_section_falls_to_the_outline_and_the_linked_one_stays_whole(world):
    decision = _diagnosed(world)
    fits = _linked_tokens(world)
    set_config(world.paths.root, {("teacher", "context", "sources_tokens"): fits})
    world.reload()
    alone, _b, _r = world.brief(None, origin=None)
    assert alone["sources"]["mode"] == "whole"
    brief, _book, record = world.brief(decision)
    assert brief["sources"]["mode"] == "whole" and _refs(brief) == [LINKED], "the linked section is not demoted"
    assert brief["sources"]["sections"][0]["passages"], "and is still read whole"
    assert SOFTMAX in {a["ref"] for a in brief["sources"]["alternates"]}, "the added one is in the outline"
    assert record["status"] == "listed"
    [added] = record["added"]
    assert added["shown"] == "outline" and "budget" in added["why"]
    assert brief["sources"]["from_diagnosis"]["listed_in_outline"][0]["ref"] == SOFTMAX
    assert brief["sources"]["from_diagnosis"]["added"] == []
    # The teacher can still read it.
    from learnloop.teacher.actions import read_source

    view = world.open(decision)
    read = read_source(world.vault, world.repository, S.load_state(world.repository, view["lesson_id"]), [SOFTMAX])
    assert read["sections"][0]["passages"][0]["text"] == SOFTMAX_TEXT


def test_the_added_section_never_changes_whether_the_linked_ones_are_whole(world):
    decision = _diagnosed(world)
    set_config(world.paths.root, {("teacher", "context", "sources_tokens"): 1})
    world.reload()
    alone, _b, _r = world.brief(None, origin=None)
    brief, _book, record = world.brief(decision)
    assert alone["sources"]["mode"] == "outline" and brief["sources"]["mode"] == "outline"
    assert brief["sources"]["tokens"] == alone["sources"]["tokens"]
    assert [s["ref"] for s in brief["sources"]["sections"]] == [LINKED]
    assert SOFTMAX in {a["ref"] for a in brief["sources"]["alternates"]}
    assert "already fill" in record["added"][0]["why"]


# -- when nothing changes ------------------------------------------------------------------------------------------


def _unchanged(world: World, decision: str, why: str) -> None:
    brief, _book, record = world.brief(decision)
    plain, _b, _r = world.brief(None, origin=None)
    assert _bytes(brief) == _bytes(plain), "the brief is unchanged"
    assert record["status"] == "none" and why in record["why"]


def test_no_diagnosis_means_an_unchanged_brief_and_the_record_says_so(world):
    world.miss()
    _unchanged(world, world.offer(), "no diagnosis")


def test_a_pending_diagnosis_means_an_unchanged_brief(world):
    attempt = world.miss()
    _exec(world.repository,
          "INSERT INTO post_attempt_jobs (id, attempt_id, kind, job_key, attempt_completed_at, state, payload_json, "
          "created_at, updated_at) VALUES ('j1', ?, 'diagnose', 'k1', '2026-11-07T09:00:00Z', 'queued', "
          "'{\"mode\": \"live\"}', '2026-11-07T09:00:00Z', '2026-11-07T09:00:00Z')", (attempt,))
    _unchanged(world, world.offer(), "still being written")


def test_a_failed_diagnosis_means_an_unchanged_brief(world):
    attempt = world.miss()
    world.diagnose(attempt, status="failed", statements=())
    _unchanged(world, world.offer(), "did not complete")


def test_a_diagnosis_with_no_hypotheses_or_gaps_means_an_unchanged_brief(world):
    attempt = world.miss()
    world.diagnose(attempt, statements=())
    _unchanged(world, world.offer(), "names no confusion")


def test_a_correct_latest_attempt_has_no_diagnosis_so_nothing_changes(world):
    old = world.miss(minutes=0)
    world.diagnose(old)
    world.miss(minutes=1.5, points=4)  # the latest attempt before the offer is a success
    _unchanged(world, world.offer(), "no diagnosis")


def test_a_miss_after_the_offer_is_not_behind_it(world):
    decision = world.offer(minutes=0.5)
    attempt = world.miss(minutes=3)
    world.diagnose(attempt, minutes=4)
    _unchanged(world, decision, "no attempt on these topics before the offer")


def test_nothing_matching_the_confusion_means_an_unchanged_brief(world):
    attempt = world.miss()
    world.diagnose(attempt, statements=("Zebras are striped.",))
    _unchanged(world, world.offer(), "no section matched")


def test_a_lesson_the_learner_started_is_unchanged(world):
    """A Reader selection and a typed topic open as ``learner_pick`` with no origin ref and no preference: nothing on
    record links them to a miss. (IH3's "learn this" names its preference: decision 2's tests below.)"""

    _diagnosed(world)
    plain, _b, _r = world.brief(None, origin=None)
    for origin, ref in (("learner_pick", None), ("learner_pick", "rd_plan_interrupt_2.0"), ("router", None)):
        brief, _book, record = world.brief(ref, origin=origin)
        assert _bytes(brief) == _bytes(plain) and record == {}, (origin, ref)
    view = S.open_lesson(world.vault, world.repository, entry="learning_object", learning_object_ids=[LO],
                         clients=clients(TeacherFake([plan_turn])), clock=_clock(5))
    assert "sources_follow" not in _open_payload(world.repository, view["lesson_id"])


# -- a lesson the learner asked for (the owner's decision 2, Nov 9) --------------------------------------------------


def test_a_lesson_asked_for_with_learn_this_reads_the_latest_miss_on_its_topic(world):
    """"Yes, definitely use the latest miss on that topic": a ``learner_pick`` lesson from IH3's "learn this" loads the
    sections matching the diagnosed confusion, beside the linked one, and the record names the request."""

    attempt = world.miss()
    world.diagnose(attempt)
    preference = world.ask()
    brief, _book, record = world.asked_brief(preference)
    assert _refs(brief) == [LINKED, SOFTMAX], "the topic's linked section first, the added one beside it"
    assert record["status"] == "added" and record["miss"]["attempt_id"] == attempt
    assert record["asked"]["preference_id"] == preference and "decision_id" not in record["miss"]
    assert brief["sources"]["from_diagnosis"]["added"][0]["found_by"] == [CONFUSION]


def test_the_learner_asked_lesson_keeps_its_record_in_the_open_turn(world):
    attempt = world.miss()
    world.diagnose(attempt)
    preference = world.ask()
    view = S.open_lesson(world.vault, world.repository, entry="learning_object", learning_object_ids=[LO],
                         clients=clients(TeacherFake([plan_turn])), clock=_clock(5), preference_id=preference)
    payload = _open_payload(world.repository, view["lesson_id"])
    assert payload["sources_follow"]["status"] == "added" and payload["sources_follow"]["asked"]["preference_id"] == preference
    assert payload["sources_follow"]["asked"]["lesson_opens_at"] == _clock(5).now().strftime("%Y-%m-%dT%H:%M:%SZ")
    lesson = _rows(world.repository, "SELECT origin, origin_ref FROM lessons WHERE id = ?", (view["lesson_id"],))[0]
    assert lesson == {"origin": "learner_pick", "origin_ref": None}, "the lesson row is a learner's start, as before"


def test_the_latest_miss_passes_over_a_later_correct_attempt(world):
    """The latest attempt with a diagnosis in force: a correct attempt has none (no score is read)."""

    attempt = world.miss(minutes=0)
    world.diagnose(attempt)
    world.miss(minutes=1.5, points=4)
    brief, _book, record = world.asked_brief(world.ask())
    assert record["status"] == "added" and record["miss"]["attempt_id"] == attempt and SOFTMAX in _refs(brief)


def test_the_latest_of_two_diagnosed_misses_is_the_one_read(world):
    first = world.miss(minutes=0)
    world.diagnose(first, statements=("Zebras are striped.",), minutes=0.5)
    second = world.miss(minutes=1)
    world.diagnose(second, minutes=1.5)
    _brief, _book, record = world.asked_brief(world.ask())
    assert record["miss"]["attempt_id"] == second and record["status"] == "added"


def test_a_miss_after_the_lesson_opens_is_not_behind_it(world):
    attempt = world.miss(minutes=10)
    world.diagnose(attempt, minutes=11)
    plain = world.brief(None, origin=None)[0]
    brief, _book, record = world.asked_brief(world.ask(), at_minutes=5)
    assert _bytes(brief) == _bytes(plain) and record["status"] == "none" and "diagnosis in force" in record["why"]


def test_a_lesson_whose_request_is_not_on_record_or_names_another_topic_adds_nothing(world):
    attempt = world.miss()
    world.diagnose(attempt)
    plain = world.brief(None, origin=None)[0]
    world.ask(preference_id="pref_other", lo="lo_eigen")
    world.ask(preference_id="pref_item", kind="new_practice")
    for preference in ("pref_missing", "pref_other", "pref_item"):
        brief, _book, record = world.asked_brief(preference)
        assert _bytes(brief) == _bytes(plain) and record["status"] == "none", preference
        assert record["why"] == "the learner's request for this lesson is not on record", preference


def test_the_sidecar_passes_the_learn_this_preference_to_the_opening(world, monkeypatch):
    """The desktop's ``lesson.turn`` ``open`` names the preference (camelCase on the wire), and only a learner's own start
    carries it on."""

    from learnloop_sidecar.handlers import lesson as H

    class _Ctx:
        grading_provider_override = None

        def require_vault(self):
            return world.vault, world.repository

        def reload(self, maintenance: bool = True):
            pass

    attempt = world.miss()
    world.diagnose(attempt)
    preference = world.ask()
    monkeypatch.setattr(H, "_clients", lambda ctx, vault: clients(TeacherFake([plan_turn])))
    params = H.LessonTurnInput.model_validate({"action": "open", "entry": "learning_object", "learningObjectIds": [LO],
                                               "preferenceId": preference})
    assert params.preference_id == preference
    opened = H.lesson_turn(_Ctx(), params)
    payload = _open_payload(world.repository, opened["lessonId"])
    assert payload["sources_follow"]["asked"]["preference_id"] == preference
    assert payload["sources_follow"]["status"] == "added"


def test_a_reader_selection_or_a_typed_topic_ignores_a_preference(world):
    """Reader-selection and typed-topic lessons stay unchanged: the service passes the preference only for a learner's
    own start on a topic."""

    attempt = world.miss()
    world.diagnose(attempt)
    preference = world.ask()
    view = S.open_lesson(world.vault, world.repository, entry="reader_selection",
                         selection={"extraction_id": "ext_ml", "span_ids": ["s2"]},
                         clients=clients(TeacherFake([plan_turn])), clock=_clock(5), preference_id=preference)
    assert "sources_follow" not in _open_payload(world.repository, view["lesson_id"])


def test_a_learner_asked_lesson_with_no_diagnosed_miss_opens_as_before(world):
    world.miss(minutes=0, points=4)
    plain = world.brief(None, origin=None)[0]
    brief, _book, record = world.asked_brief(world.ask())
    assert _bytes(brief) == _bytes(plain) and record["status"] == "none"


# -- review 3: the miss the learner asked from (M1) and one lesson per request (m3) ---------------------------------


def test_learn_this_while_the_answers_diagnosis_is_pending_reads_no_older_miss_and_says_so(world):
    """Review 3, M1 (R1): a diagnosed miss a month earlier, then the miss the learner is looking at, its diagnosis still
    queued, and "learn this" on its feedback. The lesson opens without diagnosed sections (it never waits), and the
    record names the attempt it considered and why nothing was added. The month-old miss is not read."""

    old = world.miss(minutes=-30 * 24 * 60)
    world.diagnose(old, minutes=-30 * 24 * 60 + 1)
    latest = world.miss(minutes=0)
    world.pending(latest)
    plain = world.brief(None, origin=None)[0]
    brief, _book, record = world.asked_brief(world.ask(minutes=0.5, attempt=latest), at_minutes=1)
    assert _bytes(brief) == _bytes(plain), "the lesson opens as before, without the older miss's sections"
    assert record["status"] == "none" and record["why"] == "the diagnosis of that attempt is still being written"
    assert record["miss"]["attempt_id"] == latest and record["miss"]["chosen_as"] == "the_attempt_the_learner_asked_from"
    assert record["asked"]["asked_from_attempt"] == latest and record["passed_over"] == []
    assert old not in json.dumps(record)


def test_with_no_attempt_named_the_latest_miss_pending_is_not_skipped_for_an_older_one(world):
    old = world.miss(minutes=0)
    world.diagnose(old)
    latest = world.miss(minutes=1)
    world.pending(latest)
    _brief, _book, record = world.asked_brief(world.ask(minutes=1.5))
    assert record["status"] == "none" and "still being written" in record["why"]
    assert record["miss"] == {"attempt_id": latest, "learning_object_id": LO, "attempt_at": "2026-11-07T09:01:00Z",
                              "chosen_as": "the_latest_attempt_on_the_topic"}


def test_a_failed_diagnosis_on_the_latest_miss_is_said_and_no_older_miss_is_read(world):
    old = world.miss(minutes=0)
    world.diagnose(old)
    latest = world.miss(minutes=1)
    world.diagnose(latest, status="failed", statements=(), minutes=1.2)
    _brief, _book, record = world.asked_brief(world.ask(minutes=1.5, attempt=latest))
    assert record["status"] == "none" and "did not complete" in record["why"] and record["miss"]["attempt_id"] == latest


def test_the_attempt_the_learner_asked_from_is_read_even_with_a_later_diagnosed_miss(world):
    first = world.miss(minutes=0)
    world.diagnose(first, minutes=0.5)
    second = world.miss(minutes=1)
    world.diagnose(second, statements=("Zebras are striped.",), minutes=1.5)
    brief, _book, record = world.asked_brief(world.ask(minutes=2, attempt=first))
    assert record["status"] == "added" and record["miss"]["attempt_id"] == first and SOFTMAX in _refs(brief)
    assert record["miss"]["chosen_as"] == "the_attempt_the_learner_asked_from"


def test_learn_this_on_a_right_answer_passes_it_over_by_name_to_the_latest_miss(world):
    """A right answer has no diagnosis at all (no score is read): it is passed over, named, with why."""

    miss = world.miss(minutes=0)
    world.diagnose(miss)
    right = world.miss(minutes=1, points=4)
    brief, _book, record = world.asked_brief(world.ask(minutes=1.5, attempt=right))
    assert record["status"] == "added" and record["miss"]["attempt_id"] == miss and SOFTMAX in _refs(brief)
    assert record["miss"]["chosen_as"] == "the_latest_attempt_on_the_topic"
    assert record["passed_over"] == [{"attempt_id": right, "why": "that attempt has no diagnosis (a correct answer has none)"}]


def test_an_attempt_on_another_topic_or_unknown_is_passed_over_by_name(world):
    miss = world.miss(minutes=0)
    world.diagnose(miss)
    elsewhere = world.miss(minutes=1, item="pi_det_1")  # on lo_det
    for preference_id, attempt, why in (
            ("pref_gone", "no_such_attempt", "the attempt the learner was looking at is not on record before the lesson opened"),
            ("pref_elsewhere", elsewhere, "the attempt the learner was looking at is not on this lesson's topics")):
        _brief, _book, record = world.asked_brief(world.ask(minutes=1.5, attempt=attempt, preference_id=preference_id))
        assert record["passed_over"][0] == {"attempt_id": attempt, "why": why}, preference_id
        assert record["miss"]["attempt_id"] == miss and record["status"] == "added", preference_id


def test_a_request_opens_one_lesson_and_a_second_opening_is_ignored_and_recorded(world):
    """Review 3, m3 (R1b): the first opening consumes the request (its open turn names it); the same id five minutes or
    two weeks later reads nothing, and the record names the lesson that used it. No age constant."""

    attempt = world.miss()
    world.diagnose(attempt)
    preference = world.ask()
    first = S.open_lesson(world.vault, world.repository, entry="learning_object", learning_object_ids=[LO],
                          clients=clients(TeacherFake([plan_turn])), clock=_clock(5), preference_id=preference)
    opened = _rows(world.repository, "SELECT refs_json FROM lesson_turns WHERE lesson_id = ? AND action = 'open'",
                   (first["lesson_id"],))[0]
    assert json.loads(opened["refs_json"])["preference"] == preference
    assert _open_payload(world.repository, first["lesson_id"])["sources_follow"]["status"] == "added"
    _exec(world.repository, "UPDATE lessons SET closed_at = ?, close_reason = 'learner_stop' WHERE id = ?",
          (_clock(20).now().strftime("%Y-%m-%dT%H:%M:%SZ"), first["lesson_id"]))
    plain = world.brief(None, origin=None)[0]
    for minutes in (30, 60 * 24 * 14):
        brief, _book, record = world.asked_brief(preference, at_minutes=minutes)
        assert _bytes(brief) == _bytes(plain) and record["status"] == "none", minutes
        assert record["why"] == "this request already opened a lesson", minutes
        assert record["asked"]["already_opened_lesson"] == first["lesson_id"], minutes
    second = S.open_lesson(world.vault, world.repository, entry="learning_object", learning_object_ids=[LO],
                           clients=clients(TeacherFake([plan_turn])), clock=_clock(60), preference_id=preference)
    payload = _open_payload(world.repository, second["lesson_id"])
    assert payload["sources_follow"]["why"] == "this request already opened a lesson"
    refs = _rows(world.repository, "SELECT refs_json FROM lesson_turns WHERE lesson_id = ? AND action = 'open'",
                 (second["lesson_id"],))[0]
    assert "preference" not in json.loads(refs["refs_json"]), "only the first opening consumes it"


def test_a_request_not_on_record_consumes_nothing(world):
    world.miss()
    view = S.open_lesson(world.vault, world.repository, entry="learning_object", learning_object_ids=[LO],
                         clients=clients(TeacherFake([plan_turn])), clock=_clock(5), preference_id="pref_missing")
    refs = _rows(world.repository, "SELECT refs_json FROM lesson_turns WHERE lesson_id = ? AND action = 'open'",
                 (view["lesson_id"],))[0]
    assert "preference" not in json.loads(refs["refs_json"])


def test_the_lesson_ref_prefix_is_the_plans():
    from learnloop.daily_plan.types import LESSON_OFFER_PREFIX
    from learnloop.teacher import diagnosed_sources as DS

    assert DS.LESSON_OFFER_PREFIX == LESSON_OFFER_PREFIX


def test_switch_off_and_below_the_tag_a_learner_asked_lesson_is_byte_identical(tmp_path):
    for name, world in (("off", World(tmp_path / "off", config="[router_objective]\nlesson_sources_follow_diagnosis = false\n")),
                        ("below", World(tmp_path / "below", version=OLD))):
        attempt = world.miss()
        world.diagnose(attempt)
        preference = world.ask()
        plain = world.brief(None, origin=None)[0]
        brief, _book, record = world.asked_brief(preference)
        assert _bytes(brief) == _bytes(plain) and record == {}, name
        view = S.open_lesson(world.vault, world.repository, entry="learning_object", learning_object_ids=[LO],
                             clients=clients(TeacherFake([plan_turn])), clock=_clock(5), preference_id=preference)
        assert "sources_follow" not in _open_payload(world.repository, view["lesson_id"]), name


# -- the switch and the tag ----------------------------------------------------------------------------------------


def test_switch_off_and_below_the_tag_leave_the_brief_byte_identical(tmp_path):
    on = World(tmp_path / "on")
    off = World(tmp_path / "off", config="[router_objective]\nlesson_sources_follow_diagnosis = false\n")
    below = World(tmp_path / "below", version=OLD)
    briefs = {}
    for name, world in (("on", on), ("off", off), ("below", below)):
        decision = _diagnosed(world)
        briefs[name] = (world.brief(decision), world.brief(None, origin=None)[0])
    assert _bytes(briefs["on"][0][0]) != _bytes(briefs["on"][1]), "on, the diagnosed lesson reads more"
    for name in ("off", "below"):
        (brief, _book, record), plain = briefs[name]
        assert _bytes(brief) == _bytes(plain), name
        assert record == {}, f"{name}: no record is kept"
    # And through the service: the open turn carries no record while off.
    decision = _diagnosed_open(off)
    payload = _open_payload(off.repository, f"les_{decision}")
    assert "sources_follow" not in payload
    assert SOFTMAX not in json.dumps(payload["brief"]), decision


def _diagnosed_open(world: World) -> str:
    # The World above already holds a diagnosed miss; open its lesson.
    decision = "rd_plan_interrupt_2.0"
    world.open(decision)
    return decision


def test_the_switch_needs_the_tag_and_defaults_on(tmp_path):
    assert lesson_sources_follow_diagnosis_on(create_vault_at(tmp_path / "on", TAG).config)
    assert not lesson_sources_follow_diagnosis_on(create_vault_at(tmp_path / "below", OLD).config)
    off = create_vault_at(tmp_path / "off", TAG, "[router_objective]\nlesson_sources_follow_diagnosis = false\n")
    assert not lesson_sources_follow_diagnosis_on(off.config)
    # It needs no objective: it changes what a lesson reads, never what the router decides.
    plain = create_vault_at(tmp_path / "plain", TAG, "[router_objective]\nenabled = false\n")
    assert lesson_sources_follow_diagnosis_on(plain.config)
    assert LearnLoopConfig().router_objective.lesson_sources_follow_diagnosis is True


def create_vault_at(root: Path, version: str, config: str = ""):
    paths = create_basic_vault(root)
    set_algorithm_version(paths, version)
    if config:
        append_config_toml(paths.root, config)
    return load_vault(paths.root)


def test_the_switch_is_registered_as_an_operational_kill_switch():
    rule = classify_config_path("router_objective.lesson_sources_follow_diagnosis")
    assert rule is not None and "kill switch" in rule.rationale and "IH7" in rule.rationale
    assert LearnLoopConfig().router_objective.lesson_sources_follow_diagnosis is True


# -- what searches, and what never does ----------------------------------------------------------------------------


def test_the_diagnosis_hypotheses_come_first_my_gap_first_then_the_learners_gaps(world):
    attempt = world.miss()
    first, second, retired = world.diagnose(
        attempt, statements=("Thinks the grid is the model's input and softmax is its output layer.",
                             "Mixes up argmax with the softmax output when drawing a region.",
                             "Believes cross entropy draws the region."),
        statuses=("candidate", "validated", "retired"))
    with world.repository.atomic(), world.repository.connection() as connection:
        marks_store.insert_mark(connection, {
            "attempt_id": attempt, "learning_object_id": LO, "hypothesis_version_id": second["id"],
            "hypothesis_key": second["episode_key"], "mark": "my_gap", "display_order_json": "[]",
            "surface": "feedback", "probe_answered": 0, "created_at": "2026-11-07T09:01:30Z"})
        gap_store.insert_gap(connection, {
            "source_kind": "stuck_answer", "source_id": attempt, "attempt_id": attempt,
            "practice_item_id": "pi_regions", "anchor_learning_object_id": LO, "learner_text": "no idea what a region is",
            "chooser": "decider", "context_judge": "gap_reader", "kind": "misconception",
            "named_json": {"belief_statement": "Believes a region is a probability."}, "action": "belief_candidate",
            "algorithm_version": "mvp-0.55", "pipeline_version": "t", "created_at": "2026-11-07T09:01:40Z"})
    _brief, _book, record = world.brief(world.offer())
    order = [(c["kind"], c.get("mark"), c["text"][:12]) for c in record["confusions"]]
    assert order == [("hypothesis", "my_gap", "Mixes up arg"), ("hypothesis", None, "Thinks the g"),
                     ("learner_text_gap", None, "Believes a r")], "my_gap first, a retired cause left out, then gaps"


def test_a_statement_whose_inputs_cannot_be_established_is_not_searched(world):
    attempt = world.miss()
    [row] = world.diagnose(attempt)
    with world.repository.connection() as connection:
        record_text_write(connection, kind="hypothesis", record_id=str(row["id"]), text=CONFUSION, writer="t",
                          record=WriteRecord.incomplete("a reader's inputs were not recorded"))
        connection.commit()
    brief, _book, record = world.brief(world.offer())
    [confusion] = record["confusions"]
    assert "text" not in confusion and "could not be established" in confusion["withheld"]
    assert SOFTMAX not in _refs(brief) and record["status"] == "none"


def test_a_miss_on_protected_material_adds_nothing(tmp_path):
    world = World(tmp_path, reserved=True)
    attempt = world.miss(item="pi_eig_reserved")
    _exec(world.repository, "UPDATE practice_attempts SET learning_object_id = ? WHERE id = ?", (LO, attempt))
    world.diagnose(attempt)
    brief, _book, record = world.brief(world.offer())
    assert SOFTMAX not in _refs(brief) and record["status"] == "none"
    assert record["why"] == "the attempt behind the lesson is protected material"
    assert "confusions" not in record, "nothing of a protected attempt's diagnosis is read"


def test_the_query_is_the_diagnosed_statement_never_an_expected_answer_a_rubric_or_the_analysis(world, monkeypatch):
    from learnloop.source_retrieval import section_coverage as SC

    seen: list[str] = []
    real = SC.search_sections

    def spy(vault, repository, library, query, **kwargs):
        seen.append(query)
        assert kwargs.get("read_only") is True and not kwargs.get("deep", False), "keyword only, no model"
        return real(vault, repository, library, query, **kwargs)

    monkeypatch.setattr(SC, "search_sections", spy)
    world.brief(_diagnosed(world))
    assert seen == [CONFUSION]
    for secret in ("THEY WROTE", "argmax over the logits", "okapi", "lemur"):
        assert all(secret not in query for query in seen)


def test_no_score_or_stuck_flag_selects_sections(world):
    """The same diagnosed confusion finds the same sections whatever the attempt's score or stuck flag; the module
    reads neither."""

    attempt = world.miss(points=0, stuck=True)
    world.diagnose(attempt)
    decision = world.offer()
    first, _b, record = world.brief(decision)
    _exec(world.repository, "UPDATE practice_attempts SET declared_stuck = 0, correctness = 0.75, rubric_score = 3 "
                            "WHERE id = ?", (attempt,))
    second, _b2, record2 = world.brief(decision)
    assert _refs(first) == _refs(second) == [LINKED, SOFTMAX]
    assert [e["ref"] for e in record["added"]] == [e["ref"] for e in record2["added"]]
    import re

    from learnloop.teacher import diagnosed_sources as DS

    code = re.sub(r'""".*?"""', "", Path(DS.__file__).read_text(encoding="utf-8"), flags=re.S)
    for name in ("correctness", "rubric_score", "declared_stuck", "p_fail", "mastery", "expected_answer", "rubric"):
        assert name not in code, name


def test_the_search_makes_no_model_call_and_writes_nothing(world, monkeypatch):
    decision = _diagnosed(world)
    from learnloop.source_retrieval import queries

    def refuse(*args, **kwargs):
        raise AssertionError("a model call at lesson open")

    monkeypatch.setattr(queries, "embed_query_texts", refuse)
    monkeypatch.setattr(queries, "rewrite_query", refuse)
    before = {name: _rows(world.repository, f"SELECT COUNT(*) AS n FROM {name}")[0]["n"]
              for name in ("source_retrieval_deliveries", "agent_runs") if _has(world, name)}
    _brief, _book, record = world.brief(decision)
    assert record["status"] == "added"
    after = {name: _rows(world.repository, f"SELECT COUNT(*) AS n FROM {name}")[0]["n"] for name in before}
    assert before == after


def _has(world: World, name: str) -> bool:
    return bool(_rows(world.repository, "SELECT 1 FROM sqlite_master WHERE name = ?", (name,)))
