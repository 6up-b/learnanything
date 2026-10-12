"""Delayed probes (spec §5.2, §10 test_project_probes; gate G5 at the API)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.config import LearnLoopConfig
from learnloop.projects.ai_contracts import (
    ProbeCandidate,
    ProbeCandidates,
    ProbeCitation,
    probe_authoring_prompt,
)
from learnloop.projects.ai_runtime import PaidCalls
from learnloop.projects.capture import enroll_repo, load_bundle, sweep
from learnloop.projects.experiment_store import ProjectStore
from learnloop.projects.probes import (
    ProbeStateError,
    SealedProbeError,
    authoring_context,
    contest_grade,
    due_probes,
    generate_probes,
    grade_responses,
    open_probe,
    record_response,
    reveal,
    validate_candidate,
)
from tests.project_support import (
    ProjectFake,
    TempRepo,
    clock_at,
    fake_resolver,
    isolated_git,  # noqa: F401
    make_model_repo,
)

CAPS = SpendCaps(max_candidates=100, max_pairs=0, max_retries=2, max_calls=100, max_total_tokens=10**7, max_estimated_usd=100.0)


def _routes(fake, **kwargs):
    resolver = fake_resolver(fake, **kwargs)
    return {role: resolver(None, None, role) for role in ("authoring", "closed_book", "grading")}


@pytest.fixture
def captured(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    repo = make_model_repo(tmp_path / "repo")
    config = LearnLoopConfig()
    enroll_repo(vault, config, repo.path, clock=clock_at(0))
    sweep(vault, config, clock=clock_at(0))
    store = ProjectStore.for_vault(vault)
    (diff,) = store.diffs()
    return vault, config, store, diff


def _generate(vault, config, store, fake, **kwargs):
    paid = PaidCalls(store, caps=CAPS, run_id="run-1")
    return generate_probes(store, vault, config, paid, _routes(fake, **kwargs), store.diffs(probe_status="pending"), clock=clock_at(0))


def test_answer_first_schema_and_prompt():
    order = list(ProbeCandidate.model_json_schema()["properties"])
    assert order.index("reference_answer") < order.index("question")
    assert order.index("citations") < order.index("question")


def test_generation_filters_and_selects(captured):
    vault, config, store, diff = captured
    fake = ProjectFake()
    report = _generate(vault, config, store, fake)
    assert report.status == "complete"
    probes = {probe["question"].split(":")[0].strip(): probe for probe in store.probes_for_diff(diff["id"])}
    assert probes["Q-bad-quote"]["validity"] == "quote_mismatch"
    assert probes["Q-why-uncited"]["validity"] == "why_uncited"
    assert probes["Q-why-cited"]["validity"] == "valid"
    assert probes["Q-why-cited"]["rationale_label"] == "agent_stated"  # the agent wrote the commit message
    assert probes["Q-generic"]["status"] == "rejected_generic"
    survivors = {name for name, probe in probes.items() if probe["status"] == "survivor"}
    assert survivors == {"Q-what", "Q-where", "Q-why-cited"}
    selected = [probe for probe in probes.values() if probe["selected"]]
    assert len(selected) == 2 and all(probe["status"] == "survivor" for probe in selected)
    assert store.diff(diff["id"])["probe_status"] == "generated"
    assert fake.calls == {"authoring": 1, "closed_book": 1, "grading": 1}
    # Every verdict is in the judgment mirror.
    tasks = {row["task"] for row in store.judgments()}
    assert tasks == {"project_probe_validity", "project_closed_book"}
    assert len(store.judgments(task="project_probe_validity")) == 6
    assert len(store.judgments(task="project_closed_book")) == 4


def test_selection_is_seeded_and_reproducible(isolated_git, tmp_path):
    picks = []
    for attempt in range(2):
        vault = tmp_path / f"vault{attempt}"
        vault.mkdir()
        repo = make_model_repo(tmp_path / f"repo{attempt}")
        config = LearnLoopConfig()
        enroll_repo(vault, config, repo.path, clock=clock_at(0))
        sweep(vault, config, clock=clock_at(0))
        store = ProjectStore.for_vault(vault)
        with store.connection() as connection:  # same stored seed in both vaults
            connection.execute("UPDATE diffs SET selection_seed = 12345")
        _generate(vault, config, store, ProjectFake())
        picks.append(sorted(p["candidate_index"] for p in store.all_probes() if p["selected"]))
    assert picks[0] == picks[1]


def test_under_probed_when_fewer_than_two_survive(captured):
    vault, config, store, diff = captured
    _generate(vault, config, store, ProjectFake(all_generic=True))
    assert store.diff(diff["id"])["probe_status"] == "under_probed"
    assert sum(probe["selected"] for probe in store.probes_for_diff(diff["id"])) < 2


def test_resume_never_re_authors(captured):
    vault, config, store, diff = captured
    failing = ProjectFake(fail_closed_book=True)
    report = _generate(vault, config, store, failing)
    assert report.status == "partial"
    assert store.diff(diff["id"])["probe_status"] == "pending"
    assert store.diff(diff["id"])["generation_attempts"] == 1
    assert len(store.probes_for_diff(diff["id"])) == 6
    resumed = ProjectFake()
    _generate(vault, config, store, resumed)
    assert resumed.calls == {"closed_book": 1, "grading": 1}  # authoring was paid once
    assert store.diff(diff["id"])["probe_status"] == "generated"


def test_repeated_failures_mark_the_diff_failed(captured):
    vault, config, store, diff = captured
    for _ in range(3):
        _generate(vault, config, store, ProjectFake(fail_closed_book=True))
    assert store.diff(diff["id"])["probe_status"] == "failed"


def test_unready_provider_generates_nothing(captured):
    vault, config, store, diff = captured
    fake = ProjectFake()
    report = _generate(vault, config, store, fake, ready=False)
    assert report.status == "provider_unavailable" and fake.calls == {}
    assert store.probes_for_diff(diff["id"]) == []


def _bundle(captured):
    vault, _config, _store, diff = captured
    return load_bundle(vault, diff["bundle_hash"])


def _line(bundle, needle):
    entry = bundle["files"][0]
    excerpt = entry["excerpts"][0]
    for offset, line in enumerate(excerpt["lines"]):
        if needle in line:
            return excerpt["start_line"] + offset, line
    raise AssertionError(needle)


def test_citations_must_resolve_and_quote_verbatim(captured):
    bundle = _bundle(captured)
    number, code = _line(bundle, "torch.relu")
    good = ProbeCitation(source="file", path="model.py", line_start=number, line_end=number, quote="torch.relu(y)")

    def check(*citations, kind="what_does"):
        candidate = ProbeCandidate(kind=kind, reference_answer="r", citations=list(citations), question="q")
        return validate_candidate(candidate, bundle, agent_committed=True)

    assert check(good).status == "valid"
    assert check(good.model_copy(update={"path": "nope.py"})).status == "citation_unresolved"
    assert check(good.model_copy(update={"line_start": 900, "line_end": 901})).status == "citation_unresolved"
    assert check(good.model_copy(update={"line_end": number - 1})).status == "citation_unresolved"
    assert check(good.model_copy(update={"quote": "torch.sigmoid(y)"})).status == "quote_mismatch"
    assert check().status == "no_citation"
    assert check(ProbeCitation(source="commit_message", quote="Use relu so negative activations")).status == "valid"
    assert check(ProbeCitation(source="commit_message", quote="never said")).status == "quote_mismatch"
    assert check(ProbeCitation(source="diff", path="model.py", quote="return x * self.scale")).status == "valid"
    # why: needs a citation that states the reason (see the stated_reason tests below)
    assert check(good, kind="why").status == "why_uncited"
    comment_number, _ = _line(bundle, "Clamp negatives")
    comment = ProbeCitation(source="file", path="model.py", line_start=comment_number, line_end=comment_number,
                            quote="Clamp negatives so the GRU never sees a sign flip.", rationale=True)
    candidate = ProbeCandidate(kind="why", reference_answer="So the GRU never sees a sign flip.",
                               citations=[comment], question="q")
    result = validate_candidate(candidate, bundle, agent_committed=True)
    assert result.status == "valid" and result.rationale_label == "agent_stated"  # an added line
    context_line = ProbeCitation(source="file", path="model.py", line_start=1, line_end=1, quote="import torch", rationale=True)
    assert check(context_line, kind="why").status == "why_uncited"  # code is never a stated reason


def test_redacted_lines_cannot_be_quoted(captured):
    bundle = _bundle(captured)
    bundle["files"][0]["excerpts"][0]["lines"][0] = "[REDACTED:aws_access_key]"
    citation = ProbeCitation(source="file", path="model.py", line_start=1, line_end=1, quote="[REDACTED:aws_access_key]")
    candidate = ProbeCandidate(kind="what_does", reference_answer="r", citations=[citation], question="q")
    assert validate_candidate(candidate, bundle, agent_committed=True).status == "quote_mismatch"


def test_authoring_prompt_carries_numbered_lines(captured):
    vault, config, store, diff = captured
    context = authoring_context(_bundle(captured), repo_name="repo", config=config)
    prompt = probe_authoring_prompt(context)
    number, _ = _line(_bundle(captured), "torch.relu")
    assert f"{number}| " in prompt and "ANSWER-FIRST" in prompt


def _due_setup(captured):
    vault, config, store, diff = captured
    _generate(vault, config, store, ProjectFake())
    return vault, config, store, [p for p in store.probes_for_diff(diff["id"]) if p["selected"]]


def test_probes_are_sealed_until_due(captured):
    vault, config, store, selected = _due_setup(captured)
    probe = selected[0]
    assert probe["sealed_until"] == "2026-10-08T12:00:00Z"
    assert due_probes(store, clock=clock_at(6.9)) == []
    with pytest.raises(SealedProbeError) as raised:
        open_probe(store, probe["id"], clock=clock_at(6.9))
    assert probe["question"] not in str(raised.value)
    with pytest.raises(SealedProbeError):
        record_response(store, probe["id"], kind="answer", answer="relu", clock=clock_at(6.9))
    assert {p["id"] for p in due_probes(store, clock=clock_at(7))} == {p["id"] for p in selected}
    assert open_probe(store, probe["id"], clock=clock_at(7))["question"] == probe["question"]


def test_unselected_probes_are_never_served(captured):
    vault, config, store, selected = _due_setup(captured)
    unselected = [p for p in store.all_probes() if not p["selected"]][0]
    with pytest.raises(SealedProbeError):
        open_probe(store, unselected["id"], clock=clock_at(30))


def test_answers_grades_and_contest(captured):
    vault, config, store, selected = _due_setup(captured)
    first, second = selected
    response = record_response(store, first["id"], kind="answer", answer="It scales then applies relu.", clock=clock_at(9))
    assert response["declaration"] == "unassisted" and response["grade_status"] == "pending"
    assert response["lateness_seconds"] == 2 * 86400
    assert response["evidence_class"] == "practice" and response["exposure_isolation"] == "unknown"
    with pytest.raises(ProbeStateError):
        record_response(store, first["id"], kind="skip", clock=clock_at(9))
    fake = ProjectFake()
    paid = PaidCalls(store, caps=CAPS, run_id="grade")
    results = grade_responses(store, paid, _routes(fake)["grading"], clock=clock_at(9))
    assert results[0]["status"] == "graded" and results[0]["score"] == 0.9
    graded = store.response(response["id"])
    assert graded["grade_status"] == "graded" and graded["grader_prompt_version"]
    contested = contest_grade(store, response["id"], score=0.4, note="it missed the +1", clock=clock_at(10))
    assert contested["adjudicated_score"] == 0.4 and contested["score"] == 0.9
    rows = store.judgments(task="project_probe_grade", left_id=response["id"])
    assert [row["judge"] for row in rows] == ["llm", "owner"] and rows[1]["supersedes_id"] == rows[0]["id"]
    assert reveal(store, store.response(response["id"]))["score"] == 0.4
    unfair = record_response(store, second["id"], kind="unfair", declaration="looked", clock=clock_at(9))
    assert unfair["grade_status"] == "not_applicable"
    assert store.judgments(task="project_probe_unfair")[0]["left_id"] == second["id"]


def test_grade_failures_stay_pending_then_fail(captured):
    vault, config, store, selected = _due_setup(captured)
    response = record_response(store, selected[0]["id"], kind="answer", answer="scale", clock=clock_at(8))
    paid = PaidCalls(store, caps=CAPS, run_id="grade")
    route = _routes(ProjectFake(fail_grading=True))["grading"]
    for expected in ("pending", "pending", "failed"):
        grade_responses(store, paid, route, clock=clock_at(8))
        assert store.response(response["id"])["grade_status"] == expected
    with pytest.raises(ProbeStateError):
        contest_grade(store, response["id"], score=1.0, clock=clock_at(8))


def test_judgments_are_append_only(captured):
    vault, config, store, selected = _due_setup(captured)
    with pytest.raises(sqlite3.DatabaseError):
        with store.connection() as connection:
            connection.execute("UPDATE judgments SET verdict = 'x'")
    with pytest.raises(sqlite3.DatabaseError):
        with store.connection() as connection:
            connection.execute("DELETE FROM judgments")


def test_receipts_record_disclosure_and_estimated_only_cost(captured):
    vault, config, store, diff = captured
    _generate(vault, config, store, ProjectFake())
    receipts = store.receipts(diff_id=diff["id"])
    assert [row["purpose"] for row in receipts] == [
        "project_probe_authoring", "project_closed_book_check", "project_probe_grading",
    ]
    authoring = json.loads(receipts[0]["disclosure_json"])
    assert authoring["files_sent"] == ["model.py"] and authoring["context_scope"] == "diff"
    assert authoring["hunk_count"] == 1 and authoring["bytes_sent"] > 0
    closed_book = json.loads(receipts[1]["disclosure_json"])
    assert closed_book["files_sent"] == [] and closed_book["context_scope"] == "questions_only"
    assert all(row["cost_label"] == "estimated_only" for row in receipts)
    assert all(row["estimated_usd"] and row["estimated_usd"] > 0 for row in receipts)
    assert all(json.loads(row["budget_json"])["subscription"] is True for row in receipts)


def test_model_returning_extra_candidates_is_capped(captured):
    vault, config, store, diff = captured

    class Many(ProjectFake):
        def run_project_probe_authoring(self, context):
            base = super().run_project_probe_authoring(context)
            return ProbeCandidates(candidates=base.candidates * 3)

    _generate(vault, config, store, Many())
    assert len(store.probes_for_diff(diff["id"])) == config.project.candidates_per_diff


def test_a_concurrent_generation_run_is_refused_not_double_paid(captured):
    from learnloop.projects.probes import _exclusive

    vault, config, store, diff = captured
    fake = ProjectFake()
    with _exclusive(store.path.parent, "generate.lock") as held:
        assert held
        report = _generate(vault, config, store, fake)
    assert report.status == "busy" and fake.calls == {}
    assert _generate(vault, config, store, fake).status == "complete"


def test_errors_never_quote_model_output():
    from pydantic import ValidationError

    from learnloop.ai.errors import AIInvalidOutput, AIProviderUnavailable
    from learnloop.projects.probes import GenerationError, safe_error

    secret_question = "Q: why does forward clamp negatives?"
    try:
        ProbeCandidate.model_validate({"kind": "nope", "reference_answer": "r", "question": secret_question})
    except ValidationError as exc:
        assert secret_question not in safe_error(exc)
    assert secret_question not in safe_error(AIInvalidOutput(f"bad JSON: {secret_question}"))
    assert secret_question not in safe_error(RuntimeError(secret_question))
    assert "auth required" in safe_error(AIProviderUnavailable("auth required"))
    assert "no grade for q1" in safe_error(GenerationError("grader returned no grade for q1"))


def _why(bundle, citation, reference, *, agent_committed=True):
    candidate = ProbeCandidate(kind="why", reference_answer=reference, citations=[citation], question="q")
    return validate_candidate(candidate, bundle, agent_committed=agent_committed)


def test_a_rationale_flag_on_plain_code_is_not_a_stated_reason(captured):
    bundle = _bundle(captured)
    number, _ = _line(bundle, "y = y + 1")
    code = ProbeCitation(source="file", path="model.py", line_start=number, line_end=number, quote="y = y + 1", rationale=True)
    result = _why(bundle, code, "The increment avoids collisions with legacy database ids.")
    assert result.status == "why_uncited" and "code" in result.detail


def test_a_cited_comment_must_state_the_proposed_reason(captured):
    bundle = _bundle(captured)
    number, _ = _line(bundle, "Clamp negatives")
    comment = ProbeCitation(source="file", path="model.py", line_start=number, line_end=number,
                            quote="# Clamp negatives so the GRU never sees a sign flip.", rationale=True)
    assert _why(bundle, comment, "The increment avoids collisions with legacy database ids.").status == "why_uncited"
    supported = _why(bundle, comment, "So the GRU never sees a sign flip from negative values.")
    assert supported.status == "valid" and supported.rationale_label == "agent_stated"


def test_a_descriptive_commit_subject_is_not_a_reason(captured):
    bundle = _bundle(captured)
    subject = ProbeCitation(source="commit_message", quote="Clamp the forward pass with relu", rationale=True)
    assert _why(bundle, subject, "So negative activations never reach the GRU.").status == "why_uncited"
    body = ProbeCitation(source="commit_message", quote="Use relu so negative activations never reach the GRU.")
    stated = _why(bundle, body, "So negative activations never reach the GRU.")
    assert stated.status == "valid" and stated.rationale_label == "agent_stated"  # no flag needed: it is verified
    assert _why(bundle, body, "So negative activations never reach the GRU.", agent_committed=False).rationale_label == "cited"


def test_the_reason_check_is_persisted_in_the_verifier_judgment(captured):
    vault, config, store, diff = captured
    _generate(vault, config, store, ProjectFake())
    probes = {probe["question"].split(":")[0].strip(): probe for probe in store.probes_for_diff(diff["id"])}
    verdicts = {row["left_id"]: json.loads(row["rationale"]) for row in store.judgments(task="project_probe_validity")}
    cited = verdicts[probes["Q-why-cited"]["id"]]["rationale_check"]["citations"]
    assert cited[0]["states_reason"] is True and cited[0]["shared_terms"]
    uncited = verdicts[probes["Q-why-uncited"]["id"]]
    assert uncited["rationale_check"]["citations"][0]["states_reason"] is False
    assert verdicts[probes["Q-what"]["id"]]["rationale_check"] is None  # only why candidates need a reason


ADR = """# ADR 7: Cache compiled templates

