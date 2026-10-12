"""Gate G3: arm-blindness of the generator, closed-book and grader (spec P3)."""

from __future__ import annotations

import dataclasses
import json
import re

from learnloop.ai.spend import SpendCaps
from learnloop.config import LearnLoopConfig
from learnloop.ids import new_ulid
from learnloop.projects.ai_contracts import BLIND_CONTEXTS
from learnloop.projects.ai_runtime import PaidCalls
from learnloop.projects.capture import enroll_repo, sweep
from learnloop.projects.experiment_store import ProjectStore
from learnloop.projects.probes import generate_probes, grade_responses, record_response
from tests.project_support import ProjectFake, clock_at, fake_resolver, isolated_git, make_model_repo  # noqa: F401

FORBIDDEN_FIELD = re.compile(
    r"arm|explanation|judge|feedback|provenance|agent|declaration|accept|usage|gate|assist|looked|"
    r"trailer|author_kind|closed_book|who|learner|history",
    re.IGNORECASE,
)
ALLOWED_FIELDS = {
    "ProbeAuthoringContext": {"repo_name", "commit_message", "files", "candidate_count", "kinds"},
    "ClosedBookContext": {"questions"},
    "ProbeGradingContext": {"items"},
}


def test_context_dataclasses_have_no_field_for_arm_explanation_judge_or_provenance():
    for context in BLIND_CONTEXTS:
        names = {field.name for field in dataclasses.fields(context)}
        assert names == ALLOWED_FIELDS[context.__name__]
        assert not [name for name in names if FORBIDDEN_FIELD.search(name)]


def test_rendered_prompts_carry_no_provenance_declaration_or_closed_book_origin(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    repo = make_model_repo(tmp_path / "repo")
    config = LearnLoopConfig()
    enroll_repo(vault, config, repo.path, clock=clock_at(0))
    sweep(vault, config, clock=clock_at(0))
    store = ProjectStore.for_vault(vault)
    (diff,) = store.diffs()
    # Provenance the generator and grader must never see.
    store.add_provenance({"id": new_ulid(), "diff_id": diff["id"], "accept_style": "all_at_once",
                          "usage_tap": "it_designed", "created_at": "2026-10-01T12:00:00Z"})
    fake = ProjectFake()
    resolver = fake_resolver(fake)
    routes = {role: resolver(None, None, role) for role in ("authoring", "closed_book", "grading")}
    caps = SpendCaps(max_candidates=100, max_pairs=0, max_retries=2, max_calls=100, max_total_tokens=10**7, max_estimated_usd=100)
    generate_probes(store, vault, config, PaidCalls(store, caps=caps, run_id="g"), routes, store.diffs(), clock=clock_at(0))
    selected = [probe for probe in store.probes_for_diff(diff["id"]) if probe["selected"]]
    record_response(store, selected[0]["id"], kind="answer", answer="It applies relu after scaling.",
                    declaration="used_ai", clock=clock_at(8))
    grade_responses(store, PaidCalls(store, caps=caps, run_id="r"), routes["grading"], clock=clock_at(8))

    prompts = {purpose: [] for purpose in ("project_probe_authoring", "project_closed_book_check", "project_probe_grading")}
    for purpose, prompt in fake.requests:
        prompts[purpose].append(prompt)
    assert all(prompts.values())
    everything = "\n".join(prompt for group in prompts.values() for prompt in group)
    for leaked in (
        "claude_code", "Co-Authored-By", "anthropic", "Claude Opus",  # agent attribution
        "all_at_once", "it_designed", "per_hunk",  # provenance taps
        "used_ai", "unassisted", "looked",  # the owner's declaration
        "\"arm\"", "gate_skipped", "explanation",  # M1b material
        "closed_book_answer", "rejected_generic",  # closed-book origin of an answer
    ):
        assert leaked not in everything, leaked

    # The closed-book model sees questions only: no code, no reference answers.
    closed_book = "\n".join(prompts["project_closed_book_check"])
    assert "torch.relu" not in closed_book and "self.scale" not in closed_book
    for probe in store.probes_for_diff(diff["id"]):
        assert probe["reference_answer"] not in closed_book
    # The grader is not told which answers are the owner's and which the closed-book model's.
    grading_payloads = [json.loads(prompt.split("\n\n")[-1])["context"]["items"] for prompt in prompts["project_probe_grading"]]
    for items in grading_payloads:
        for item in items:
            assert set(item) == {"id", "question", "reference_answer", "evidence", "answer"}
