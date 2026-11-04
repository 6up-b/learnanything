"""The owner's ruling of Nov 4, 2026, replacing R3: only reserved questions stop a probe.

Past exam answers can inform causes, and an old record no longer blocks by itself. A machine check
compares each cause and each generated question against what is still reserved or withheld; a match
sends that miss to the practice lane.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

import pytest

from learnloop import learner_protection
from learnloop.db.stores import followup_serve as store
from learnloop.db.stores import write_provenance as wp
from learnloop.followup_run import admission, authoring, router
from learnloop.followup_run.authoring import CAUSE_MATCHES_RESERVED, QUESTION_MATCHES_RESERVED
from learnloop.followup_serve import identity, workflow as wf
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.followup_serve_helpers import (
    CLOCK,
    AuthorFake,
    BlindRivalClient,
    _item_path,
    author_clients,
    live_miss,
    live_shape_vault,
    run_jobs,
)

RESERVED_ITEM = "pi_eigen_001"
STEM = "Sentinel stem: diagonalize the reserved sentinel matrix over the given sentinel field today."
KEY = "Sentinel key: the reserved eigenbasis sentinel is built from the three sentinel vectors."
RUBRIC = "Sentinel rubric: names the reserved sentinel criterion for the three sentinel vectors exactly."


def _reserve(monkeypatch, *, item_id=RESERVED_ITEM, reason=learner_protection.WITHHELD_EXAM):
    real = learner_protection.withheld_items

    def withheld(vault_arg, repository_arg):
        seen = real(vault_arg, repository_arg)
        return learner_protection.Withheld(
            reasons={**seen.reasons, item_id: reason}, available=True, known_items=seen.known_items,
            unknowns=seen.unknowns, exam=seen.exam,
        )

    monkeypatch.setattr(learner_protection, "withheld_items", withheld)


def _with_reserved_question(paths, repository):
    path = _item_path(paths, RESERVED_ITEM)
    payload = read_yaml(path)
    payload["prompt"], payload["expected_answer"] = STEM, KEY
    payload["grading_rubric"]["criteria"][0]["description"] = RUBRIC
    write_yaml(path, payload)
    return load_vault(paths.root)


def _setup(tmp_path, monkeypatch, *, quoting=""):
    paths, vault, repository = live_shape_vault(tmp_path)
    vault = _with_reserved_question(paths, repository)
    _reserve(monkeypatch)
    client = BlindRivalClient()
    client.quoting = quoting
    result, outcome = live_miss(vault, repository, client)
    return paths, vault, repository, result, outcome


def _reasons(repository, workflow_id):
    with repository.connection() as connection:
        return [event["reason"] for event in store.workflow_events(connection, workflow_id)]


@pytest.mark.parametrize("words", [STEM, KEY, RUBRIC], ids=["stem", "solution", "rubric"])
def test_a_cause_quoting_a_reserved_question_takes_the_practice_lane(tmp_path, monkeypatch, words):
    _paths, vault, repository, _result, outcome = _setup(tmp_path, monkeypatch, quoting=f" {words}")
    decided = []
    monkeypatch.setattr(router, "decide", lambda *a, **k: decided.append(1))
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    row = wf.get(repository, outcome.workflow_id)
    assert row["state"] == wf.SETTLED and row["lane"] == wf.LANE_PRACTICE and row["feedback_released_at"]
    assert _reasons(repository, outcome.workflow_id)[-1] == CAUSE_MATCHES_RESERVED
    assert fake.calls == 0 and decided == []


def test_a_past_exam_answer_on_a_question_no_longer_reserved_can_inform_a_cause(tmp_path, monkeypatch):
    """Exam work on a question nothing reserves: its words in a cause stop nothing."""

    words = "my answer on that past exam used the sentinel words nobody reserves at all"
    paths, vault, repository = live_shape_vault(tmp_path)
    client = BlindRivalClient()
    client.quoting = f" {words}"
    result, outcome = live_miss(vault, repository, client)
    with repository.connection() as connection:
        connection.execute(
            "UPDATE practice_attempts SET attempt_type = 'exam_attempt', learner_answer_md = ? WHERE id = ?",
            (words, "att_02_svd_fail"))
        connection.commit()
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1 and wf.get(repository, outcome.workflow_id)["state"] == wf.READY


@pytest.mark.parametrize("field", ["prompt", "expected", "rubric"])
def test_an_authored_question_echoing_a_reserved_one_is_refused_with_nothing_served(tmp_path, monkeypatch, field):
    paths, vault, repository, result, outcome = _setup(tmp_path, monkeypatch)

    class Echoes(AuthorFake):
        def run_followup_probe_authoring(self, context):
            authored = super().run_followup_probe_authoring(context)
            if field == "prompt":
                return authored.model_copy(update={"prompt_md": f"Now try this. {STEM}"})
            if field == "expected":
                return authored.model_copy(update={"expected_answer_md": KEY})
            first = authored.criteria[0].model_copy(update={"description": RUBRIC})
            return authored.model_copy(update={"criteria": [first, *authored.criteria[1:]]})

    fake = Echoes()
    run_jobs(vault, repository, clients=author_clients(fake))
    row = wf.get(repository, outcome.workflow_id)
    assert fake.calls == 1
    assert row["state"] == wf.SETTLED and row["lane"] == wf.LANE_PRACTICE and row["feedback_released_at"]
    assert _reasons(repository, outcome.workflow_id)[-1] == QUESTION_MATCHES_RESERVED
    assert not row["practice_item_id"] and not row["presentation_id"]
    # Nothing was written: no identity, no file.
    assert identity.generated_probe_ids(repository) == frozenset()
    assert not [path for path in Path(paths.root).rglob("pi_gen_*")]


def _old_records(monkeypatch, repository, row):
    real = wp.stored_record
    monkeypatch.setattr(wp, "stored_record",
                        lambda connection, kind, record_id: None if kind == "hypothesis" else real(connection, kind, record_id))


@pytest.mark.parametrize("kind", ["missing", "incomplete"])
def test_a_vault_with_exam_attempts_and_incomplete_records_reaches_the_probe_lane(tmp_path, monkeypatch, kind):
    paths, vault, repository, result, outcome = _setup(tmp_path, monkeypatch)
    with repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET attempt_type = 'exam_attempt' WHERE id = 'att_02_svd_fail'")
        ids = [row[0] for row in connection.execute(
            "SELECT id FROM causal_hypotheses WHERE attempt_id = ?", (result.attempt_id,))]
        connection.commit()
    if kind == "missing":
        _old_records(monkeypatch, repository, None)
    else:
        with repository.connection() as connection:
            for hypothesis_id in ids:
                statement = repository.causal_hypothesis(hypothesis_id)["statement"]
                wp.record_text_write(connection, kind="hypothesis", record_id=hypothesis_id, text=statement, writer="old",
                                     record=wp.WriteRecord.incomplete("old"))
            connection.commit()
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1 and wf.get(repository, outcome.workflow_id)["state"] == wf.READY


def test_the_admission_receipt_says_what_the_causes_records_covered(tmp_path, monkeypatch):
    _paths, vault, repository, _result, outcome = _setup(tmp_path, monkeypatch)
    with repository.connection() as connection:
        connection.execute("UPDATE practice_attempts SET attempt_type = 'exam_attempt' WHERE id = 'att_02_svd_fail'")
        connection.commit()
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    row = wf.get(repository, outcome.workflow_id)
    with repository.connection() as connection:
        reviewed = connection.execute(
            "SELECT review_reason FROM causal_probe_candidates WHERE id = ?", (row["probe_candidate_id"],)).fetchone()[0]
    receipt = json.loads(reviewed)
    assert receipt["reserved_check"] == "passed"
    assert {entry["record"] for entry in receipt["causes_record"]} <= {"complete", "incomplete", "missing", "stale"}
    assert all("exam_answers" in entry and "answers" in entry for entry in receipt["causes_record"])


def test_reserved_questions_and_what_quotes_them_stay_out_of_the_authors_context(tmp_path, monkeypatch):
    paths, vault, repository = live_shape_vault(tmp_path)
    # An ordinary item on the missed topic whose words quote the reserved question.
    path = _item_path(paths, "pi_svd_compute_002")
    payload = read_yaml(path)
    payload["prompt"] = f"Worked from the exam: {STEM}"
    write_yaml(path, payload)
    vault = _with_reserved_question(paths, repository)
    payload = read_yaml(_item_path(paths, RESERVED_ITEM))
    payload["learning_object_id"] = "lo_svd_compute"
    write_yaml(_item_path(paths, RESERVED_ITEM), payload)
    vault = load_vault(paths.root)
    _reserve(monkeypatch)
    _result, outcome = live_miss(vault, repository, BlindRivalClient())
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 1
    text = json.dumps(asdict(fake.contexts[0]), default=str)
    assert "Sentinel" not in text and "sentinel" not in text


def test_a_generated_question_may_share_a_topic_with_a_reserved_one(tmp_path, monkeypatch):
    _paths, vault, repository, _result, outcome = _setup(tmp_path, monkeypatch)
    class SameTopic(AuthorFake):
        def run_followup_probe_authoring(self, context):
            authored = super().run_followup_probe_authoring(context)
            return authored.model_copy(update={"prompt_md": f"{authored.prompt_md} Diagonalize a small matrix to check."})

    run_jobs(vault, repository, clients=author_clients(SameTopic()))
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.READY


def test_a_check_waiting_holds_nothing_here(tmp_path, monkeypatch):
    paths, vault, repository = live_shape_vault(tmp_path)
    vault = _with_reserved_question(paths, repository)
    _reserve(monkeypatch, reason=learner_protection.WITHHELD_COLD)
    client = BlindRivalClient()
    client.quoting = f" {STEM}"
    _result, outcome = live_miss(vault, repository, client)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.READY


def test_protection_that_cant_be_read_fails_closed(tmp_path, monkeypatch):
    paths, vault, repository = live_shape_vault(tmp_path)
    _result, outcome = live_miss(vault, repository, BlindRivalClient())
    monkeypatch.setattr(learner_protection, "withheld_items",
                        lambda *_a: learner_protection.Withheld(available=False))
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    assert fake.calls == 0
    assert wf.get(repository, outcome.workflow_id)["state"] == wf.FAILED


def test_the_retired_codes_are_gone():
    import learnloop.followup_run.authoring as module

    assert not hasattr(module, "CAUSES_UNACCOUNTED") and not hasattr(module, "CAUSES_FROM_EXAM")
    assert not hasattr(module, "hypotheses_exam_reason") and not hasattr(learner_protection, "CAUSE_UNRECORDED")
    assert not hasattr(learner_protection.PastWork, "exam_reason")


def test_an_exam_sittings_miss_reaches_the_probe_lane_after_the_sitting(tmp_path):
    """§3.1 amended: nothing interrupts a sitting, since the pipeline runs at ``finish_exam``, and the
    cap holds (``test_an_exam_sitting_records_eligibility_inside_its_cap``). Its own misses may
    now get a question afterwards, and feedback isn't held, since the report shows it."""

    from learnloop.attempts.post_attempt import run_exam_sitting_pipeline
    from tests.followup_serve_helpers import rival_causes_vault
    from tests.test_causal_p2_acceptance import _divergent_failure

    vault, repository, _paths = rival_causes_vault(tmp_path)
    result = _divergent_failure(vault, repository, attempt_id="att_exam_0")
    outcome = run_exam_sitting_pipeline(vault, repository, results=[result], followup_surface="desktop", clock=CLOCK)[0]
    fake = AuthorFake()
    run_jobs(vault, repository, clients=author_clients(fake))
    row = wf.get(repository, outcome.workflow_id)
    assert row["origin"] == "exam" and not row["feedback_held"]
    assert row["state"] == wf.READY and row["lane"] == wf.LANE_PROBE and fake.calls == 1


