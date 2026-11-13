"""Model-work checkpoints: one cycle (load, validate, discard, save) for every
paid structured call; stale results are discarded, and every path keys a
window the same way for the same inputs."""

from __future__ import annotations

from types import SimpleNamespace

from pydantic import BaseModel
import pytest

from learnloop.ai.errors import AITurnTimeout
from learnloop.ai.execution import ModelCheckpoint, checkpointed, content_key, request_key
from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices
from learnloop.content.synthesis.ai_contracts import ConceptGraphStructuring, ConceptMergeGroup
from learnloop.content.synthesis import source_unit_inventory as inventory
from learnloop.content.synthesis.source_set_synthesis import StudyMapError, create_study_map
from learnloop.db.repositories import Repository
from tests.source_inventory_helpers import FakeInventoryClient, _block, _ir, _persist, _register_revision, _CLOCK
from tests.source_set_synthesis_helpers import (
    FakeSynthesisClient,
    _default_payload,
    _distinct_title_builder,
    _setup,
    _setup_two_chapters,
)


class _Store:
    """A checkpoint store in memory, recording what the cycle does to it."""

    def __init__(self, saved=None):
        self.rows = dict(saved or {})
        self.saves: list[tuple[str, str, dict, dict | None]] = []

    def model_checkpoint(self, cache_key):
        return {"result": self.rows[cache_key], "usage": {}} if cache_key in self.rows else None

    def save_model_checkpoint(self, cache_key, *, purpose, result, usage=None):
        self.saves.append((cache_key, purpose, result, usage))
        self.rows.setdefault(cache_key, result)

    def discard_model_checkpoint(self, cache_key):
        self.rows.pop(cache_key, None)


class _Answer(BaseModel):
    text: str


def test_the_request_key_is_what_is_sent_and_nothing_left_unset():
    assert request_key(purpose="p", prompt="hello", schema={"type": "object"}, settings={"model": "m"}) == content_key(
        {"purpose": "p", "prompt": "hello", "schema": {"type": "object"}, "settings": {"model": "m"}})
    # The older shapes keep their own fields through identity_extra, and leave out what they never had.
    assert request_key(purpose="p", prompt="hello", settings={"model": "m"}, identity_extra={"schema_version": 1}) == (
        content_key({"purpose": "p", "prompt": "hello", "settings": {"model": "m"}, "schema_version": 1}))
    assert request_key(purpose="p", prompt="hello!") != request_key(purpose="p", prompt="hello")


def test_a_saved_answer_is_read_back_and_nothing_is_paid():
    checkpoint = checkpointed(_Store(), purpose="p", prompt="q", schema=None, settings=None, result_model=_Answer)
    checkpoint.store.rows[checkpoint.key] = {"text": "saved"}
    paid = []

    answer, reused = checkpoint.answer(lambda: paid.append(1) or _Answer(text="fresh"))

    assert (answer, reused, paid) == (_Answer(text="saved"), True, [])


def test_a_fresh_answer_is_saved_with_its_usage_before_it_is_returned():
    store = _Store()
    checkpoint = checkpointed(store, purpose="p", prompt="q", schema=None, settings=None, result_model=_Answer)

    answer, reused = checkpoint.answer(lambda: _Answer(text="fresh"), usage=lambda a: {"chars": len(a.text)})

    assert (answer, reused) == (_Answer(text="fresh"), False)
    assert store.saves == [(checkpoint.key, "p", {"text": "fresh"}, {"chars": 5})]


def test_a_failed_call_saves_nothing():
    store = _Store()
    checkpoint = checkpointed(store, purpose="p", prompt="q", schema=None, settings=None, result_model=_Answer)

    def fail():
        raise RuntimeError("provider down")

    with pytest.raises(RuntimeError):
        checkpoint.answer(fail)
    assert store.saves == []


