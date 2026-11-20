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


def topics_in(root, subject, template, count):
    """``count`` topics copied from ``template`` and the note their questions cite, in another
    library (a built book's), so the section writer's answers resolve there too; with a facet of
    that library's registry for them to measure."""

    from learnloop.vault.paths import VaultPaths

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    add_note(root, subject, "section", "Section", "The topic definitions.", clock=FrozenClock(NOW))
    data = read_yaml(paths.learning_object_path(subject, template))
    for lo in TOPICS[:count]:
        write_yaml(paths.learning_object_path(subject, lo), {**data, "id": lo, "title": lo})
    return TOPICS[:count], sorted(vault.evidence_facets)[0]


def answer(topics, *, duplicate=False, invalid=False, per_topic=1, held=(), repeated=(), facet="recall"):
    """One topic's answer: ``per_topic`` grounded, audited questions per topic, each citing the
    supplied note. ``held`` names the positions (0-based, within a topic) the model marks
    ``review_required`` anyway, as the live route did for every question of a finished section;
    ``repeated`` the positions whose prompt is the same in every topic (a later topic's is refused)."""

    items = []
    for lo in topics:
        for position in range(per_topic):
            name = lo if position == 0 else f"{lo}_{position}"
            data = _generated_practice_proposal_payload({
                "learning_object_id": lo,
                "prompt": "Repeated prompt" if duplicate or position in repeated else (
                    f"Explain {lo}." if position == 0 else f"Explain {lo}, case {position}."),
                "surface_family": lo,
                "repair_targets": [facet],
                "evidence_facets": [facet],
                "evidence_weights": {facet: 1.0},
                "criterion_facet_weights": {"correctness": {facet: 1.0}},
                "difficulty": 0.25,
            })
            row = data["items"][0]
            row.update(client_item_id=name, proposed_entity_id=f"pi_{name}", source_ref_ids=["note_section"])
            if position in held:
                row.update(review_route="review_required",
                           rationale="Grounded in the section's note; the audit passed. Marked for review.")
            if invalid:
                row["payload"]["learning_object_id"] = "lo_missing"
            items.append(row)
    return AuthoringProposal.model_validate({"summary": "Section questions", "source_refs": [
        {"ref_type": "note", "ref_id": "note_section"}], "items": items})


class Writer(StructuredClientFake):
    def __init__(self, *, fail=(), duplicate=False, invalid=False, bad_topics=(), per_topic=1, held=(), repeated=(),
                 facet="recall"):
        self.calls = []
        self.requests = []
        self.contexts = []
        self.fail = set(fail)
        self.bad_topics = set(bad_topics)
        self.duplicate = duplicate
        self.invalid = invalid
        self.per_topic = per_topic
        self.held = set(held)
        self.repeated = set(repeated)
        self.facet = facet
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
        return answer(topics, duplicate=self.duplicate, invalid=self.invalid, per_topic=self.per_topic,
                      held=self.held, repeated=self.repeated, facet=self.facet)


def held_writer(per_topic=3, held=(0, 1, 2), facet="recall"):
    """The live route's answer: every question grounded in the section and audited, yet marked
    review_required (by default all three of each topic)."""

    return Writer(per_topic=per_topic, held=held, facet=facet)


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
