"""RW4e Codex review F1: role proposals under concurrent writers (production WAL settings).

The identity lookup (is there already a proposal for this passage and role?),
the status check (is it still ``proposed``?), the object's creation and its
version append run in one ``BEGIN IMMEDIATE`` transaction, so:

* a learner's review that lands while a judge is between reading the head
  and appending its agreement stands: the judge's version goes in before the
  review (never after it), and the review stays the head;
* two judges proposing the same role on the same passage at once make one
  object with two versions (the agreement), never two objects.

Each test opens the race window deterministically: the first judge's identity
lookup starts the competing writer on another thread and gives it time to
commit before the judge writes. Fakes only; no model is reached.
"""
from __future__ import annotations

import json
import threading

import pytest

from learnloop.reader import source_objects as SO
from learnloop.reader import source_roles as RS
from tests.passage_cue_fakes import build_cue_vault, loaded

pytestmark = pytest.mark.durability

#: How long the competing writer is given to commit inside the race window. A
#: correct writer is blocked by the judge's write lock for all of it.
RACE_WINDOW_SECONDS = 1.5


@pytest.fixture
def library(tmp_path):
    paths, repository, spans = build_cue_vault(tmp_path / "vault")
    with repository.connection() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    return paths, repository, spans


def _claim(span_id: str, role: str, confidence: str = "high", *, ledger_id: str = "rlb_x") -> dict:
    return {"extraction_id": "ext_text", "span_id": span_id, "role": role, "confidence": confidence,
            "ledger_id": ledger_id}


def _propose(paths, repository, claims, *, judge):
    return RS.propose_roles(loaded(paths), repository, claims, judge=judge, prompt_version=f"{judge}.v1",
                            model="fake-model")


def _race(monkeypatch, competitor):
    """Run ``competitor`` on another thread inside the first identity lookup
    (after it read, before anything is written); returns its join handle."""

    real = RS._existing
    state: dict = {"thread": None, "errors": []}

    def lookup(*args, **kwargs):
        found = real(*args, **kwargs)
        if state["thread"] is None:
            finished = threading.Event()

            def run():
                try:
                    competitor()
                except BaseException as exc:  # noqa: BLE001 - surfaced by the test
                    state["errors"].append(exc)
                finally:
                    finished.set()

            state["thread"] = threading.Thread(target=run)
            state["thread"].start()
            finished.wait(RACE_WINDOW_SECONDS)
        return found

    monkeypatch.setattr(RS, "_existing", lookup)

    def join():
        assert state["thread"] is not None, "the race window never opened"
        state["thread"].join(30)
        assert not state["thread"].is_alive()
        if state["errors"]:
            raise state["errors"][0]

    return join


def _versions(repository, object_id: str) -> list[tuple[int, str, str | None]]:
    with repository.connection() as connection:
        return [(int(row[0]), str(row[1]), json.loads(row[2] or "{}").get("judge")) for row in connection.execute(
            "SELECT version_ordinal, status, content_json FROM source_object_versions "
            "WHERE source_object_id = ? ORDER BY version_ordinal", (object_id,))]


def test_a_review_between_a_judges_read_and_its_write_stands(library, monkeypatch):
    paths, repository, _spans = library
    (object_id,) = _propose(paths, repository, [_claim("t3", "contrast")], judge=RS.JUDGE_LABELLER)["written"]
    join = _race(monkeypatch, lambda: SO.review_source_object(
        repository, source_object_id=object_id, status="rejected"))
    _propose(paths, repository, [_claim("t3", "contrast", "medium", ledger_id="pcj_1")], judge=RS.JUDGE_CUE)
    join()
    head = repository.source_object_head(object_id)["version"]
    assert head["status"] == "rejected"
    versions = _versions(repository, object_id)
    # The judge's agreement went in before the review, never after it.
    assert [status for _ordinal, status, _judge in versions] == ["proposed", "proposed", "rejected"]
    vault = loaded(paths)
    assert [label for label in RS.role_proposals(vault, repository) if label.object_id == object_id] == []


def test_a_review_that_won_the_lock_first_takes_no_further_proposal(library, monkeypatch):
    paths, repository, _spans = library
    (object_id,) = _propose(paths, repository, [_claim("t3", "contrast")], judge=RS.JUDGE_LABELLER)["written"]
    SO.review_source_object(repository, source_object_id=object_id, status="rejected")
    out = _propose(paths, repository, [_claim("t3", "contrast", ledger_id="pcj_1")], judge=RS.JUDGE_CUE)
    assert out["versions"] == [] and out["written"] == []
    assert out["skipped"] == [{"key": ["ext_text", "t3"], "role": "contrast", "reason": "reviewed as rejected"}]
    with pytest.raises(SO.SourceObjectError):
        SO.append_proposal_version(repository, source_object_id=object_id, revision_id="rev_text",
                                   object_type="motif_or_passage", authorial_role="contrast", content={},
                                   citations=[{"span_id": "t3"}])
    assert repository.source_object_head(object_id)["version"]["status"] == "rejected"


def test_two_judges_at_once_make_one_object_with_their_agreement(library, monkeypatch):
    paths, repository, _spans = library
    join = _race(monkeypatch, lambda: _propose(
        paths, repository, [_claim("t3", "contrast", "medium", ledger_id="pcj_1")], judge=RS.JUDGE_CUE))
    _propose(paths, repository, [_claim("t3", "contrast", ledger_id="rlb_1")], judge=RS.JUDGE_LABELLER)
    join()
    with repository.connection() as connection:
        objects = [str(row[0]) for row in connection.execute(
            f"SELECT DISTINCT source_object_id FROM source_object_versions "
            f"WHERE source_object_id IN ({RS.PROPOSAL_KIND_SQL})")]
    assert len(objects) == 1
    versions = _versions(repository, objects[0])
    assert [ordinal for ordinal, _status, _judge in versions] == [1, 2]
    assert {judge for _ordinal, _status, judge in versions} == {RS.JUDGE_LABELLER, RS.JUDGE_CUE}
    (label,) = RS.role_proposals(loaded(paths), repository)
    assert set(label.judges) == {RS.JUDGE_LABELLER, RS.JUDGE_CUE} and label.versions == 2
