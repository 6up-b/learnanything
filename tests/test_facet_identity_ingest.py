"""Facet identity at mint time: within-run consolidation, attach (D2), undo, kill switch.

Bootstrap synthesis end to end with the house fake synthesis client and a
fake judge. A duplicate candidate is not minted: its references keep its id
(an alias of the survivor), so the one-tap undo re-mints it exactly.
"""

from __future__ import annotations

import sqlite3

from learnloop.content.facet_identity.actions import list_actions, undo_action
from learnloop.content.facet_identity.judge import TASK
from learnloop.content.synthesis.ai_contracts import (
    SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION,
    SOURCE_SET_SYNTHESIS_PROMPT_VERSION,
    SynthCriterion,
    SynthCriterionTarget,
    SynthFacet,
    SynthPracticeItem,
    SynthRecipeComponent,
    source_set_synthesis_prompt,
)
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.models import learning_object_facet_union
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml

from tests.facet_identity_fakes import FakeFacetJudge
from tests.helpers import append_config_toml, write_facets
from tests.test_source_set_synthesis import _CLOCK, FakeSynthesisClient, _default_payload, _setup

DEF_CLAIM = "A real square matrix is symmetric exactly when A^T = A."
DUP_ID = "facet_symmetry_definition_restated"
DUP_CLAIM = "A real square matrix A is symmetric if and only if it equals its transpose."


def _with_duplicate(context, _ordinal):
    payload = _default_payload(context)
    prov = payload.facets[0].provenance
    payload.facets.append(SynthFacet(
        client_item_id="f_def_dup", id=DUP_ID, concept_client_id="c_sym", kind="definition",
        claim=DUP_CLAIM, preconditions=["the matrix is square"], positive_examples=["[[1,2],[2,1]]"],
        error_signatures=["checks only the diagonal"], instructional_repairs=["compare entries across the diagonal"],
        provenance=prov,
    ))
    payload.blueprints[0].recipes[0].all_of.append(
        SynthRecipeComponent(facet_client_id="f_def_dup", capability="retrieval"))
    payload.practice_items.append(SynthPracticeItem(
        client_item_id="pi_3", id="pi_transpose_check", learning_object_client_id="lo_diag",
        practice_mode="retrieval", prompt="When does A equal its transpose?", expected_answer="When a_ij = a_ji.",
        evidence_facet_client_ids=["f_def_dup"],
        criteria=[SynthCriterion(
            id="states_transpose_condition", points=1.0, description="States a_ij = a_ji.",
            correlation_group="transpose_condition",
            targets=[SynthCriterionTarget(facet_client_id="f_def_dup", capability="retrieval", role="primary")],
        )],
        provenance=prov,
    ))
    return payload


