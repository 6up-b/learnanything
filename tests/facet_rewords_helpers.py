"""What other test files use from ``tests/test_facet_rewords.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from learnloop.clock import FrozenClock, utc_now_iso
from learnloop.vault.yaml_io import read_yaml

from tests.helpers import seed_explanatory_source


_CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))
OLD_CLAIM = "SVD factorizes into U, Sigma, V^T."
NEW_CLAIM = "Every real matrix factorizes as U Sigma V^T with orthogonal U, V and non-negative diagonal Sigma."
#: The facet's meaning (``facet_identity.authority.AUTHORITY_FIELDS``).
_MEANING_KEYS = {"kind", "title", "claim", "description", "preconditions", "postconditions", "applicability",
                 "non_goals", "positive_examples", "negative_examples"}


def _facet_update_proposal(repository, payload: dict, *, cited: bool = True) -> str:
    """A facet update proposal. One that changes the facet's meaning cites an
    explanatory span (``seed_explanatory_source``), as the facet-meaning
    chokepoint requires; ``cited=False`` leaves it uncited."""

    if cited and "meaning_support" not in payload and set(payload) & _MEANING_KEYS:
        citation = seed_explanatory_source(Path(repository.sqlite_path).parent, repository)
        payload = {**payload, "meaning_support": [{"from": "test", "citations": [citation]}]}
    now = utc_now_iso(_CLOCK)
    agent_run_id = repository.insert_agent_run({
        "purpose": "test_append", "provider": "learner", "provider_type": "learner",
        "started_at": now, "completed_at": now, "status": "completed",
    })
    item = {
        "client_item_id": "facet_update_1", "item_type": "facet", "operation": "update",
        "target_entity_type": "facet", "target_entity_id": payload["id"], "payload": payload,
        "source_ref_ids": [], "audit": {"origin": "test"}, "decision": "pending",
        "validation_status": "valid", "validation_errors": [], "depends_on_client_item_ids": [],
        "dependency_status": "pending", "created_at": now, "updated_at": now,
    }
    return repository.persist_proposal_batch({
        "agent_run_id": agent_run_id, "purpose": "test_facet_update", "summary": "reword",
        "source_refs": [], "status_cache": "pending", "created_at": now, "updated_at": now,
    }, [item])


def _entry(paths, facet_id: str) -> dict:
    return next(entry for entry in read_yaml(paths.facets_path)["facets"] if entry["id"] == facet_id)