@pytest.mark.parametrize("stored", [{"text": None}, ["not", "an", "object"], {"text": "short"}],
                         ids=["invalid", "not_an_object", "fails_its_check"])
def test_a_saved_answer_that_no_longer_reads_is_discarded_and_paid_once(stored):
    def at_least_six(answer):
        if len(answer.text) < 6:
            raise ValueError("too short")

    store = _Store()
    checkpoint = checkpointed(store, purpose="p", prompt="q", schema=None, settings=None, result_model=_Answer,
                              validate=at_least_six)
    store.rows[checkpoint.key] = stored

    answer, reused = checkpoint.answer(lambda: _Answer(text="a longer one"))

    assert (answer.text, reused) == ("a longer one", False)
    assert store.rows[checkpoint.key] == {"text": "a longer one"}


def test_a_checkpoint_under_its_own_key_reads_its_own_shape():
    store = _Store({"own:key": {"verdict": "same", "model": "m"}})
    checkpoint = ModelCheckpoint(store, "own:key", "own", lambda stored: (stored["verdict"], stored["model"]))

    assert checkpoint.load() == ("same", "m")
    store.rows["own:key"] = {"model": "m"}
    assert checkpoint.load() is None and "own:key" not in store.rows


def _checkpoint_rows(repo, purpose):
    with repo.connection() as connection:
        return connection.execute(
            "SELECT cache_key, result_json FROM model_work_checkpoints WHERE purpose = ?", (purpose,)
        ).fetchall()


def _one_unit_document(repo):
    _register_revision(repo)
    document = _ir([("u1", "Chapter", [_block("s1", "An eigenvector scales under a matrix.")], "hash1", 1)])
    _persist(repo, document, revision_id="rev1", extraction_id="ext1")
    return document


def test_inventory_window_checkpoint_that_no_longer_validates_is_discarded(tmp_path, monkeypatch):
    repo = Repository(tmp_path / "state.sqlite")
    document = _one_unit_document(repo)
    window = inventory.build_inventory_windows(document, "u1", input_budget_tokens=20000)[0]
    monkeypatch.setattr(inventory, "build_inventory_windows", lambda *_args, **_kwargs: [{**window, "window_ordinal": 1}, {**window, "window_ordinal": 2}])
    original = inventory.request_source_unit_inventory
    interrupted = False

    def request(client, context):
        nonlocal interrupted
        if context.unit_view["window_ordinal"] == 2 and not interrupted:
            interrupted = True
            raise AITurnTimeout("interrupted window")
        return original(client, context)

    monkeypatch.setattr(inventory, "request_source_unit_inventory", request)
    client = FakeInventoryClient()
    with pytest.raises(AITurnTimeout):
        inventory.run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)
    [(key, _result)] = _checkpoint_rows(repo, "inventory_window")
    # The saved window now cites a span the unit no longer has.
    with repo.connection() as connection:
        connection.execute(
            "UPDATE model_work_checkpoints SET result_json = ? WHERE cache_key = ?",
            ('{"concept_mentions": [{"name": "eigenvector", "span_ids": ["s_gone"]}]}', key),
        )

    result = inventory.run_unit_inventory(repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK)

    assert result.usage["reused_windows"] == 0
    assert result.usage["calls"] == 2
    assert all("s_gone" not in row[1] for row in _checkpoint_rows(repo, "inventory_window"))


def test_synthesis_pass_checkpoint_that_no_longer_validates_is_discarded(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)

    def builder(context, _n):
        return _default_payload(context).model_copy(update={"summary": "long summary " * 400})

    client = FakeSynthesisClient(builder=builder)
    with pytest.raises(StudyMapError, match="exceeded its output budget"):
        create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK,
                         budget_overrides={"synthesis_shard_output_tokens": 100})
    [(key, _result)] = _checkpoint_rows(repo, "synthesis_pass")
    with repo.connection() as connection:
        connection.execute(
            "UPDATE model_work_checkpoints SET result_json = ? WHERE cache_key = ?",
            ('{"span_requests": "not a list"}', key),
        )

    result = create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK)

    assert result.proposal_id is not None
    assert len(client.calls) == 2
    assert all("not a list" not in row[1] for row in _checkpoint_rows(repo, "synthesis_pass"))