class _RecordingSynthesisClient(FakeSynthesisClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prompts: list[str] = []

    def complete(self, request):
        if request.purpose == "source_set_synthesis":
            self.prompts.append(request.prompt)
        return super().complete(request)


def _ledger(sqlite_path):
    return sqlite3.connect(sqlite_path).execute(
        "SELECT left_kind, verdict, judge, judge_model FROM judgment_ledger WHERE task = ?", (TASK,)
    ).fetchall()


def test_a_duplicate_candidate_is_merged_before_the_gates_and_undo_re_mints_it(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]])
    client = _RecordingSynthesisClient(builder=_with_duplicate)
    result = create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK, apply=True,
                              facet_identity_client=judge)
    assert result.applied
    block = result.facet_identity
    assert block["status"] == "judged" and block["in_run_retired"] == 1
    (action,) = block["actions"]
    assert action["action"] == "merge" and action["scope"] == "in_run" and action["status"] == "applied"
    assert action["survivor"]["id"] == "facet_symmetry_definition"
    assert [facet["id"] for facet in action["retired"]] == [DUP_ID]
    assert action["undoable"]
    # The prompt carried the one-facet-per-skill rule under the bumped version.
    assert "ONE FACET PER TESTABLE SKILL" in client.prompts[0]
    assert SOURCE_SET_SYNTHESIS_FACET_IDENTITY_PROMPT_VERSION in client.prompts[0]

    vault = load_vault(root)
    assert DUP_ID not in vault.evidence_facets
    survivor = vault.evidence_facets["facet_symmetry_definition"]
    assert DUP_ID in survivor.aliases
    assert "the matrix is square" in survivor.preconditions
    assert "[[1,2],[2,1]]" in survivor.positive_examples
    # References keep the candidate's id on disk; the loader resolves the alias.
    paths = VaultPaths(vault.root, vault.config)
    item_yaml = read_yaml(paths.practice_item_path("linear-algebra", "pi_transpose_check"))
    assert item_yaml["evidence_facets"] == [DUP_ID]
    assert vault.practice_items["pi_transpose_check"].evidence_facets == ["facet_symmetry_definition"]
    assert vault.practice_items["pi_transpose_check"].grading_rubric.criteria[0].targets[0].facet == "facet_symmetry_definition"
    assert set(learning_object_facet_union(vault.learning_objects["lo_diagonalize_symmetric"])) == {
        "facet_symmetry_definition", "facet_spectral_applicability"}
    # The merged pair of the three c_sym candidates is ledgered; the two
    # kept-apart pairs were never shortlisted (no lexical near-duplicate, no
    # embeddings), so they write no row (owner decision 2026-10-12).
    rows = _ledger(repo.sqlite_path)
    assert len(rows) == 1 and {row[0] for row in rows} == {"facet_candidate"}
    assert [row[1] for row in rows] == ["same"]

    undone = undo_action(root, repo, action["id"], clock=_CLOCK)
    assert undone["restored_facet_ids"] == [DUP_ID]
    vault = load_vault(root)
    assert DUP_ID in vault.evidence_facets
    assert DUP_ID not in vault.evidence_facets["facet_symmetry_definition"].aliases
    assert vault.evidence_facets[DUP_ID].claim == DUP_CLAIM
    assert "the matrix is square" not in vault.evidence_facets["facet_symmetry_definition"].preconditions
    assert vault.practice_items["pi_transpose_check"].evidence_facets == [DUP_ID]
    assert set(learning_object_facet_union(vault.learning_objects["lo_diagonalize_symmetric"])) == {
        "facet_symmetry_definition", "facet_spectral_applicability", DUP_ID}


def test_an_unapplied_proposal_records_the_merge_without_an_undo(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]])
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_duplicate), repository=repo,
                              clock=_CLOCK, facet_identity_client=judge)
    (action,) = result.facet_identity["actions"]
    assert action["status"] == "proposed" and not action["undoable"]
    proposal_facets = [row for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    assert sorted(row["payload"]["id"] for row in proposal_facets) == [
        "facet_spectral_applicability", "facet_symmetry_definition"]
    try:
        undo_action(root, repo, action["id"])
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "code", "") == "not_applied"
    else:  # pragma: no cover
        raise AssertionError("undo of an unapplied merge must refuse")


def test_a_candidate_matching_a_registered_facet_becomes_its_alias(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    paths = VaultPaths(root, load_vault(root).config)
    write_facets(paths, [{
        "id": "facet_symmetric_matrix_definition", "kind": "definition", "claim": DEF_CLAIM,
        "concept_id": None, "status": "reviewed",
    }])
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM]], key=lambda view: str(view.get("claim") or ""))
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK,
                              apply=True, facet_identity_client=judge)
    block = result.facet_identity
    assert block["attached"] == 1, block
    (action,) = block["actions"]
    assert action["scope"] == "attach" and action["survivor"]["id"] == "facet_symmetric_matrix_definition"
    vault = load_vault(root)
    assert "facet_symmetry_definition" not in vault.evidence_facets
    assert "facet_symmetry_definition" in vault.evidence_facets["facet_symmetric_matrix_definition"].aliases
    assert vault.practice_items["pi_identify_symmetry"].evidence_facets == ["facet_symmetric_matrix_definition"]
    undo_action(root, repo, action["id"], clock=_CLOCK)
    vault = load_vault(root)
    assert "facet_symmetry_definition" in vault.evidence_facets
    assert vault.evidence_facets["facet_symmetric_matrix_definition"].aliases == []
    assert vault.practice_items["pi_identify_symmetry"].evidence_facets == ["facet_symmetry_definition"]