def test_the_mint_and_batch_paths_refuse_a_reserved_question_at_the_tag_only(tmp_path, monkeypatch):
    from learnloop.diagnosis.probe_instance_generation import _reproduces_reserved

    paths, vault, repository = live_shape_vault(tmp_path)
    vault = _with_reserved_question(paths, repository)
    _reserve(monkeypatch)
    payload = {"prompt": f"Try: {STEM}", "expected_answer": "x", "grading_rubric": {"criteria": []}}
    assert _reproduces_reserved(vault, repository, payload)
    assert not _reproduces_reserved(vault, repository, {**payload, "prompt": "Something else entirely here."})
    below = live_shape_vault(tmp_path / "below", version="mvp-0.44")[1]
    assert not _reproduces_reserved(below, repository, payload)


def test_a_short_reserved_stem_is_still_a_match_within_longer_words(tmp_path, monkeypatch):
    from learnloop.content.authoring.practice_leakage import reserved_findings, reserved_questions

    paths, vault, repository = live_shape_vault(tmp_path)
    monkeypatch.setattr(authoring, "protection_view", lambda *_a: None)
    _reserve(monkeypatch, item_id="pi_unrelated_001")  # "Name a prime."
    reserved = reserved_questions(vault, repository, learner_protection.withheld_items(vault, repository))
    assert reserved_findings("Earlier you were asked to name a prime, and did.", reserved)
    assert not reserved_findings("Earlier you named a number.", reserved)


def test_wording_an_ordinary_item_already_shows_is_no_match(tmp_path, monkeypatch):
    """On a real copy 28 of 84 ordinary items shared a six-word shingle with the reserved questions,
    mostly formulas ("(u+v)+w = u+(v+w)"). What the learner is already shown can't leak."""

    from learnloop.content.authoring.practice_leakage import reserved_findings, reserved_questions

    shared = "for every vector in the space the identity holds"
    paths, vault, repository = live_shape_vault(tmp_path)
    for item_id, words in ((RESERVED_ITEM, f"{STEM} {shared}"), ("pi_svd_compute_002", f"Show that {shared}.")):
        path = _item_path(paths, item_id)
        payload = read_yaml(path)
        payload["prompt"] = words
        write_yaml(path, payload)
    vault = load_vault(paths.root)
    _reserve(monkeypatch)
    reserved = reserved_questions(vault, repository, learner_protection.withheld_items(vault, repository))
    assert not reserved_findings(f"We know that {shared} here.", reserved)
    assert reserved_findings("the reserved sentinel matrix over the given sentinel field", reserved)
