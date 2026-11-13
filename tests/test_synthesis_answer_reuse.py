"""Saved synthesis answers answer only the requests they stand for, and a rejection drops only what it judged.

A completed shard is reused only when it stands for one request: a shard with a span round reruns its passes,
each from its own checkpoint, so a changed span request is paid (phase-1 review I4) and a rejected span answer is
dropped with its base pass (I6). A gate rejection drops the saved answers it judged, not whatever is saved under
their keys by then, so a fresh answer another run paid for survives (I5).

No LLM: house fake clients count every call.
"""

from __future__ import annotations

import pytest

from learnloop.ai.execution import ModelCheckpoint
from learnloop.content.synthesis import source_append as append_module
from learnloop.content.synthesis import source_set_synthesis as synthesis
from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis, SynthSpanRequest
from learnloop.content.synthesis.source_append import append_source
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map
from learnloop.db.repositories import Repository

from tests.source_append_helpers import FakeAppendClient, _bootstrap_and_add
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


# --- I6: a rejection drops a reused shard's span answer too ------------------


def test_a_rejected_reused_shard_drops_its_span_round_answer(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient(builder=_with_span_round)

    def fail_before_gates(*_args, **_kwargs):
        raise RuntimeError("interrupted")

    monkeypatch.setattr(synthesis, "_facet_identity_plan", fail_before_gates)
    with pytest.raises(RuntimeError, match="interrupted"):
        _build(root, repo, client)
    monkeypatch.undo()
    assert (len(_base_calls(client)), len(_span_calls(client))) == (1, 1)

    def gates_reject(*_args, **_kwargs):
        raise StudyMapError("synthesis_gate_failed", "rejected")

    monkeypatch.setattr(synthesis, "_gate_and_persist", gates_reject)
    with pytest.raises(StudyMapError, match="rejected"):
        _build(root, repo, client)
    monkeypatch.undo()

    _build(root, repo, client)

    # Both rejected answers were dropped: the third attempt pays for each.
    assert (len(_base_calls(client)), len(_span_calls(client))) == (2, 2)


# --- I5: a rejection drops the answer it judged, not a newer one -------------


def test_a_checkpoint_discard_keeps_an_answer_saved_after_the_one_judged(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    first = ModelCheckpoint(repo, "k", "synthesis_pass", SourceSetSynthesis.model_validate)
    second = ModelCheckpoint(repo, "k", "synthesis_pass", SourceSetSynthesis.model_validate)
    first.save(SourceSetSynthesis(summary="old"))
    judged_by_first = first.fetch()
    judged_by_second = second.fetch()

    first.discard(judged_by_first[1])
    first.save(SourceSetSynthesis(summary="fresh"))
    second.discard(judged_by_second[1])

    assert first.load().summary == "fresh"


def test_a_bootstrap_rejection_keeps_a_fresh_answer_another_run_saved(tmp_path, monkeypatch):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient()
    fresh = SourceSetSynthesis(summary="a fresh answer another run paid for")

    def another_run_then_reject(*_args, **_kwargs):
        # Another run judged the same answer first, dropped it, and a retry
        # saved a fresh one under the same key; then this run's gates reject.
        for key in _stored(repo, "synthesis_pass"):
            repo.discard_model_checkpoint(key)
            repo.save_model_checkpoint(key, purpose="synthesis_pass", result=fresh.model_dump(mode="json"))
            shard = repo.synthesis_shard_result(key)
            repo.save_synthesis_shard_result(shard_key=key, shard_ordinal=0, shard_count=1,
                                             result={"result": fresh.model_dump(mode="json")})
            assert shard is not None
        raise StudyMapError("synthesis_gate_failed", "rejected")

    monkeypatch.setattr(synthesis, "_gate_and_persist", another_run_then_reject)
    with pytest.raises(StudyMapError, match="rejected"):
        _build(root, repo, client)

    stored = _stored(repo, "synthesis_pass")
    assert len(stored) == 1 and "another run paid for" in next(iter(stored.values()))
    shard = repo.synthesis_shard_result(next(iter(stored)))
    assert shard is not None and shard["output"]["result"]["summary"] == fresh.summary


def test_an_append_rejection_keeps_a_fresh_answer_another_run_saved(tmp_path, monkeypatch):
    root, repo = _bootstrap_and_add(tmp_path)
    fresh = {"summary": "a fresh answer another run paid for"}

    def another_run_then_reject(*_args, **_kwargs):
        for key in _stored(repo, "append_reconciliation"):
            repo.discard_model_checkpoint(key)
            repo.save_model_checkpoint(key, purpose="append_reconciliation", result=fresh)
        raise StudyMapError("append_gate_failed", "rejected")

    monkeypatch.setattr(append_module, "run_synthesis_gates", another_run_then_reject)
    with pytest.raises(StudyMapError, match="rejected"):
        append_source(root, "set_la", client=FakeAppendClient(), new_revision_ids=["rev_alt"], repository=repo,
                      clock=_CLOCK)

    stored = _stored(repo, "append_reconciliation")
    assert len(stored) == 1 and "another run paid for" in next(iter(stored.values()))
