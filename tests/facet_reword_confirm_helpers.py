"""What other test files use from ``tests/test_facet_reword_confirm.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.content.facet_identity import actions as facet_actions
from learnloop.content.proposals.patches import apply_accepted_items
from learnloop.vault.loader import load_vault

from tests.helpers import seed_explanatory_source
from tests.facet_identity_actions_helpers import SHARED
from tests.facet_rewords_helpers import NEW_CLAIM


_CLOCK = FrozenClock(datetime(2026, 10, 13, 14, 0, 0, tzinfo=UTC))
THIRD_CLAIM = "A = U Sigma V^T, with the singular values on Sigma's diagonal in decreasing order."


def _seed(paths, repository, role: str, name: str, *, text: str | None = None) -> dict[str, str]:
    """A source-set member of ``role`` with one span; returns a citation of it."""

    citation = seed_explanatory_source(
        paths.root, repository, source_id=f"src_{name}", revision_id=f"rev_{name}",
        extraction_id=f"ext_{name}", unit_id=f"unit_{name}", role=role,
    )
    if text is not None:
        from learnloop.ingest.ir import DocumentBlock

        ir = repository.load_document_ir(citation["extraction_id"])
        ir.blocks = [DocumentBlock.build(span_id="s1", block_type="Text", ordinal=1, section_path=["root"],
                                         text=text)]
        repository.persist_document_ir(citation["extraction_id"], ir)
    return citation


def _support(*citations, label: str = "reword") -> list[dict]:
    return [{"from": label, "citations": [dict(citation) for citation in citations]}]


def _proposal(repository, payload: dict, *, operation: str = "update") -> str:
    """A facet proposal exactly as given (no citation added)."""

    now = utc_now_iso(_CLOCK)
    agent_run_id = repository.insert_agent_run({
        "purpose": "test_confirm", "provider": "learner", "provider_type": "learner",
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
        "agent_run_id": agent_run_id, "purpose": "test_reword_confirm", "summary": "reword",
        "source_refs": [], "status_cache": "pending", "created_at": now, "updated_at": now,
    }, [item])


def _pending(repository, root) -> list[dict]:
    return facet_actions.pending_reword_confirms(repository, load_vault(root))


def _held(paths, repository, payload: dict | None = None) -> dict:
    """An uncited reword of SHARED, accepted: it waits for the owner's confirm."""

    patch_id = _proposal(repository, payload or {"id": SHARED, "claim": NEW_CLAIM})
    apply_accepted_items(paths.root, patch_id, clock=_CLOCK)
    (confirm,) = _pending(repository, paths.root)
    return confirm