class _ConfiguredInventoryClient(FakeInventoryClient):
    """An inventory client whose provider settings go beyond its model slug."""

    profile = SimpleNamespace(
        model="fake-model-1", base_url="https://inventory.example/v1",
        reasoning_effort="high", thinking=None, response_format=None,
    )


def test_ingest_job_and_direct_inventory_key_windows_identically(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    _one_unit_document(repo)
    direct = inventory.prepare_unit_inventory(
        repo, "ext1", "u1", role="reference", client=_ConfiguredInventoryClient(),
        input_budget_tokens=20000, clock=_CLOCK,
    )
    assert direct.window_keys

    runner = IngestRunner(
        repo, vault_root=tmp_path, worker_id="worker", clock=_CLOCK,
        services=RunnerServices(inventory_client_factory=lambda ctx: _ConfiguredInventoryClient()),
    )
    batch = runner.enqueue_batch("import_inventory", [JobSpec("inventory", {
        "extraction_id": "ext1", "input_budget_tokens": 20000,
        "units": [{"unit_id": "u1", "role": "reference"}],
    })])
    runner.drain()

    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert sorted(row[0] for row in _checkpoint_rows(repo, "inventory_window")) == sorted(direct.window_keys)


class _StructuringClient(FakeSynthesisClient):
    """Two shards of distinct titles, and a structuring pass that merges them."""

    def __init__(self, *, builder=_distinct_title_builder):
        super().__init__(builder=builder)
        self.structuring_contexts: list = []

    def run_concept_graph_structuring(self, context):
        self.structuring_contexts.append(context)
        ids = [concept["client_item_id"] for concept in context.concepts]
        return ConceptGraphStructuring(
            merge_groups=[ConceptMergeGroup(canonical_client_id=ids[0], duplicate_client_ids=ids[1:])],
        )


def _two_shard_study_map(root, repo, client):
    return create_study_map(root, "set_la", client=client, brief={"depth": "intro"}, repository=repo,
                            clock=_CLOCK, budget_overrides={"synthesis_shard_input_tokens": 1})


def test_a_retry_after_a_structuring_pass_reads_its_checkpoint(tmp_path, monkeypatch):
    root, repo = _setup_two_chapters(tmp_path)
    client = _StructuringClient()

    def explode(self, batch, rows):
        raise RuntimeError("disk full")

    monkeypatch.setattr(Repository, "persist_proposal_batch", explode)
    with pytest.raises(RuntimeError, match="disk full"):
        _two_shard_study_map(root, repo, client)
    monkeypatch.undo()
    assert len(client.structuring_contexts) == 1

    result = _two_shard_study_map(root, repo, client)

    assert len(client.structuring_contexts) == 1
    assert result.item_counts["concept"] == 1
    usage = repo.synthesis_run(result.synthesis_run_id)["actual_usage"]
    assert usage["consolidated_concepts"] == 1
    assert len(_checkpoint_rows(repo, "concept_graph_structuring")) == 1


def test_a_gate_failure_drops_the_structuring_answer_it_judged(tmp_path):
    def builder(context, n):
        payload = _distinct_title_builder(context, n)
        if n == 1:
            payload.practice_items[1].depends_on_client_item_ids = ["no_such_item"]
        return payload

    root, repo = _setup_two_chapters(tmp_path)
    client = _StructuringClient(builder=builder)
    with pytest.raises(StudyMapError) as excinfo:
        _two_shard_study_map(root, repo, client)
    assert excinfo.value.code == "synthesis_gate_failed"
    assert len(client.structuring_contexts) == 1

    assert _checkpoint_rows(repo, "concept_graph_structuring") == []
