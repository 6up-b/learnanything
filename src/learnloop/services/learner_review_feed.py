"""Learner-facing changelog and standing working hypotheses."""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.remediation import misconception_status_history
from learnloop.services.session_learning_diff import session_learning_diff
from learnloop.vault.models import LoadedVault


def build_learner_review_feed(
    vault: LoadedVault, repository: Repository
) -> dict[str, Any]:
    changelog: list[dict[str, Any]] = []
    for session in repository.review_session_rows():
        attempts = session["attempts"]
        learning_diff = session_learning_diff(vault, repository, session["id"])
        facet_ids: set[str] = set()
        for attempt in attempts:
            item = vault.practice_items.get(str(attempt["practice_item_id"]))
            if item is not None:
                facet_ids.update(
                    vault.canonical_facet_id(str(facet))
                    for facet in item.evidence_facets
                )
        changelog.append(
            {
                "id": session["id"],
                "kind": "session",
                "at": session["ended_at"],
                "attempts_recorded": len(attempts),
                "items_reviewed": len(
                    {row["practice_item_id"] for row in attempts}
                ),
                "predictions_moved": {
                    **learning_diff["predictions_moved"],
                },
                "facet_ids": sorted(facet_ids),
                "corrections": learning_diff["corrections"],
                "facets_demonstrated": learning_diff["facets_demonstrated"],
                "misconceptions_touched": learning_diff[
                    "misconceptions_touched"
                ],
            }
        )

    working = []
    seen: set[str] = set()
    for learning_object_id in sorted(vault.learning_objects):
        for record in repository.misconceptions_for_learning_object(
            learning_object_id, statuses=("active", "resolving")
        ):
            if record.id in seen or not record.correction_statement:
                continue
            seen.add(record.id)
            working.append(
                {
                    "id": record.id,
                    "learning_object_id": record.learning_object_id,
                    "statement": record.statement,
                    "correction_statement": record.correction_statement,
                    "mechanism": record.mechanism,
                    "target_facet": record.target_facet,
                    "confused_with_facet": record.confused_with_facet,
                    "status": record.status,
                    "history": misconception_status_history(
                        repository, record.id
                    ),
                    "severity": record.severity,
                }
            )
    working.sort(key=lambda row: (-float(row["severity"]), row["id"]))
    return {"changelog": changelog, "working_hypotheses": working}