def test_the_kill_switch_restores_the_prompt_and_never_calls_the_judge(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    append_config_toml(root, "[facet_identity]\nenabled = false")
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]])
    client = _RecordingSynthesisClient(builder=_with_duplicate)
    result = create_study_map(root, "set_la", client=client, repository=repo, clock=_CLOCK, apply=True,
                              facet_identity_client=judge)
    assert result.facet_identity is None and judge.requests == []
    assert "ONE FACET PER TESTABLE SKILL" not in client.prompts[0]
    assert SOURCE_SET_SYNTHESIS_PROMPT_VERSION in client.prompts[0]
    assert source_set_synthesis_prompt(client.calls[0]) == client.prompts[0]
    assert DUP_ID in load_vault(root).evidence_facets
    assert _ledger(repo.sqlite_path) == [] and list_actions(repo) == []


def test_an_unavailable_judge_keeps_the_candidates_and_says_so(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_duplicate),
                              repository=repo, clock=_CLOCK, apply=True)
    assert result.facet_identity["status"] == "judge_unavailable"
    assert result.facet_identity["actions"] == []
    assert DUP_ID in load_vault(root).evidence_facets


def test_revalidation_replays_the_plan_without_a_judge_call(tmp_path, monkeypatch):
    import learnloop.content.synthesis.source_set_synthesis as synthesis
    from learnloop.content.synthesis.source_set_synthesis import revalidate_synthesis_candidate

    root, repo = _setup(tmp_path, with_exam=False)
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]])
    real = synthesis.run_synthesis_gates

    def failing_once(proposal, ctx):
        monkeypatch.setattr(synthesis, "run_synthesis_gates", real)
        report = real(proposal, ctx)
        from learnloop.content.synthesis.synthesis_gates import GateDiagnostic

        report.diagnostics.append(GateDiagnostic(gate="test", severity="hard_fail", entity_refs=(),
                                                 message="forced", suggested_action="retry"))
        return report

    monkeypatch.setattr(synthesis, "run_synthesis_gates", failing_once)
    try:
        create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_duplicate), repository=repo,
                         clock=_CLOCK, facet_identity_client=judge)
    except synthesis.StudyMapError as exc:
        run_id = exc.synthesis_run_id
    else:  # pragma: no cover
        raise AssertionError("the forced gate failure must fail the run")
    calls = len(judge.requests)
    result = revalidate_synthesis_candidate(root, run_id, repository=Repository(repo.sqlite_path), clock=_CLOCK)
    assert len(judge.requests) == calls
    facets = [row["payload"]["id"] for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    assert DUP_ID not in facets
    assert result.facet_identity["in_run_retired"] == 1


def test_the_desktop_lists_a_runs_merges_and_undoes_one(tmp_path):
    import io
    import json

    from learnloop_sidecar.server import serve

    root, repo = _setup(tmp_path, with_exam=False)
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_duplicate), repository=repo,
                              clock=_CLOCK, apply=True,
                              facet_identity_client=FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]]))
    action_id = result.facet_identity["actions"][0]["id"]
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"vaultPath": str(root)}},
        {"jsonrpc": "2.0", "id": 2, "method": "list_facet_identity_actions",
         "params": {"runId": result.synthesis_run_id}},
        {"jsonrpc": "2.0", "id": 3, "method": "undo_facet_identity_action", "params": {"actionId": action_id}},
        {"jsonrpc": "2.0", "id": 4, "method": "undo_facet_identity_action", "params": {"actionId": action_id}},
    ]
    stdout = io.StringIO()
    serve(io.StringIO("".join(json.dumps(m) + "\n" for m in messages)), stdout)
    replies = {reply["id"]: reply for reply in map(json.loads, stdout.getvalue().splitlines()) if "id" in reply}
    assert "undo_facet_identity_action" in replies[1]["result"]["capabilities"]["methods"]
    listed = replies[2]["result"]["actions"]
    assert [entry["id"] for entry in listed] == [action_id] and listed[0]["undoable"] is True
    assert replies[3]["result"]["status"] == "undone"
    assert replies[3]["result"]["action"]["status"] == "undone"
    assert replies[4]["error"]["data"]["code"] == "already_undone"


