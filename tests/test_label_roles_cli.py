"""RW4e: the owner-run batch role labeller (spec_reader_workbench_v1 §7.9; G44).

``learnloop reader label-roles --source <id> [--dry-run]``:

* ``--dry-run`` makes zero calls and zero writes and reports the batch plan
  (passages in reading order, each batch's estimated tokens and dollars), the
  route and its cost basis, and the cap with the batches it would stop;
* a real run sends one listwise call per batch, writes every judged passage's
  roles as proposals (judge ``role_labeller``), and checks
  ``roles.batch_max_cost_usd`` **before each batch call** (a batch that would
  pass it is never sent, nor any after it);
* solutions, held-out and exam material never reach the model, and a source
  held back whole is not labelled;
* a rerun resumes after the passages already labelled (no call for them);
* a missing or malformed roles field never fails a batch.
With no model reachable (the suite's ``LEARNLOOP_ROLE_LABELLER_MODELS=off``)
nothing is called or written. Fakes only.
"""
from __future__ import annotations

import hashlib
import json

import pytest
from typer.testing import CliRunner

from learnloop.ai.execution import report_call_usage
from learnloop.cli import app
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.source_retrieval import role_labeller as RL
from tests.passage_cue_fakes import build_cue_vault, loaded, set_config
from tests.pf_fakes import prompt_context


class RoleLabellerFake:
    """The batch labeller, deterministic: every passage gets ``roles``.
    ``provider_type``: ``codex_sdk`` bills the subscription, any other is
    metered; ``malformed``: the roles field is missing on every passage."""

    provider_name = "fake_role_labeller"
    model = "fake-role-labeller-model"

    def __init__(self, *, provider_type: str = "openrouter", roles=(("explanation", "medium"),),
                 malformed: bool = False) -> None:
        self.provider_type = provider_type
        self.roles = roles
        self.malformed = malformed
        self.prompts: list[str] = []
        self.contexts: list[dict] = []

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion", "isolated_turn"}

    def complete(self, request):
        assert request.result_model is RL.RoleLabellerResult
        self.prompts.append(request.prompt)
        report_call_usage({"input_tokens": len(request.prompt) // 4, "output_tokens": 60,
                           "resolved_model": self.model})
        context = prompt_context(request.prompt)
        self.contexts.append(context)
        judgments = []
        for candidate in context["candidates"]:
            judgment = {"ref": candidate["ref"], "verdict": "roles", "rationale": "plays a role"}
            if not self.malformed:
                judgment["roles"] = [{"role": role, "confidence": confidence} for role, confidence in self.roles]
            judgments.append(judgment)
        return RL.RoleLabellerResult.model_validate({"judgments": judgments, "picks": []})


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, spans = build_cue_vault(tmp_path / "vault")
    set_config(paths, "source_retrieval", llm_price_per_million=1.0)
    monkeypatch.setattr(RL, "BATCH_SIZE", 3)
    return paths, repository, spans


def _digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _counts(repository) -> dict[str, int]:
    tables = ("source_objects", "source_object_versions", "source_object_citations", "judgment_ledger",
              "model_call_receipts")
    with repository.connection() as connection:
        return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}


def _texts(repository, extraction_id: str, span_ids) -> list[str]:
    with repository.connection() as connection:
        return [str(row[0]) for row in connection.execute(
            f"SELECT text FROM source_document_blocks WHERE extraction_id = ? AND span_id IN "
            f"({','.join('?' for _ in span_ids)})", (extraction_id, *span_ids))]


