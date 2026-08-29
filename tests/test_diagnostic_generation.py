"""§5 diagnostic generation end-to-end + §6 gate wiring."""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.db.repositories import Repository
from learnloop.content.proposals.proposals import generate_diagnostic_proposal
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import NOW_ISO, create_basic_vault


class _FakeClient(StructuredClientFake):
    provider_name = "codex"
    provider_type = "test"
    model = "test-model"

    def __init__(self, proposal: AuthoringProposal):
        self._proposal = proposal
        self.contexts: list = []

    def run_authoring_proposal(self, context):
        self.contexts.append(context)
        return self._proposal


def _proposal(*, expected="Qx is the coordinate vector", mc_consistent="Q^T x is the coordinate vector"):
    return AuthoringProposal.model_validate(
        {
            "summary": "diagnostic",
            "source_refs": [],
            "items": [
                {
                    "client_item_id": "c_diag",
                    "item_type": "practice_item",
                    "operation": "create",
                    "proposed_entity_id": "pi_diag_gen",
                    "rationale": "Diagnostic applying the belief to a concrete instance.",
                    "review_route": "review_required",
                    "payload": {
                        "id": "pi_diag_gen",
                        "learning_object_id": "lo_svd_definition",
                        "practice_mode": "short_answer",
                        "prompt": "Compute Q^T x; which of Qx / Q^T x is the coordinate vector?",
                        "expected_answer": expected,
                        "misconception_consistent_answer": mc_consistent,
                        "surface_family": "computation",
                        "evidence_facets": ["recall"],
                        "evidence_weights": {"recall": 1.0},
                        "grading_rubric": {
                            "max_points": 4,
                            "criteria": [{"id": "c1", "points": 4, "description": "correct"}],
                            "fatal_errors": [
                                {"id": "fe_reversed", "description": "reverses Q/Q^T", "misconception_id": "mc_reverse_q", "max_grade": 1}
                            ],
                        },
                    },
                }
            ],
        }
    )


def _setup(root):
    # 8 trials so a perfect discriminator clears the 25th-percentile bounds.
    toml = (root / "learnloop.toml").read_text().replace("sim_gate_trials = 5", "sim_gate_trials = 8")
    (root / "learnloop.toml").write_text(toml)
    vault = load_vault(root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    repository.insert_misconception(
        id="mc_reverse_q",
        learning_object_id="lo_svd_definition",
        statement="reverses Q / Q^T",
        signature="Q^T x is the coordinate vector",
        facet_ids=["recall"],
        severity=0.9,
        status="active",
    )
    need_id = repository.upsert_intervention_need(
        {
            "attempt_id": "att_diag",
            "learning_object_id": "lo_svd_definition",
            "practice_item_id": "pi_svd_define_001",
            "desired_intent": "repair",
            "trigger_reason": "severe_error_event",
            "target_facets": ["recall"],
            "error_types": [],
            "priority": 0.9,
            "status": "pending",
            "blocked_reason": "no_suitable_item",
            "candidate_requirements": {},
            "diagnostic_focus": {
                "misconception_ids": ["mc_reverse_q"],
                "misconception_statements": {"mc_reverse_q": "reverses Q / Q^T"},
                "source_practice_item_id": "pi_svd_define_001",
                "source_surface_family": "definition",
                "demonstrated_facets": [],
                "implicated_facets": ["recall"],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        }
    )
    return repository, need_id


def test_generate_diagnostic_accepted_and_reviewed(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository, need_id = _setup(root)
    client = _FakeClient(_proposal())

    patch_id = generate_diagnostic_proposal(root, client, need_id=need_id)

    # Need linked to the queued patch.
    need = repository.intervention_need(need_id)
    assert need["blocked_reason"].startswith(f"diagnostic_proposal_queued:{patch_id}")
    assert need["status"] == "fulfilled"
    # Item persisted, validated with context (not invalid), still pending (gate passed).
    items = repository.proposal_items(patch_id)
    assert len(items) == 1
    assert items[0]["decision"] == "pending"
    assert items[0]["validation_status"] != "invalid"
    # Discrimination row seeded by the gate.
    row = repository.discrimination_row("pi_diag_gen", "mc_reverse_q")
    assert row is not None and row.source == "sim"


def test_generate_diagnostic_gate_failure_reopens_need(tmp_path):
    root = create_basic_vault(tmp_path / "vault").root
    repository, need_id = _setup(root)
    # Paraphrase: planted answer equals expected -> gate fails.
    client = _FakeClient(_proposal(mc_consistent="Qx is the coordinate vector"))

    patch_id = generate_diagnostic_proposal(root, client, need_id=need_id)

    items = repository.proposal_items(patch_id)
    assert items[0]["decision"] == "rejected"
    need = repository.intervention_need(need_id)
    assert need["status"] == "pending"
    assert need["blocked_reason"].startswith(f"diagnostic_proposal_rejected:{patch_id}")
    focus = need["diagnostic_focus"]
    assert "last_gate_result" in focus
    assert focus["last_gate_result"][0]["accepted"] is False
