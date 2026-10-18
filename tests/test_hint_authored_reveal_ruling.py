"""Adaptive hints H2b: the authored-reveal ruling (orchestrator ruling on the H2a landing finding).

An ``authored`` hint served by the hint service must leave the same evidence
as the same hint revealed by the client today. The client's reveal
(``practice.record_hint_reveal``) writes no ``reveal_events`` row (spec §3.2;
§10.1 successor 3 keeps authored reveals out of the reveal ledger in v1), so
the service's delivery of an authored hint writes none either. It still
counts one at level 3 as a server row, which matches the client count it
replaces. Every other kind keeps §5's ``tutor_answer`` reveal on a key
overlap. The first two tests fail on ``5b2efaf24`` (H2a's delivery wrote a
``hint:authored:L3`` reveal). Fakes only.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.vault.yaml_io import read_yaml, write_yaml
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.hint_fakes import ITEM, WORK, ChooserFake, WriterFake, assists, hint_vault, prefer, reveals, store_map

SELF_GRADE = {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}
#: An authored hint that states part of the key, so a lexical overlap exists
#: (H2a's landing measured 0.143 for the same shape on a real item).
OVERLAPPING = ["Integrate the density: F(x) = x^2 on [0, 1].", "Evaluate the CDF at the point."]


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _sidecar(tmp_path, config: str = ""):
    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n' + config)
    store_map(paths)
    item_path = paths.practice_item_path("linear-algebra", ITEM)
    data = read_yaml(item_path)
    data["hints"] = list(OVERLAPPING)
    write_yaml(item_path, data)
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    ctx.hint_seed = "e"
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    return paths, ctx, session


def _attempt(paths, attempt_id):
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM practice_attempts WHERE id = ?", (attempt_id,)).fetchone())


def _submit(ctx, session, key, *, hints: int = 0):
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": hints, "selfGrade": SELF_GRADE, "submissionId": key})


def test_a_service_served_authored_hint_writes_no_reveal_and_counts_one(tmp_path):
    # The chooser's fallback serves the item's first authored hint (§4.5).
    paths, ctx, session = _sidecar(tmp_path, "chooser_enabled = false\n")
    ctx.hint_writer_client = WriterFake()
    job = _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                               "answerMd": WORK})
    result = job["result"]
    assert (result["status"], result["kind"], result["authoredIndex"], result["shown"]) == ("ready", "authored", 0,
                                                                                           True)
    assert result["hintMd"] == OVERLAPPING[0]
    # The ruling: no reveal row, exactly as the client's reveal of the same hint.
    assert reveals(paths.sqlite_path) == []
    attempt = _attempt(paths, _submit(ctx, session, "k1")["attemptId"])
    # Still counted once at level 3 as a server row (the client sent 0).
    assert (attempt["hints_used"], attempt["primed"]) == (1, 0)
    [row] = assists(paths.sqlite_path)
    assert (row["hint_kind"], row["level"], row["counted_by"], row["shown"]) == ("authored", 3, "server", 1)


def test_the_same_hint_leaves_the_same_evidence_by_either_path(tmp_path):
    served_paths, served, session = _sidecar(tmp_path / "served", "chooser_enabled = false\n")
    served.hint_writer_client = WriterFake()
    _call(served, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                            "answerMd": WORK})
    by_service = _attempt(served_paths, _submit(served, session, "k1")["attemptId"])

    client_paths, client, other = _sidecar(tmp_path / "client")
    _call(client, "practice.record_hint_reveal", {"sessionId": other, "practiceItemId": ITEM, "submissionId": "k1",
                                                  "authoredIndex": 0, "answerMd": WORK})
    by_client = _attempt(client_paths, _submit(client, other, "k1", hints=1)["attemptId"])

    assert reveals(served_paths.sqlite_path) == reveals(client_paths.sqlite_path) == []
    for column in ("hints_used", "primed"):
        assert by_service[column] == by_client[column]


def test_a_written_kind_still_writes_its_tutor_answer_reveal(tmp_path):
    paths, ctx, session = _sidecar(tmp_path)
    ctx.hint_writer_client = WriterFake()
    ctx.hint_chooser_client = ChooserFake(prefer("walkthrough@L5", 0.9))
    _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                         "answerMd": WORK, "takenLevel": 5})
    [reveal] = reveals(paths.sqlite_path)
    assert (reveal["source_kind"], reveal["basis"]) == ("tutor_answer", "hint:walkthrough:L5")