def test_append_attaches_a_new_facet_to_the_registered_one_it_restates(tmp_path):
    from learnloop.content.proposals.patches import apply_accepted_items
    from learnloop.content.synthesis.ai_contracts import AppendReconciliation, SynthSpanRef
    from learnloop.content.synthesis.source_append import append_source

    from tests.test_source_append import FakeAppendClient, _bootstrap_and_add, _first_new_span

    root, repo = _bootstrap_and_add(tmp_path)
    # The bootstrap's probe episodes used to lock the registered facet; facet
    # locks were removed (owner, 2026-10-12), so its examples grow.
    restated = "Symmetry of a real square matrix means it coincides with its transpose."

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="primary", role="primary_textbook")
        # Embeddings are off: the registered facets of the candidate's own
        # (registered) concept are its neighbourhood.
        return AppendReconciliation(
            summary="restated definition",
            facets=[SynthFacet(client_item_id="f_new", id="facet_symmetry_restated",
                               concept_id="concept_symmetric_matrix", kind="definition", claim=restated,
                               positive_examples=["I is symmetric"], provenance=[ref])],
        )

    # The judge calls the restatement a worked instance of the registered
    # definition: absorb it as an example (an append-legal, growth-only update).
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, restated]], action="absorb")
    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, facet_identity_client=judge)
    block = result.facet_identity
    assert block["attached"] == 1 and len(judge.requests) == 1
    assert judge.requests[0]["context"]["mode"] == "attach"
    (action,) = block["actions"]
    assert action["scope"] == "attach" and action["origin"] == "append" and action["status"] == "proposed"
    assert action["action"] == "absorb"
    facet_rows = [row for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    assert [(row["operation"], row["payload"]["id"]) for row in facet_rows] == [("update", "facet_symmetry_definition")]
    assert "facet_symmetry_restated" in facet_rows[0]["payload"]["aliases"]
    # The facet's content is the alias and the example; ``meaning_support`` is the
    # proposal's record of the citation the example rests on, judged again at apply.
    assert set(facet_rows[0]["payload"]) == {"id", "aliases", "positive_examples", "meaning_support"}
    assert facet_rows[0]["payload"]["meaning_support"][0]["citations"][0]["extraction_id"] == "ext_alt"
    assert facet_rows[0]["payload"]["positive_examples"][-1] == restated
    apply_accepted_items(root, result.proposal_id, item_ids=[row["id"] for row in repo.proposal_items(result.proposal_id)
                                                             if row["item_type"] in {"facet", "concept"}], clock=_CLOCK)
    vault = load_vault(root)
    assert vault.canonical_facet_id("facet_symmetry_restated") == "facet_symmetry_definition"
    undo_action(root, repo, action["id"], clock=_CLOCK)
    vault = load_vault(root)
    assert vault.evidence_facets["facet_symmetry_restated"].claim == restated
    assert "facet_symmetry_restated" not in vault.evidence_facets["facet_symmetry_definition"].aliases
    assert restated not in vault.evidence_facets["facet_symmetry_definition"].positive_examples


# --- review F2: attach never adds a precondition (facet locks are gone) ----------


def _attach_absorb(tmp_path, *, absorb_as, strict=False):
    from learnloop.content.synthesis.ai_contracts import AppendReconciliation, SynthSpanRef
    from learnloop.content.synthesis.source_append import append_source

    from tests.test_source_append import FakeAppendClient, _bootstrap_and_add, _first_new_span

    root, repo = _bootstrap_and_add(tmp_path)
    if strict:
        # Review F2's strict lock policy: a retired key nothing reads any more.
        append_config_toml(root, "[facet_identity]\nmerge_locked_facets = false")
    restated = "Symmetry of a real square matrix means it coincides with its transpose."

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="primary", role="primary_textbook")
        return AppendReconciliation(
            summary="restated definition",
            facets=[SynthFacet(client_item_id="f_new", id="facet_symmetry_restated",
                               concept_id="concept_symmetric_matrix", kind="definition", claim=restated,
                               provenance=[ref])],
        )

    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, restated]], action="absorb")
    if absorb_as == "precondition":
        original = judge.complete

        def as_precondition(request):
            verdict = original(request)
            for decided in verdict.sets:
                decided.absorb_as = "precondition"
            return verdict

        judge.complete = as_precondition  # type: ignore[method-assign]
    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, facet_identity_client=judge)
    return root, repo, result, restated