## Context

Every page render parses its template.

## Decision

We cache compiled templates because parsing templates on every request increases latency.

```python
cache_templates(because="parsing templates on every request increases latency")
```
"""
ADR_REASON = "We cache compiled templates because parsing templates on every request increases latency."


@pytest.fixture
def adr_bundle(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    repo = TempRepo(tmp_path / "repo")
    repo.write("README.md", "Templates.\n")
    repo.commit("Initial", trailer=None)
    repo.write("docs/adr/0007-template-cache.md", ADR)
    repo.commit("Record the template cache decision")
    config = LearnLoopConfig()
    enroll_repo(vault, config, repo.path, clock=clock_at(0))
    sweep(vault, config, clock=clock_at(0))
    (diff,) = ProjectStore.for_vault(vault).diffs()
    return load_bundle(vault, diff["bundle_hash"])


def _adr_line(bundle, text):
    entry = next(entry for entry in bundle["files"] if entry["path"].endswith(".md"))
    excerpt = entry["excerpts"][0]
    number = excerpt["start_line"] + excerpt["lines"].index(text)
    return ProbeCitation(source="file", path=entry["path"], line_start=number, line_end=number, quote=text)


def test_a_plain_markdown_adr_paragraph_states_its_reason(adr_bundle):
    # P4 allows an ADR as a rationale span: prose in a prose document is not code.
    cited = _adr_line(adr_bundle, ADR_REASON)
    result = _why(adr_bundle, cited, ADR_REASON)
    assert result.status == "valid" and result.rationale_label == "agent_stated", result.detail
    in_diff = ProbeCitation(source="diff", path=cited.path, quote=ADR_REASON)
    assert _why(adr_bundle, in_diff, "Parsing templates on every request increases latency.").status == "valid"


def test_adr_prose_must_still_state_the_proposed_reason(adr_bundle):
    context = _adr_line(adr_bundle, "Every page render parses its template.")
    assert "states no reason" in _why(adr_bundle, context, ADR_REASON).detail
    other = _why(adr_bundle, _adr_line(adr_bundle, ADR_REASON), "To keep memory use under the container limit.")
    assert other.status == "why_uncited" and "does not state this reason" in other.detail
    wrong_line = _adr_line(adr_bundle, ADR_REASON).model_copy(update={"line_start": 1, "line_end": 1})
    assert _why(adr_bundle, wrong_line, ADR_REASON).status == "quote_mismatch"  # the citation is still verified


def test_a_fenced_code_block_in_an_adr_is_still_code(adr_bundle):
    code = 'cache_templates(because="parsing templates on every request increases latency")'
    for citation in (_adr_line(adr_bundle, code), ProbeCitation(source="diff", path=_adr_line(adr_bundle, code).path, quote=code)):
        result = _why(adr_bundle, citation, ADR_REASON)
        assert result.status == "why_uncited" and "code" in result.detail


@pytest.mark.parametrize("shape", ["empty", "missing_one", "duplicate", "unknown"])
def test_incomplete_closed_book_answers_never_pass_the_filter(captured, shape):
    from learnloop.projects.ai_contracts import ClosedBookAnswer, ClosedBookAnswers

    vault, config, store, diff = captured

    class Incomplete(ProjectFake):
        def run_project_closed_book_check(self, context):
            answers = super().run_project_closed_book_check(context).answers
            if shape == "empty":
                answers = []
            elif shape == "missing_one":
                answers = answers[1:]
            elif shape == "duplicate":
                answers = answers + [answers[0]]
            else:
                answers = answers[:-1] + [ClosedBookAnswer(id="q99", answer="x")]
            return ClosedBookAnswers(answers=answers)

    fake = Incomplete()
    report = _generate(vault, config, store, fake)
    assert report.status == "partial"
    statuses = {probe["status"] for probe in store.probes_for_diff(diff["id"])}
    assert statuses == {"invalid", "pending_closed_book"}  # nothing advanced to grading
    assert "grading" not in fake.calls
    assert store.diff(diff["id"])["probe_status"] == "pending"
    assert "closed-book" in store.diff(diff["id"])["generation_error"]
