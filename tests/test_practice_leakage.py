"""ING M8 — cross-source practice generation leakage controls (§8.5, §14).

Canned codex, zero network. Proves the held-out leakage inventory + the
deterministic gate: a planted held-out phrase in a generated surface is BLOCKED
(never auto-applied, marked invalid), while a fresh surface passes; and the
per-item cross-source grounding context is bounded (KM §12.9).
"""

from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.content.proposals.ai_contracts import PRACTICE_GENERATION_PROMPT_VERSION
from learnloop.content.proposals.ai_contracts import AuthoringProposal
from learnloop.content.authoring.practice_generation import generate_cross_source_practice_proposal
from learnloop.content.authoring.practice_leakage import (
    build_cross_source_spans,
    build_held_out_inventory,
    check_leakage,
    screen_practice_payload,
)
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.vault.loader import load_vault

from tests.test_source_set_synthesis import FakeSynthesisClient, _EXAM_QUESTION_WORDING, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))
_LO_ID = "lo_diagonalize_symmetric"


def _apply_map(tmp_path):
    root, repo = _setup(tmp_path, with_exam=True)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo,
                     clock=_CLOCK, apply=True, brief={"outcome": "exam prep"})
    return root, repo


def _mark_probe_complete(repo):
    repo.upsert_probe_state(
        learning_object_id=_LO_ID,
        status="complete",
        algorithm_version="mvp-0.7",
        probe_phase_id=f"probe_{_LO_ID}",
        hypothesis_set_id=f"hyp_{_LO_ID}",
        probe_attempts_completed=3,
        probe_attempts_target=3,
        completed_at=_CLOCK.now().isoformat(),
        clock=_CLOCK,
    )


class _FakeAuthoringClient(StructuredClientFake):
    provider_name = "codex"
    provider_type = "test"
    model = "test-model"

    def __init__(self, proposal: AuthoringProposal):
        self._proposal = proposal
        self.contexts: list = []

    def run_authoring_proposal(self, context):
        self.contexts.append(context)
        return self._proposal


def _proposal(*, leaking_prompt: str, clean_prompt: str) -> AuthoringProposal:
    def item(cid, prompt):
        return {
            "client_item_id": cid,
            "item_type": "practice_item",
            "operation": "create",
            "proposed_entity_id": cid,
            "rationale": "generated practice",
            "review_route": "review_required",
            "payload": {
                "id": cid,
                "learning_object_id": _LO_ID,
                "practice_mode": "short_answer",
                "prompt": prompt,
                "expected_answer": "A^T = A",
                "surface_family": "computation",
                "evidence_facets": ["facet_symmetry_definition"],
                "evidence_weights": {"facet_symmetry_definition": 1.0},
            },
        }

    return AuthoringProposal.model_validate(
        {
            "summary": "cross-source practice",
            "source_refs": [],
            "items": [item("pi_leak", leaking_prompt), item("pi_clean", clean_prompt)],
        }
    )


# --- pure gate --------------------------------------------------------------


def test_held_out_inventory_flags_planted_phrase_and_passes_fresh_text(tmp_path):
    root, repo = _apply_map(tmp_path)
    vault = load_vault(root)
    inv = build_held_out_inventory(vault, repo, subject_ids=["linear-algebra"])
    assert inv.span_count == 1 and inv.shingles

    planted = f"Warm-up: {_EXAM_QUESTION_WORDING} Show your reasoning."
    findings = check_leakage(planted, inv)
    assert any(f["kind"] == "wording" for f in findings)

    fresh = "Show that a real matrix that equals its own transpose has real eigenvalues."
    assert check_leakage(fresh, inv) == []


def test_screen_practice_payload_catches_expected_answer_leak(tmp_path):
    root, repo = _apply_map(tmp_path)
    vault = load_vault(root)
    inv = build_held_out_inventory(vault, repo, subject_ids=["linear-algebra"])
    payload = {"prompt": "A fresh prompt", "expected_answer": _EXAM_QUESTION_WORDING}
    assert screen_practice_payload(payload, inv)


def test_cross_source_context_is_bounded_and_authority_first(tmp_path):
    root, repo = _apply_map(tmp_path)
    vault = load_vault(root)
    spans = build_cross_source_spans(vault, repo, _LO_ID, max_spans_per_item=2)
    assert 0 < len(spans) <= 2  # KM §12.9: bounded, never grows with source count
    assert spans[0].semantic_authority is True
    assert all(s.relation in {"primary", "support", "alternate"} for s in spans)


# --- end-to-end gate --------------------------------------------------------


def test_generated_practice_never_reproduces_held_out_wording(tmp_path):
    root, repo = _apply_map(tmp_path)
    _mark_probe_complete(repo)
    client = _FakeAuthoringClient(
        _proposal(
            leaking_prompt=f"Question: {_EXAM_QUESTION_WORDING}",
            clean_prompt="When is a real square matrix equal to its transpose?",
        )
    )
    result = generate_cross_source_practice_proposal(
        root, client, learning_object_ids=[_LO_ID], max_spans_per_item=3
    )

    # The leaking item is blocked by the deterministic gate.
    blocked_ids = {b.client_item_id for b in result.leakage_blocked}
    assert "pi_leak" in blocked_ids
    assert "pi_clean" not in blocked_ids
    assert result.context_span_count > 0

    # Persisted rows: the leaking row is invalid + not applied (decision stays pending).
    rows = {row["client_item_id"]: row for row in repo.proposal_items(result.patch_id)}
    assert rows["pi_leak"]["validation_status"] == "invalid"
    assert "held_out_leakage" in (rows["pi_leak"]["validation_errors"] or [])
    assert rows["pi_leak"]["decision"] == "pending"

    # The generation ran under its own bumped prompt version, and the cross-source
    # grounding context actually reached the model.
    batch = next(b for b in repo.proposal_batches() if b["id"] == result.patch_id)
    run = repo.agent_run(batch["agent_run_id"])
    assert run["prompt_version"] == PRACTICE_GENERATION_PROMPT_VERSION
    assert "CROSS_SOURCE_CONTEXT" in client.contexts[0].instructions
    assert "BLUEPRINT_SHAPING" in client.contexts[0].instructions