def test_an_absorbed_precondition_never_grows_a_registered_facet(tmp_path):
    root, repo, result, restated = _attach_absorb(tmp_path, absorb_as="precondition")
    (action,) = result.facet_identity["actions"]
    assert action["action"] == "absorb" and "precondition" in (action["contract_note"] or "")
    facet_rows = [row for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    assert set(facet_rows[0]["payload"]) == {"id", "aliases"}  # alias only: append-legal
    assert "facet_symmetry_restated" in facet_rows[0]["payload"]["aliases"]


def test_the_retired_strict_lock_policy_no_longer_keeps_an_absorbed_example_out(tmp_path):
    """Review F2's strict policy kept a locked facet's examples unchanged; the
    key is retired, so an absorbed example grows the registered facet."""

    root, repo, result, restated = _attach_absorb(tmp_path, absorb_as="example", strict=True)
    (action,) = result.facet_identity["actions"]
    assert not action.get("contract_note")
    facet_rows = [row for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    assert set(facet_rows[0]["payload"]) == {"id", "aliases", "positive_examples", "meaning_support"}
    assert facet_rows[0]["payload"]["positive_examples"][-1] == restated


def test_the_alias_only_append_gate_refuses_a_precondition_growth():
    from types import SimpleNamespace

    from learnloop.content.synthesis.synthesis_gates import GateItem, _is_alias_only_facet_append

    facet = SimpleNamespace(aliases=[], positive_examples=["e1"], preconditions=["p1"])
    ctx = SimpleNamespace(vault=SimpleNamespace(evidence_facets={"f": facet}))

    def item(payload):
        return GateItem(client_item_id="c", item_type="facet", operation="update", entity_id="f",
                        payload={"id": "f", "aliases": ["g"], **payload})

    assert _is_alias_only_facet_append(item({}), ctx)
    assert _is_alias_only_facet_append(item({"positive_examples": ["e1", "e2"]}), ctx)
    assert not _is_alias_only_facet_append(item({"preconditions": ["p1", "p2"]}), ctx)
    assert not _is_alias_only_facet_append(item({"positive_examples": ["e2"]}), ctx)


# --- review F7: two judged sets on one in-run survivor undo as one -------------------

DUP2_ID = "facet_symmetry_definition_third"
DUP2_CLAIM = "Symmetric matrices are exactly the square matrices equal to their own transposes."


def _with_two_duplicates(context, ordinal):
    payload = _with_duplicate(context, ordinal)
    prov = payload.facets[0].provenance
    payload.facets.append(SynthFacet(
        client_item_id="f_def_dup2", id=DUP2_ID, concept_client_id="c_sym", kind="definition",
        claim=DUP2_CLAIM, positive_examples=["the identity matrix"], provenance=prov,
    ))
    payload.blueprints[0].recipes[0].all_of.append(
        SynthRecipeComponent(facet_client_id="f_def_dup2", capability="retrieval"))
    return payload


def test_two_sets_on_one_in_run_survivor_are_one_action_that_undoes_both(tmp_path, monkeypatch):
    import learnloop.content.facet_identity.plan as plan_module

    real = plan_module.build_plan

    def second_group(*args, **kwargs):
        # The attach phase can put a surviving candidate into a set with no
        # registered facet: scope in_run, the same survivor, another group.
        plan = real(*args, **kwargs)
        for key, retirement in plan.retirements.items():
            if key.endswith("f_def_dup2"):
                retirement.group_id = "attach-phase-group"
                retirement.action, retirement.absorb_as = "absorb", "example"
        return plan

    monkeypatch.setattr(plan_module, "build_plan", second_group)
    root, repo = _setup(tmp_path, with_exam=False)
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM, DUP2_CLAIM]])
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_two_duplicates),
                              repository=repo, clock=_CLOCK, apply=True, facet_identity_client=judge)
    assert result.facet_identity["in_run_retired"] == 2
    (action,) = result.facet_identity["actions"]
    assert sorted(facet["id"] for facet in action["retired"]) == sorted([DUP_ID, DUP2_ID])
    assert action["undoable"]
    vault = load_vault(root)
    survivor = vault.evidence_facets["facet_symmetry_definition"]
    assert {DUP_ID, DUP2_ID} <= set(survivor.aliases) and DUP2_CLAIM in survivor.positive_examples

    undo_action(root, repo, action["id"], clock=_CLOCK)
    vault = load_vault(root)
    assert {DUP_ID, DUP2_ID} <= set(vault.evidence_facets)
    survivor = vault.evidence_facets["facet_symmetry_definition"]
    assert survivor.aliases == [] and DUP2_CLAIM not in survivor.positive_examples
    assert "the matrix is square" not in survivor.preconditions
    assert vault.evidence_facets[DUP2_ID].claim == DUP2_CLAIM