def test_the_cli_dry_run_calls_and_writes_nothing_and_gives_the_plan_and_the_cap(library):
    paths, repository, spans = library
    repository.connection().close()
    before = _digest(paths.sqlite_path)
    result = CliRunner().invoke(app, ["reader", "label-roles", "--vault", str(paths.root), "--source", "src_text",
                                      "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out["status"] == "dry_run" and out["dry_run"] is True and out["calls"] == 0
    assert out["extraction_id"] == "ext_text" and out["source_id"] == "src_text"
    eligible = out["passages"]["eligible"]
    assert eligible >= 4 and out["passages"]["withheld"]["solution"] == len(spans["solutions"]) - 1
    assert out["passages"]["withheld"]["furniture_or_empty"] == len(spans)  # the section headers
    assert [batch["batch"] for batch in out["batches"]] == list(range(1, len(out["batches"]) + 1))
    assert sum(batch["passages"] for batch in out["batches"]) == eligible
    assert all(batch["estimated_tokens"] > 0 and batch["estimated_usd"] > 0 for batch in out["batches"])
    subscription = out["route"]["billing"] == "subscription"  # the vault's active provider
    assert out["caps"] == {"roles.batch_max_cost_usd": 5.0, "checked": "before each batch call", "batch_size": 3,
                           "subscription_exempt_from_dollar_cap": subscription}
    assert out["spend_plan"]["calls"] == len(out["batches"])
    assert out["spend_plan"]["cost_basis"] == ("estimated_only" if subscription else "metered_estimate")
    assert _digest(paths.sqlite_path) == before


def test_the_dry_run_names_the_batches_the_cap_would_stop(library):
    paths, repository, _spans = library
    metered = RoleLabellerFake()
    first = RL.label_roles(loaded(paths), repository, "ext_text", dry_run=True, client=metered)
    assert {batch["status"] for batch in first["batches"]} == {"planned"}
    assert first["caps"]["subscription_exempt_from_dollar_cap"] is False
    cost = first["batches"][0]["estimated_usd"]
    set_config(paths, "roles", batch_max_cost_usd=cost * 1.5)
    capped = RL.label_roles(loaded(paths), repository, "ext_text", dry_run=True, client=metered)
    assert [batch["status"] for batch in capped["batches"]] == ["planned"] + ["would_cap"] * (
        len(capped["batches"]) - 1)
    assert _counts(repository)["model_call_receipts"] == 0 and metered.prompts == []


def test_a_real_run_with_no_model_reachable_calls_and_writes_nothing(library):
    paths, repository, _spans = library
    before = _counts(repository)
    result = CliRunner().invoke(app, ["reader", "label-roles", "--vault", str(paths.root), "--source", "src_text",
                                      "--json"])
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    assert out["calls"] == 0 and out["status"] in ("unavailable", "skipped")
    assert _counts(repository) == before


def test_an_unknown_source_is_refused(library):
    paths, _repository, _spans = library
    result = CliRunner().invoke(app, ["reader", "label-roles", "--vault", str(paths.root), "--source", "nope",
                                      "--dry-run"])
    assert result.exit_code == 1 and json.loads(result.output)["status"] == "invalid"


def test_a_run_labels_every_batch_in_reading_order_as_proposals(library):
    paths, repository, spans = library
    plan = RL.label_roles(loaded(paths), repository, "ext_text", dry_run=True)
    fake = RoleLabellerFake(roles=(("explanation", "medium"), ("contrast", "low")))
    out = RL.label_roles(loaded(paths), repository, "ext_text", client=fake)
    assert out["status"] == "done" and out["calls"] == len(plan["batches"]) == len(fake.prompts)
    assert [batch["status"] for batch in out["batches"]] == ["judged"] * len(plan["batches"])
    sent = [candidate["passage"] for context in fake.contexts for candidate in context["candidates"]]
    assert len(sent) == plan["passages"]["eligible"]
    # Never a solution or a section header; in reading order.
    assert not set(sent) & set(_texts(repository, "ext_text", spans["solutions"]))
    with repository.connection() as connection:
        order = [str(row[0]) for row in connection.execute(
            "SELECT text FROM source_document_blocks WHERE extraction_id = 'ext_text' ORDER BY ordinal")]
    assert sent == [text for text in order if text in sent]
    with repository.connection() as connection:
        rows = [(row[0], json.loads(row[1])) for row in connection.execute(
            "SELECT authorial_role, content_json FROM source_object_versions")]
    assert len(rows) == 2 * len(sent) and out["proposals"]["written"] == len(rows)
    assert {content["judge"] for _role, content in rows} == {"role_labeller"}
    assert {content["prompt_version"] for _role, content in rows} == {RL.PROMPT_VERSION}
    assert {(role, content["confidence"]) for role, content in rows} == {("explanation", "medium"), ("contrast", "low")}
    assert out["usage"]["cost_basis"] == "metered_estimate" and out["usage"]["estimated_usd"] > 0


def test_the_cap_is_checked_before_each_batch_call(library):
    paths, repository, _spans = library
    fake = RoleLabellerFake()
    plan = RL.label_roles(loaded(paths), repository, "ext_text", dry_run=True, client=fake)
    assert len(plan["batches"]) >= 2
    set_config(paths, "roles", batch_max_cost_usd=plan["batches"][0]["estimated_usd"] * 1.5)
    out = RL.label_roles(loaded(paths), repository, "ext_text", client=fake)
    assert out["status"] == "capped" and len(fake.prompts) == 1 and out["calls"] == 1
    assert [batch["status"] for batch in out["batches"]] == ["judged"] + ["capped"] * (len(plan["batches"]) - 1)
    assert out["batches"][1]["reason"].startswith("roles.batch_max_cost_usd")
    assert _counts(repository)["model_call_receipts"] == 1


def test_a_zero_cap_sends_nothing(library):
    paths, repository, _spans = library
    set_config(paths, "roles", batch_max_cost_usd=0.0)
    before = _counts(repository)
    fake = RoleLabellerFake()
    out = RL.label_roles(loaded(paths), repository, "ext_text", client=fake)
    assert out["status"] == "capped" and fake.prompts == [] and out["calls"] == 0
    assert {batch["status"] for batch in out["batches"]} == {"capped"}
    assert _counts(repository) == before


def test_a_subscription_route_is_estimated_only_and_never_refused_for_money(library):
    paths, repository, _spans = library
    set_config(paths, "roles", batch_max_cost_usd=0.0)
    fake = RoleLabellerFake(provider_type="codex_sdk")
    plan = RL.label_roles(loaded(paths), repository, "ext_text", dry_run=True, client=fake)
    assert plan["caps"]["subscription_exempt_from_dollar_cap"] is True
    assert plan["spend_plan"]["cost_basis"] == "estimated_only"
    out = RL.label_roles(loaded(paths), repository, "ext_text", client=fake)
    assert out["status"] == "done" and len(fake.prompts) == len(plan["batches"])
    assert out["usage"]["cost_basis"] == "estimated_only"


def test_a_rerun_resumes_after_the_passages_already_labelled(library):
    paths, repository, _spans = library
    fake = RoleLabellerFake()
    RL.label_roles(loaded(paths), repository, "ext_text", client=fake)
    before = _counts(repository)
    again = RoleLabellerFake()
    out = RL.label_roles(loaded(paths), repository, "ext_text", client=again)
    assert again.prompts == [] and out["calls"] == 0 and out["passages"]["eligible"] == 0
    assert out["passages"]["already_labelled"] == sum(len(c["candidates"]) for c in fake.contexts)
    assert _counts(repository) == before


def test_a_missing_roles_field_never_fails_a_batch(library):
    paths, repository, _spans = library
    fake = RoleLabellerFake(malformed=True)
    out = RL.label_roles(loaded(paths), repository, "ext_text", client=fake)
    assert out["status"] == "done" and {batch["status"] for batch in out["batches"]} == {"judged"}
    assert out["proposals"]["written"] == 0
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = 'instructional_roles'"
                                  ).fetchone()[0] == sum(len(c["candidates"]) for c in fake.contexts)


def test_held_out_and_exam_material_never_reach_the_labeller(library):
    paths, repository, spans = library
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"ch5": "held_out_evaluation"})
    fake = RoleLabellerFake(provider_type="codex_sdk")
    out = RL.label_roles(loaded(paths), repository, "ext_text", client=fake)
    sent = [candidate["passage"] for context in fake.contexts for candidate in context["candidates"]]
    assert not set(sent) & set(_texts(repository, "ext_text", spans["ch5"]))
    assert out["passages"]["withheld"].get("held_out", 0) + out["passages"]["withheld"].get("assessment_lane", 0) >= 2
    with repository.connection() as connection:
        cited = {row[0] for row in connection.execute("SELECT span_id FROM source_object_citations")}
    assert not cited & set(spans["ch5"])
    exam = RL.label_roles(loaded(paths), repository, "ext_exam", client=RoleLabellerFake(provider_type="codex_sdk"))
    assert exam["status"] == "withheld" and exam["calls"] == 0
