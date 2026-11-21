"""Missing wire IDs keep paid questions, with deterministic names and checkpoint replay."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re

import pytest
from pydantic import ValidationError, model_validator

from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import execute_structured_operation
from learnloop.config.schema import ChatGPTPlanProviderConfig
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.content.proposals import proposals
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.helpers import NOW
from tests.plan_deadline_fakes import Session, completed, install_stream
from tests.section_question_parts_helpers import TOPICS, answer, enqueue, jobs_for, section


def unnamed_answer():
    data = answer(TOPICS[:1], per_topic=3).model_dump(mode="json")
    for item in data["items"]:
        item["proposed_entity_id"] = item["payload"]["id"] = None
    return data


def plan_writer(monkeypatch, *answers):
    client = ChatGPTPlanProviderClient("plan", ChatGPTPlanProviderConfig(
        model="fake", base_url="http://127.0.0.1"), session=Session())
    _, requests, _ = install_stream(monkeypatch, lambda n: [
        (1, completed(json.dumps(answers[min(n, len(answers)) - 1]))),
    ])
    return client, requests


def ids(proposal):
    return [item.proposed_entity_id or item.payload.id for item in proposal.items]


def test_three_unnamed_questions_apply_and_finish_topic_without_any_repair(tmp_path, monkeypatch):
    paths, repo = section(tmp_path, 1)
    raw = unnamed_answer()
    client, requests = plan_writer(monkeypatch, raw)
    batch = enqueue(jobs_for(paths, repo, client), 1)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed", job["error"]
    assert (job["current_window"], job["total_windows"]) == (1, 1)
    rows = repo.proposal_items(job["payload"]["question_parts"][0]["patch_id"])
    minted = [row["payload"]["id"] for row in rows]
    assert len(set(minted)) == 3
    assert all(re.fullmatch(r"pi_[a-z0-9_]+", value) for value in minted)
    assert set(minted) <= set(load_vault(paths.root).practice_items)
    assert [row["decision"] for row in rows] == ["accepted"] * 3
    assert len(requests) == 1
    assert ids(AuthoringProposal.model_validate_json(json.dumps(raw))) == minted


def test_checkpoint_replay_keeps_minted_ids_and_applies_nothing_twice(tmp_path, monkeypatch):
    paths, repo = section(tmp_path, 1)
    client, requests = plan_writer(monkeypatch, unnamed_answer())
    jobs = jobs_for(paths, repo, client)
    apply = proposals.auto_apply_rows
    applied = []

    def crash(root, patch, rows):
        apply(root, patch, rows)
        applied.extend(row["payload"]["id"] for row in rows)
        raise RuntimeError("lost progress after apply")

    monkeypatch.setattr(proposals, "auto_apply_rows", crash)
    batch = enqueue(jobs, 1)
    assert len(applied) == 3
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "failed"
    before = repo.proposal_items(repo.proposal_batches()[0]["id"])
    monkeypatch.setattr(proposals, "auto_apply_rows", lambda *a: pytest.fail("applied twice"))
    jobs.resume_batch(batch)
    assert repo.ingest_jobs_for_batch(batch)[0]["status"] == "completed"
    assert repo.proposal_items(repo.proposal_batches()[0]["id"]) == before
    assert set(applied) <= set(load_vault(paths.root).practice_items)
    assert len(requests) == 1
    assert len(repo.proposal_batches()) == 1


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_repeated_client_ids_and_blank_fields_mint_distinct_stable_safe_ids(empty):
    raw = unnamed_answer()
    for item in raw["items"]:
        item["client_item_id"] = "../../same name!?"
        item["proposed_entity_id"] = item["payload"]["id"] = empty
    raw["items"][1] = deepcopy(raw["items"][0])
    before = deepcopy(raw)
    first = AuthoringProposal.model_validate(raw)
    assert len(set(ids(first))) == 3
    assert all(re.fullmatch(r"pi_[a-z0-9_]+", value) for value in ids(first))
    assert ids(first) == ids(AuthoringProposal.model_validate_json(json.dumps(raw)))
    assert ids(first) == ids(AuthoringProposal.model_validate(first.model_dump(mode="json")))
    assert raw == before


def test_reserved_named_id_wins_even_when_it_occurs_after_the_unnamed_item():
    raw = unnamed_answer()
    candidate = ids(AuthoringProposal.model_validate(raw))[0]
    raw["items"][2]["proposed_entity_id"] = candidate
    proposal = AuthoringProposal.model_validate(raw)
    assert ids(proposal)[2] == candidate
    assert ids(proposal)[0] == candidate + "_2"
    assert len(set(ids(proposal))) == 3


def test_fresh_and_checkpointed_authoring_keep_the_same_minted_and_named_ids(tmp_path, monkeypatch):
    paths, repo = section(tmp_path, 1)
    raw = unnamed_answer()
    reserved = ids(AuthoringProposal.model_validate(raw))[0]
    raw["items"][2]["payload"]["id"] = reserved
    client, requests = plan_writer(monkeypatch, raw)
    context = proposals.build_authoring_context(load_vault(paths.root))

    fresh = proposals.dispatch_authoring_request(client, context)
    assert len(requests) == 1
    saved = proposals.dispatch_authoring_request(client, context, checkpoints=repo)
    assert len(requests) == 2 and requests[0] == requests[1]
    replayed = proposals.dispatch_authoring_request(client, context, checkpoints=repo)
    assert len(requests) == 2

    assert ids(fresh) == ids(saved) == ids(replayed)
    assert ids(replayed)[0] == reserved + "_2"
    assert ids(replayed)[2] == reserved


def test_vault_collision_uses_first_free_suffix_and_checkpoint_keeps_it(tmp_path, monkeypatch):
    paths, repo = section(tmp_path, 1)
    raw = unnamed_answer()
    candidate = ids(AuthoringProposal.model_validate(raw))[0]
    template = read_yaml(paths.practice_item_path("linear-algebra", "pi_svd_define_001"))
    for value in (candidate, candidate + "_2"):
        write_yaml(paths.practice_item_path("linear-algebra", value), {**template, "id": value})
    client, requests = plan_writer(monkeypatch, raw)
    jobs = jobs_for(paths, repo, client)
    batch = enqueue(jobs, 1)
    job = repo.ingest_jobs_for_batch(batch)[0]
    assert job["status"] == "completed", job["error"]
    rows = repo.proposal_items(job["payload"]["question_parts"][0]["patch_id"])
    assert rows[0]["payload"]["id"] == candidate + "_3"
    assert all(row["decision"] == "accepted" for row in rows)
    saved = proposals.dispatch_authoring_request(client, proposals.build_authoring_context(load_vault(paths.root)),
                                                 checkpoints=repo)
    # The same saved request returns its original names after they become occupied.
    context = proposals.build_authoring_context(load_vault(paths.root))
    for value in ids(saved):
        write_yaml(paths.practice_item_path("linear-algebra", value), {**template, "id": value})
    assert ids(proposals.dispatch_authoring_request(client, context, checkpoints=repo)) == ids(saved)
    assert len(requests) == 2


@pytest.mark.parametrize("kind,prefix", [("learning_object", "lo_"), ("concept", "concept_")])
def test_other_supported_create_types_keep_their_prefix(kind, prefix):
    raw = unnamed_answer()
    raw["items"] = [{**raw["items"][0], "item_type": kind, "payload": {"id": None, "title": "Title"}}]
    assert ids(AuthoringProposal.model_validate(raw))[0].startswith(prefix)


def test_unnamed_error_type_still_requires_a_taxonomy_name():
    raw = unnamed_answer()
    raw["items"] = [{**raw["items"][0], "item_type": "error_type", "payload": {"id": None}}]
    with pytest.raises(ValidationError, match="proposed_entity_id is required"):
        AuthoringProposal.model_validate(raw)


def recorded_answer():
    golden = json.loads((Path(__file__).parent / "fixtures" / "diagnosis_journey_golden.json").read_text())

    def outputs(value):
        if isinstance(value, dict):
            text = value.get("output_text")
            if isinstance(text, str) and '"proposed_entity_id":"pi_ltg_seed_001"' in text:
                yield text
            for child in value.values():
                yield from outputs(child)
        elif isinstance(value, list):
            for child in value:
                yield from outputs(child)

    return next(outputs(golden))


@pytest.mark.parametrize("owner", ["proposed", "payload", "both"])
def test_named_recorded_answer_produces_byte_identical_rows(tmp_path, monkeypatch, owner):
    paths, _ = section(tmp_path, 1)
    monkeypatch.setattr(proposals, "new_ulid", lambda: "fixed-row-id")
    raw = json.loads(recorded_answer())
    if owner in {"payload", "both"}:
        raw["items"][0]["payload"]["id"] = raw["items"][0]["proposed_entity_id"]
    if owner == "payload":
        raw["items"][0]["proposed_entity_id"] = None
    proposal = AuthoringProposal.model_validate_json(json.dumps(raw))
    rows = [proposals.proposal_item_row(item, NOW.isoformat(), vault=load_vault(paths.root),
                                      proposal=proposal, provider="plan") for item in proposal.items]
    serialized = json.dumps(rows, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert sha256(serialized.encode()).hexdigest() == "88222adcb3f52df301850e4adab6fc8f850a214d924e233e6135291a95f9389a"


class PositiveAnswer(WireModel):
    value: int

    @model_validator(mode="after")
    def positive(self):
        if self.value <= 0:
            raise ValueError("value must be positive")
        return self


def test_plan_repair_tells_the_model_the_python_validation_error(monkeypatch):
    client, requests = plan_writer(monkeypatch, {"value": -1}, {"value": 1})
    result = execute_structured_operation(client, purpose="test", prompt="original", result_model=PositiveAnswer)
    assert result.value == 1
    first, repair = requests
    assert "value must be positive" in repair["input"][0]["content"]
    assert first["input"][0]["content"] == "original"


@pytest.mark.parametrize("entry", ["canonical_ingest", "file_import"])
def test_other_wire_entry_points_reserve_vault_ids(tmp_path, monkeypatch, entry):
    from learnloop.content.pipeline.ai_contracts import CanonicalIngestContext
    from learnloop.content.pipeline.source_ingestion import request_canonical_ingest
    from learnloop.cli.app import propose

    paths, repo = section(tmp_path, 1)
    raw = unnamed_answer()
    candidate = ids(AuthoringProposal.model_validate(raw))[0]
    template = read_yaml(paths.practice_item_path("linear-algebra", "pi_svd_define_001"))
    write_yaml(paths.practice_item_path("linear-algebra", candidate), {**template, "id": candidate})
    if entry == "canonical_ingest":
        client, requests = plan_writer(monkeypatch, raw)
        context = CanonicalIngestContext(vault_root=str(paths.root), source_kind="website_page",
                                         canonical_source={}, chunks=[])
        result = request_canonical_ingest(client, context)
        assert ids(result)[0] == candidate + "_2"
        assert len(requests) == 1
    else:
        source = tmp_path / "proposal.json"
        source.write_text(json.dumps(raw))
        propose(file=source, vault=paths.root)
        rows = repo.proposal_items(repo.proposal_batches()[0]["id"])
        assert rows[0]["payload"]["id"] == candidate + "_2"
        assert all(row["decision"] == "accepted" for row in rows)
