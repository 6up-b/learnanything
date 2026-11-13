"""Saved synthesis answers answer only the requests they stand for, and a rejection drops only what it judged.

A completed shard is reused only when it stands for one request: a shard with a span round reruns its passes,
each from its own checkpoint, so a changed span request is paid (phase-1 review I4) and a rejected span answer is
dropped with its base pass (I6). A gate rejection drops the saved answers it judged, not whatever is saved under
their keys by then, so a fresh answer another run paid for survives (I5).

No LLM: house fake clients count every call.
"""

from __future__ import annotations

import pytest

from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis, SynthSpanRequest
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.db.repositories import Repository

from tests.source_set_synthesis_helpers import (
    FakeSynthesisClient,
    _CLOCK,
    _default_payload,
    _first_semantic_span,
    _setup,
)


def _with_span_round(context, _n):
    """A base pass that asks for its first cited span; the span round answers."""

    if context.resolved_spans:
        return _default_payload(context)
    extraction, unit, span = _first_semantic_span(context)
    return SourceSetSynthesis(span_requests=[SynthSpanRequest(extraction_id=extraction, unit_id=unit, span_id=span)])


def _base_calls(client):
    return [call for call in client.calls if not call.resolved_spans]


def _span_calls(client):
    return [call for call in client.calls if call.resolved_spans]


def _build(root, repo, client, **kwargs):
    return create_study_map(root, "set_la", client=client, brief={"depth": "intro"}, repository=repo,
                            clock=_CLOCK, **kwargs)


def _stored(repo, purpose):
    with repo.connection() as connection:
        return {row["cache_key"]: row["result_json"] for row in connection.execute(
            "SELECT cache_key, result_json FROM model_work_checkpoints WHERE purpose = ?", (purpose,))}


# --- I4: a completed shard stands for every request it answered -------------


def test_a_completed_shard_does_not_answer_a_changed_span_round_request(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient(builder=_with_span_round)

    def explode(self, batch, rows, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(Repository, "persist_proposal_batch", explode)
    with pytest.raises(RuntimeError, match="disk full"):
        _build(root, repo, client)
    monkeypatch.undo()
    assert (len(_base_calls(client)), len(_span_calls(client))) == (1, 1)

    result = _build(root, repo, client, budget_overrides={"synthesis_span_char_cap": 12})

    # The base request is unchanged and answers from its checkpoint; the span
    # request now carries shorter text, so it is sent.
    assert (len(_base_calls(client)), len(_span_calls(client))) == (1, 2)
    assert all(len(span["text"]) <= 12 for span in client.calls[-1].resolved_spans)
    assert result.proposal_id is not None


def test_an_unchanged_two_pass_shard_is_answered_by_its_checkpoints(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient(builder=_with_span_round)

    def explode(self, batch, rows, **_kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(Repository, "persist_proposal_batch", explode)
    with pytest.raises(RuntimeError, match="disk full"):
        _build(root, repo, client)
    monkeypatch.undo()

    result = _build(root, repo, client)

    assert len(client.calls) == 2  # nothing paid again
    assert result.span_request_count == 1