# --- review F5: every dry run names the judge's route and caps, and changes nothing --------


def test_the_synthesize_dry_run_plans_the_ingest_judge(tmp_path, monkeypatch):
    import learnloop.cli as cli_module
    from typer.testing import CliRunner

    from learnloop.cli import app
    from learnloop.content.synthesis.source_set_synthesis import plan_study_map_embedding

    root, _repo = _setup(tmp_path, with_exam=False)
    judge = plan_study_map_embedding(root, "set_la")["facet_identity"]
    assert judge["enabled"] and judge["status"] == "may_judge"
    assert judge["max_calls"] == 24 and judge["route"]["route"] == "facet_identity_judge"
    assert judge["caps"]["max_calls"] == 24

    monkeypatch.setattr(cli_module, "_ready_provider_for_task",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("dry run resolved a provider")))
    text = CliRunner().invoke(app, ["synthesize", "set_la", "--dry-run", "--mode", "bootstrap", "--vault", str(root)])
    assert text.exit_code == 0, text.output
    assert "facet-identity judge:" in text.output and "up to 24" in text.output

    append_config_toml(root, "[facet_identity]\nenabled = false")
    assert plan_study_map_embedding(root, "set_la")["facet_identity"] == {
        "enabled": False, "status": "off", "max_calls": 0, "max_estimated_usd": 0.0}


def test_the_append_dry_run_plans_the_ingest_judge(tmp_path):
    from learnloop.content.synthesis.source_append import plan_append_embedding

    from tests.test_source_append import _bootstrap_and_add

    root, _repo = _bootstrap_and_add(tmp_path)
    config = root / "learnloop.toml"
    config.write_text(config.read_text(encoding="utf-8").replace(
        "[ai.routing]\n", '[ai.routing]\nfacet_identity_judge = "openrouter_haiku"\n', 1), encoding="utf-8")
    judge = plan_append_embedding(root, "set_la", new_revision_ids=["rev_alt"])["facet_identity"]
    assert judge["billing"] == "metered" and judge["max_estimated_usd"] == 0.5
    assert judge["route"]["model"] == "anthropic/claude-haiku-5.5"


def test_the_dedupe_dry_run_never_migrates_the_database(tmp_path, monkeypatch):
    import learnloop.db.repositories as repositories
    from learnloop.content.facet_identity.dedupe import run_dedupe

    from tests.test_facet_identity import _regression_vault, _study_judge

    root, repository, data = _regression_vault(tmp_path / "vault")

    def no_migration(*_args, **_kwargs):
        raise AssertionError("a dry run applied migrations")

    monkeypatch.setattr(repositories, "create_or_attach_current", no_migration)
    report = run_dedupe(root, dry_run=True, client=_study_judge(data))
    assert report["status"] == "dry_run" and report["estimate"]["calls"] == 1


