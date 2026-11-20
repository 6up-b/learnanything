"""Synthetic sections and structured answers for the section writer."""
from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import json

from learnloop.ai.errors import AITurnTimeout
from learnloop.ai.strict_schema import strict_output_schema
from learnloop.clock import FrozenClock
from learnloop.content.pipeline.jobs import DurableIngestJobs
from learnloop.content.pipeline.runner import RunnerServices
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.vault.loader import add_note, load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.helpers import NOW, create_basic_vault
from tests.proposal_persistence_helpers import _generated_practice_proposal_payload
from tests.structured_ai import StructuredClientFake, _request_context

TOPICS = ["lo_topic_f", "lo_topic_b", "lo_topic_e", "lo_topic_a", "lo_topic_d", "lo_topic_c", "lo_topic_h", "lo_topic_g"]


def section(tmp_path, count=8):
    paths = create_basic_vault(tmp_path / "vault")
    add_note(paths.root, "linear-algebra", "section", "Section", "The topic definitions.", clock=FrozenClock(NOW))
    template = read_yaml(paths.learning_object_path("linear-algebra", "lo_svd_definition"))
    for lo in TOPICS[:count]:
        write_yaml(paths.learning_object_path("linear-algebra", lo), {**template, "id": lo, "title": lo})
    return paths, Repository(paths.sqlite_path)


def answer(topics, *, duplicate=False, invalid=False):
    items = []
    for lo in topics:
        data = _generated_practice_proposal_payload({
            "learning_object_id": lo,
            "prompt": "Repeated prompt" if duplicate else f"Explain {lo}.",
            "surface_family": lo,
            "repair_targets": ["recall"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "criterion_facet_weights": {"correctness": {"recall": 1.0}},
            "difficulty": 0.25,
        })
        row = data["items"][0]
        row.update(client_item_id=lo, proposed_entity_id=f"pi_{lo}", source_ref_ids=["note_section"])
        if invalid:
            row["payload"]["learning_object_id"] = "lo_missing"
        items.append(row)
    return AuthoringProposal.model_validate({"summary": "Section questions", "source_refs": [
        {"ref_type": "note", "ref_id": "note_section"}], "items": items})


class Writer(StructuredClientFake):
    def __init__(self, *, fail=(), duplicate=False, invalid=False, bad_topics=()):
        self.calls = []
        self.requests = []
        self.contexts = []
        self.fail = set(fail)
        self.bad_topics = set(bad_topics)
        self.duplicate = duplicate
        self.invalid = invalid
        self.before = lambda: None

    def complete(self, request):
        if request.purpose != "authoring":
            return super().complete(request)
        context = _request_context(request.prompt, request.purpose)
        repair = context.instructions.startswith("REPAIR PASS:")
        topics = [] if repair else [t["learning_object_id"] for t in ast.literal_eval(
            next(line.removeprefix("Targets: ") for line in context.instructions.splitlines() if line.startswith("Targets: ")))]
        self.calls.append(topics)
        self.contexts.append(context)
        self.requests.append({"prompt": request.prompt, "schema": strict_output_schema(request.result_model),
                              "purpose": request.purpose, "output_budget_tokens": request.output_budget_tokens,
                              "output_ceiling_tokens": request.output_ceiling_tokens, "timeout_seconds": request.timeout_seconds,
                              "workspace": request.workspace, "isolated": request.isolated,
                              "reasoning_effort": request.reasoning_effort, "images": request.images})
        self.before()
        if topics and topics[0] in self.bad_topics:
            from learnloop.ai.errors import AIInvalidOutput
            raise AIInvalidOutput("invalid JSON after one wire repair")
        if len(self.calls) in self.fail:
            raise AITurnTimeout("third topic timed out")
        if repair:
            failing = json.loads(context.instructions.split("FAILING_ITEMS: ", 1)[1])
            return answer([entry["client_item_id"] for entry in failing], duplicate=self.duplicate)
        return answer(topics, duplicate=self.duplicate, invalid=self.invalid)


def request_digest(request):
    return sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def jobs_for(paths, repo, writer):
    jobs = DurableIngestJobs()
    jobs.bind(repo, paths.root, background=False, clock=FrozenClock(NOW),
              services=RunnerServices(synthesis_client_factory=lambda ctx: writer))
    return jobs


def enqueue(jobs, count=8):
    return jobs.enqueue_practice_expansion(learning_object_ids=TOPICS[:count],
                                         reason="reader_section_completed:section_one", source_refs=[])


def comparable_rows(repo, patch):
    rows = deepcopy(repo.proposal_items(patch))
    for row in rows:
        for key in ("id", "patch_id", "proposed_patch_id", "created_at", "updated_at", "applied_change_batch_id", "decided_at"):
            row.pop(key, None)
        for key in ("created_at", "updated_at"):
            row["payload"].pop(key, None)
    return sorted(rows, key=lambda row: row["client_item_id"])


def live_questions(paths):
    return {key for key in load_vault(paths.root).practice_items if key.startswith("pi_lo_topic_")}
