"""The relabel round (owner 2026-10-23: "Sonnet both + rubric"), fakes only.

* **The probability service copy's Qwen backfill.** Paid run 3 left 177 of
  337 records unembedded: ``ProtectedTextRefused`` on two passes, although
  the copy's redaction had blanked every withheld block (111). The
  diagnosis (counts only, on the run's own copies): the guard's probe of one
  withheld 19-character assessment-lane heading is text that seven
  PERMITTED blocks of the same extraction also contain, so the guard refused
  permitted text. Redaction was right and nothing withheld was about to be
  sent. The guard now probes only what is distinctive to withheld text (every
  window of it that no permitted block contains, not just its first 48
  characters), and the backfill refuses, before sending, any record of a
  withheld block (an unredacted copy). Both fail closed.
* **The relabel.** Label A is Claude Sonnet 5.5 too, an independent pass; the
  relevance rubric is revised on the development slice and frozen by hash.
* **The cumulative cap.** A new authorization carries every earlier
  authorization's committed spend (and seals those ledgers), so the $40 is
  E0-wide, enforced by the ledger before each send.
* **Reuse.** ``--reuse-run`` points a new plan at an earlier run's
  content-keyed stores (checkpoints, vectors, service copies, records); its
  ledger chain still knows every earlier admission.

No network: a socket guard refuses any connection.
"""
from __future__ import annotations

import socket
from contextlib import closing

import pytest

from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings.budget import E0Ledger
from tests.e0_fakes import FakeQwenClient, build_e0_vault
from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: The fake vault's withheld solution block (``role_hint="solution"``).
SOLUTION = "Solution: apply linearity to 0 = 0 + 0 and cancel T(0) on both sides."


class Qwen(FakeQwenClient):
    """The fake production embedding client with the backfill's capability fields."""

    modalities = frozenset({"text"})
    max_input_tokens = 32_768


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def _set_text(paths, prefix: str, text: str) -> None:
    """Rewrite one block of the frozen fake copy (before any snapshot)."""

    from learnloop.db.connection import connect

    with closing(connect(paths.sqlite_path)) as connection:
        changed = connection.execute("UPDATE source_document_blocks SET text = ? WHERE text LIKE ?",
                                     (text, prefix + "%")).rowcount
        connection.commit()
    assert changed == 1


def _service(tmp_path, paths, snapshot, *, redact: bool = True):
    from learnloop.experiments.contextual_embeddings.system_arms import (
        enable_embeddings_on_copy,
        make_service_copy,
        open_service,
        redact_service_copy,
    )

    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "svc" / "qwen")
    enable_embeddings_on_copy(root)
    handle = open_service(root)
    if redact:
        redact_service_copy(handle, snapshot.policy)
    return handle


# -- 1. the backfill: permitted text that contains a withheld block's text ----------------


def test_a_permitted_block_containing_a_withheld_blocks_text_is_embedded(tmp_path, verified_prices):
    """Paid run 3's probability failure, in miniature: a permitted block
    contains the whole text of a withheld one (there, a 19-character
    assessment-lane heading inside seven permitted Text blocks). Redaction
    blanks the withheld block; the permitted one is what the backfill sends,
    and it must be embedded, so the dense coverage completes."""

    from learnloop.experiments.contextual_embeddings.system_arms import (
        backfill_service_copy,
        dense_coverage_complete,
        guarded_factory,
    )

    paths, _repository = build_e0_vault(tmp_path)
    _set_text(paths, "Exercise 2.1.", "Exercise 2.1. Show that every linear map sends the zero vector to the zero "
              "vector. A worked answer would begin: " + SOLUTION)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    assert any(snapshot.policy.verdict(extraction_id, block.span_id) and block.text == SOLUTION
               for extraction_id, blocks in snapshot.blocks.items() for block in blocks)
    handle = _service(tmp_path, paths, snapshot)
    qwen = Qwen()
    reports = backfill_service_copy(handle, E0Ledger(tmp_path / "ledger"),
                                    client_factory=guarded_factory(lambda: qwen, snapshot))
    assert all(report.get("status") == "complete" for report in reports), [r.get("error_type") for r in reports]
    assert dense_coverage_complete(handle)["complete"] is True


def test_the_guard_still_refuses_withheld_text_even_past_its_first_characters(tmp_path):
    """Failing closed, and stronger than before: every window of a withheld
    block that no permitted block contains is probed, so a leaked tail is
    refused as well as a leaked head (the old guard probed the first 48
    characters only)."""

    from learnloop.experiments.contextual_embeddings.system_arms import ProtectedTextRefused, guarded_factory

    paths, _repository = build_e0_vault(tmp_path)
    tail = " and so T(0) = 0, which is what the exercise asks; nothing else is needed for this proof."
    _set_text(paths, "Solution: apply linearity", SOLUTION + tail)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    inner = FakeQwenClient()
    client = guarded_factory(lambda: inner, snapshot)()
    client.embed(["Definition 1.1 (Vector space). A vector space is a set V"], "retrieval-document")
    for leaked in (SOLUTION + tail, "Section: Chapter 2\n" + tail.strip(), "Exam question 1: prove that the "
                   "additive inverse in a vector space is unique."):
        with pytest.raises(ProtectedTextRefused):
            client.embed(["permitted text", leaked], "retrieval-document")
    assert len(inner.calls) == 1


def test_an_unredacted_service_copy_is_refused_before_any_request(tmp_path, verified_prices):
    """The record-level check: a backfill whose records include a withheld
    block (the copy was never redacted) sends nothing, whatever the text."""

    from learnloop.experiments.contextual_embeddings.system_arms import backfill_service_copy, guarded_factory

    paths, _repository = build_e0_vault(tmp_path)
    snapshot = C.build_snapshot(C.open_copy(paths.root))
    handle = _service(tmp_path, paths, snapshot, redact=False)
    qwen = Qwen()
    reports = backfill_service_copy(handle, E0Ledger(tmp_path / "ledger"),
                                    client_factory=guarded_factory(lambda: qwen, snapshot), policy=snapshot.policy)
    assert qwen.calls == []
    assert any(report.get("status") == "refused_unredacted" and report.get("withheld_records", 0) > 0
               for report in reports)