# --- review F10: the kill switch also stops a stored plan from replaying ------------------


def test_revalidation_with_the_switch_off_replays_no_stored_plan(tmp_path, monkeypatch):
    import learnloop.content.synthesis.source_set_synthesis as synthesis
    from learnloop.content.synthesis.source_set_synthesis import revalidate_synthesis_candidate
    from learnloop.content.synthesis.synthesis_gates import GateDiagnostic

    root, repo = _setup(tmp_path, with_exam=False)
    real = synthesis.run_synthesis_gates

    def failing_once(proposal, ctx):
        monkeypatch.setattr(synthesis, "run_synthesis_gates", real)
        report = real(proposal, ctx)
        report.diagnostics.append(GateDiagnostic(gate="test", severity="hard_fail", entity_refs=(),
                                                 message="forced", suggested_action="retry"))
        return report

    monkeypatch.setattr(synthesis, "run_synthesis_gates", failing_once)
    try:
        create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_duplicate), repository=repo,
                         clock=_CLOCK, facet_identity_client=FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]]))
    except synthesis.StudyMapError as exc:
        run_id = exc.synthesis_run_id
    else:  # pragma: no cover
        raise AssertionError("the forced gate failure must fail the run")
    append_config_toml(root, "[facet_identity]\nenabled = false")
    result = revalidate_synthesis_candidate(root, run_id, repository=Repository(repo.sqlite_path), clock=_CLOCK)
    facets = [row["payload"]["id"] for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    assert DUP_ID in facets  # minted, as with no facet identity at all
    assert result.facet_identity is None and list_actions(repo) == []


def test_the_gate_knows_aliases_only_while_facet_identity_is_on():
    from types import SimpleNamespace

    from learnloop.content.synthesis.synthesis_gates import GateItem, GateProposal, _known_facet_references

    def ctx(enabled):
        config = SimpleNamespace(facet_identity=SimpleNamespace(enabled=enabled))
        vault = SimpleNamespace(config=config, facet_aliases={"facet_old_name": "facet_a"})
        return SimpleNamespace(registered_facet_ids={"facet_a"}, vault=vault)

    proposal = GateProposal(items=[GateItem(client_item_id="c", item_type="facet", entity_id="facet_b",
                                            payload={"id": "facet_b", "aliases": ["cand_b2"]})])
    assert {"facet_old_name", "cand_b2"} <= _known_facet_references(proposal, ctx(True))
    assert _known_facet_references(proposal, ctx(False)) == {"facet_a", "facet_b"}


# --- review F6/F9: what the desktop needs to show live, accurate state --------------------


def test_the_run_summary_names_its_run_and_each_action_its_evidence_and_undo_limits(tmp_path):
    from learnloop.content.facet_identity.actions import describe

    root, repo = _setup(tmp_path, with_exam=False)
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_duplicate), repository=repo,
                              clock=_CLOCK, apply=True,
                              facet_identity_client=FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]]))
    block = result.facet_identity
    assert block["run_id"] == result.synthesis_run_id
    (action,) = block["actions"]
    assert "stay with it" in action["undo_limits"] and action["evidenced_facets"] == []
    assert "locked" not in action and "lock_sources" not in action
    record = dict(list_actions(repo)[0])
    record["detail"] = {**record["detail"], "evidence": {"facet_x": {"surface_groups": 2, "independent_mass": 1.0}}}
    assert describe(record, load_vault(root))["evidenced_facets"] == ["facet_x"]
    # A row written before locks were removed keeps its lock reasons on disk; none show.
    record["detail"] = {"lock_reasons": {"facet_x": [{"source": "probe", "detail": "probe"}]}}
    assert describe(record, load_vault(root))["evidenced_facets"] == []
    undone = undo_action(root, repo, action["id"], clock=_CLOCK)
    assert "stay with it" in undone["not_restored"]
