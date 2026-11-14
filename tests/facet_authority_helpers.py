"""What other test files use from ``tests/test_facet_authority.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import ast
import json
from datetime import UTC, datetime
from pathlib import Path

import learnloop
from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.content.facet_identity.plan import FacetIdentityPlan, Retirement
from learnloop.content.synthesis.ai_contracts import (
    SourceSetSynthesis,
    SynthConcept,
    SynthFacet,
    SynthSpanRef,
)
from learnloop.content.synthesis.normalize import normalize
from learnloop.content.synthesis.source_set_synthesis import _collect_inputs, _gate_context
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
from learnloop.content.synthesis.synthesis_gates import GateProposal, run_synthesis_gates
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_source_set

from tests.source_append_helpers import SymmetryInventoryClient
from tests.source_inventory_helpers import _block, _ir, _persist, _register_revision
from tests.source_set_synthesis_helpers import _setup


_CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))
NOW = "2026-10-13T12:00:00Z"
SUBJECT = "linear-algebra"
EXAM_CLAIM = "On the final, a matrix counts as symmetric only when every diagonal entry is positive."
EXAM_CONDITION = "EXAM-ONLY condition: every diagonal entry is positive"
NEW_CLAIM = "A real square matrix A is symmetric exactly when it equals its transpose: A^T = A."
#: The held-out exam paper of ``_setup(with_exam=True)``.
EXAM_SPAN = {"extraction_id": "ext_exam", "unit_id": "paper_2024", "span_id": "s1"}


def _add_member(repo, root, *, source_id, revision_id, extraction_id, units, role, scope):
    """Register a source revision with ``units`` = [(unit_id, [(span_id, text)])] and add it to set_la."""

    _register_revision(repo, source_id=source_id, revision_id=revision_id)
    ir = _ir([
        (unit_id, unit_id.replace("_", " "), [_block(span_id, text) for span_id, text in blocks],
         f"sha256:{unit_id}", index + 3)
        for index, (unit_id, blocks) in enumerate(units)
    ])
    _persist(repo, ir, revision_id=revision_id, extraction_id=extraction_id)
    for entry in scope:
        run_unit_inventory(repo, extraction_id, entry["unit_id"], role=entry.get("role_override") or role,
                           profile="combined", client=SymmetryInventoryClient(), input_budget_tokens=20000,
                           clock=_CLOCK)
    vault = load_vault(root)
    current = next(source_set for source_set in vault.source_sets if source_set.id == "set_la")
    members = [member.model_dump(mode="json", exclude_none=True) for member in current.members]
    # The scope names the reading its unit ids were chosen on (exam
    # protection by extraction identity).
    members.append({"source_id": source_id, "revision_id": revision_id, "default_role": role,
                    "scope": scope, "priority": 1, "scope_extraction_id": extraction_id,
                    "scope_revision_id": revision_id})
    upsert_source_set(root, {"id": "set_la", "subject_id": SUBJECT, "title": "Linear Algebra",
                             "members": members}, clock=_CLOCK)


def _add_two_units(repo, root):
    """An explanatory source with one selected unit and one the owner left out."""

    _add_member(repo, root, source_id="src_two", revision_id="rev_two", extraction_id="ext_two",
                units=[("two_selected", [("s1", "Symmetric matrices have real eigenvalues.")]),
                       ("two_outside", [("s2", "A matrix is symmetric when its diagonal is positive.")])],
                role="alternate_explanation", scope=[{"unit_id": "two_selected"}])


def _source_set(root):
    return next(source_set for source_set in load_vault(root).source_sets if source_set.id == "set_la")


def _facet_proposal(repository, payload: dict, *, operation: str) -> str:
    now = utc_now_iso(_CLOCK)
    agent_run_id = repository.insert_agent_run({
        "purpose": "test_authority", "provider": "learner", "provider_type": "learner",
        "started_at": now, "completed_at": now, "status": "completed",
    })
    item = {
        "client_item_id": f"facet_{operation}_1", "item_type": "facet", "operation": operation,
        "target_entity_type": "facet" if operation == "update" else None,
        "target_entity_id": payload["id"] if operation == "update" else None, "payload": payload,
        "source_ref_ids": [], "audit": {"origin": "test"}, "decision": "pending",
        "validation_status": "valid", "validation_errors": [], "depends_on_client_item_ids": [],
        "dependency_status": "pending", "created_at": now, "updated_at": now,
    }
    return repository.persist_proposal_batch({
        "agent_run_id": agent_run_id, "purpose": "test_facet_authority", "summary": "authority",
        "source_refs": [], "status_cache": "pending", "created_at": now, "updated_at": now,
    }, [item])


def _support(*citations, label: str = "test") -> list[dict]:
    return [{"from": label, "citations": [dict(citation) for citation in citations]}]


def _meaning(payload: dict) -> str:
    fields = ("kind", "claim", "description", "preconditions", "postconditions", "applicability", "non_goals",
              "positive_examples", "negative_examples")
    return json.dumps({name: payload.get(name) for name in fields}, sort_keys=True)


def _exam_vault(tmp_path):
    """The bootstrap textbook map with the held-out exam paper in the set (``_setup(with_exam=True)``)."""

    from learnloop.content.synthesis.source_set_synthesis import create_study_map

    from tests.source_set_synthesis_helpers import FakeSynthesisClient

    root, repo = _setup(tmp_path, with_exam=True)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True,
                     brief={"depth": "intro"})
    return root, repo


def _consolidation(tmp_path, *, survivor_cites, retired_cites, action, absorb_as):
    root, repo = _setup(tmp_path, with_exam=True)
    vault = load_vault(root)
    inputs = _collect_inputs(repo, vault, _source_set(root))
    synth = SourceSetSynthesis(
        concepts=[SynthConcept(client_item_id="c_sym", id="concept_symmetric_matrix", title="Symmetric matrix")],
        facets=[
            SynthFacet(client_item_id="f_survivor", id="facet_symmetry", concept_client_id="c_sym",
                       kind="definition", claim="A real square matrix is symmetric exactly when A^T = A.",
                       preconditions=["the matrix is real and square"],
                       provenance=[SynthSpanRef(**survivor_cites, relation="primary")]),
            SynthFacet(client_item_id="f_retired", id="facet_symmetry_exam", concept_client_id="c_sym",
                       kind="definition", claim=EXAM_CLAIM, preconditions=[EXAM_CONDITION],
                       provenance=[SynthSpanRef(**retired_cites, relation="primary")]),
        ],
    )
    plan = FacetIdentityPlan(status="judged", retirements={"f_retired": Retirement(
        client_id="f_retired", scope="in_run", action=action, absorb_as=absorb_as, survivor_client="f_survivor",
    )})
    normalized = normalize(synth, inputs, vault, NOW, subject_id=SUBJECT, facet_identity_plan=plan)
    report = run_synthesis_gates(GateProposal(items=normalized.gate_items), _gate_context(vault, repo, inputs, []))
    survivor = next(row["payload"] for row in normalized.rows if row["client_item_id"] == "f_survivor")
    return normalized, report, survivor


def _exam_alias_consolidation(tmp_path):
    """An ingest run whose judge merges an exam-only candidate into the textbook one (it joins as an alias)."""

    from learnloop.content.synthesis.source_set_synthesis import create_study_map

    from tests.facet_identity_fakes import FakeFacetJudge
    from tests.facet_identity_ingest_helpers import DEF_CLAIM
    from tests.source_set_synthesis_helpers import FakeSynthesisClient, _default_payload

    def with_exam_duplicate(context, _ordinal):
        payload = _default_payload(context)
        payload.facets.append(SynthFacet(
            client_item_id="f_exam_dup", id="facet_symmetry_exam", concept_client_id="c_sym", kind="definition",
            claim=EXAM_CLAIM, preconditions=[EXAM_CONDITION], positive_examples=["an exam-only example"],
            provenance=[SynthSpanRef(**EXAM_SPAN, relation="primary")],
        ))
        return payload

    root, repo = _setup(tmp_path, with_exam=True)
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=with_exam_duplicate),
                              repository=repo, clock=_CLOCK, apply=True,
                              facet_identity_client=FakeFacetJudge(clusters=[[DEF_CLAIM, EXAM_CLAIM]]))
    return root, repo, result


def _owner_judgments(repo) -> list[dict]:
    with repo.connection() as connection:
        rows = connection.execute("SELECT * FROM judgment_ledger WHERE judge = 'owner' ORDER BY id").fetchall()
    return [dict(row) for row in rows]


#: The source tree of the ``learnloop`` actually imported (``src/``).
_SRC = Path(learnloop.__file__).resolve().parents[1]
#: Modules allowed to name the facet registry file at all, and why.
_REGISTRY_FILE_MODULES = {
    "learnloop/content/facet_identity/authority.py": "the chokepoint: the one writer",
    "learnloop/content/facet_identity/actions.py": "reads the registry document (merges, undo, Library)",
    "learnloop/vault/paths.py": "defines the path",
    "learnloop/vault/loader.py": "reads it; creates an empty registry for a new vault",
    "learnloop/vault/writer.py": "upsert_facet, called only by the proposal compiler (checked below)",
    "learnloop/ops/doctor.py": "reads and reports",
    "learnloop_sidecar/handlers/library.py": "routes a Library save of the registry to save_registry_text",
}
#: Functions that write facet meaning, and the only modules that may call them.
_GUARDED_CALLS = {
    "upsert_facet": {"learnloop/content/proposals/patches.py"},
    "union_payload": {"learnloop/content/facet_identity/authority.py",
                      # builds the judge's read-only view of a consolidated candidate
                      "learnloop/content/facet_identity/plan.py"},
    "write_registry_text": {"learnloop/content/facet_identity/actions.py",
                            "learnloop/content/facet_identity/authority.py"},
    "OwnerEdit": {"learnloop/content/facet_identity/actions.py"},
    # A proposal's facet writes compile only inside the checked apply.
    "compile_proposal_item": {"learnloop/content/proposals/apply_protocol.py"},
    "stage_target_contents": {"learnloop/content/proposals/patches.py"},
}


def _python_sources():
    for path in sorted(_SRC.rglob("*.py")):
        yield path.relative_to(_SRC).as_posix(), ast.parse(path.read_text(encoding="utf-8"))


def _called(node: ast.Call) -> str:
    func = node.func
    return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
