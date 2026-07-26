"""Learner-facing changelog and standing working hypotheses."""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.services.remediation import misconception_status_history
from learnloop.services.session_learning_diff import session_learning_diffs
from learnloop.services.surfaced_beliefs import surfaced_belief_corrections
from learnloop.vault.models import LoadedVault


def _empty_belief_change() -> dict[str, Any]:
    """Zeroed belief-change fields shared by system-authored changelog entries.

    Regrade and recalibration entries carry no per-session belief movement, but
    the Review UI reads these keys on every entry, so they are always present.
    """

    return {
        "attempts_recorded": 0,
        "items_reviewed": 0,
        "predictions_moved": {"up": 0, "down": 0},
        "corrections": 0,
        "facets_demonstrated": 0,
        "misconceptions_touched": {"resolved": 0, "returned": 0},
    }


def build_learner_review_feed(
    vault: LoadedVault, repository: Repository
) -> dict[str, Any]:
    changelog: list[dict[str, Any]] = []
    # Session windows [started_at, ended_at] partition regrades into
    # in-session (already counted as the session diff's `corrections`) and
    # out-of-session (surfaced here as their own system-authored entries).
    session_windows: list[tuple[str, str]] = []
    sessions = repository.review_session_rows()
    learning_diffs = session_learning_diffs(vault, repository, sessions)
    for session in sessions:
        attempts = session["attempts"]
        learning_diff = learning_diffs.get(str(session["id"]), _empty_belief_change())
        started_at = session.get("started_at")
        ended_at = session.get("ended_at")
        if started_at is not None and ended_at is not None:
            session_windows.append((str(started_at), str(ended_at)))
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

    def _in_session(at: str) -> bool:
        return any(start <= at <= end for start, end in session_windows)

    # System-authored regrade entries: only regrades applied OUTSIDE any
    # session window (maintenance/deferred/manual out-of-session). In-session
    # regrades stay folded into their session entry's `corrections` count and
    # are deliberately not re-listed as top-level entries.
    for transition in repository.regrade_epoch_transitions():
        at = str(transition["at"])
        if _in_session(at):
            continue
        item = vault.practice_items.get(str(transition["practice_item_id"]))
        facets = (
            sorted(
                vault.canonical_facet_id(str(facet))
                for facet in item.evidence_facets
            )
            if item is not None
            else []
        )
        old_score = float(transition["old_points"])
        new_score = float(transition["new_points"])
        if new_score < old_score:
            direction = "down"
        elif new_score > old_score:
            direction = "up"
        else:
            direction = "same"
        changelog.append(
            {
                **_empty_belief_change(),
                "id": f"regrade:{transition['attempt_id']}:{at}",
                "kind": "regrade",
                "at": at,
                "items_reviewed": 1,
                "facet_ids": facets,
                "direction": direction,
                "old_score": old_score,
                "new_score": new_score,
            }
        )

    # Recalibration: an algorithm_version bump collapses to ONE honest entry
    # ("estimates recomputed — your evidence unchanged"), never a per-facet
    # flood the learner appears to have caused (§4.9).
    for change in repository.derived_state_rebuild_version_changes():
        changelog.append(
            {
                **_empty_belief_change(),
                "id": f"recalibration:{change['id']}",
                "kind": "recalibration",
                "at": str(change["at"]),
                "facet_ids": [],
                "algorithm_version": change["algorithm_version"],
                "previous_algorithm_version": change[
                    "previous_algorithm_version"
                ],
                # Measurement §5.2: name WHICH boundary recomputed the estimates.
                # A coverage-denominator change moves displayed mastery without
                # touching the evidence or the projection, and an entry that could
                # not say so would be indistinguishable from an algorithm rewrite.
                "canonical_projection_version": change.get(
                    "canonical_projection_version"
                ),
                "coverage_denominator_version": change.get(
                    "coverage_denominator_version"
                ),
                "previous_coverage_denominator_version": change.get(
                    "previous_coverage_denominator_version"
                ),
            }
        )

    # A6 (spec_diagnostic_augmentation_v1.md §2 A6): a belief the learner was
    # SHOWN and that has since been withdrawn gets an explicit retraction. This
    # is the counterpart of the §5.6 contest affordance — the learner could
    # already object, and now the system can apologise. Three properties are
    # load-bearing and all three live in the producer:
    #   * scope — only beliefs with a `surfaced_to_learner` presentation; retiring
    #     an internal provisional hypothesis nobody saw stays housekeeping;
    #   * wording — the claim is quoted as it was shown, not as the (mutable)
    #     belief statement reads now;
    #   * idempotency — the entry id is keyed on the disposition EVENT, so
    #     rebuilding the feed re-derives the same entry and a belief shown five
    #     times is withdrawn once.
    for withdrawal in surfaced_belief_corrections(repository):
        changelog.append(
            {
                **_empty_belief_change(),
                "id": withdrawal.entry_id,
                "kind": "belief_withdrawn",
                "at": withdrawal.at,
                "facet_ids": list(withdrawal.facet_ids),
                "belief_kind": withdrawal.belief_kind,
                "belief_id": withdrawal.belief_id,
                "learning_object_id": withdrawal.learning_object_id,
                # The claim in the learner's own reading, plus an honesty marker
                # saying whether that is literally the string they were shown.
                "withdrawn_claim_text": withdrawal.withdrawn_claim_text,
                "claim_text_source": withdrawal.claim_text_source,
                "withdrawal_reason": withdrawal.withdrawal_reason,
                "statement": withdrawal.statement,
                "disposition": withdrawal.disposition,
                "surfaced_at": withdrawal.surfaced_at,
                "surfaced_on": withdrawal.surfaced_on,
                # A successor is reported ALONGSIDE the retraction, never instead
                # of it — A6 forbids quietly re-stating a withdrawn claim as a
                # weaker belief.
                "replacement_belief_id": withdrawal.replacement_belief_id,
                "replacement_statement": withdrawal.replacement_statement,
            }
        )

    # Interleave all entries reverse-chronologically. Deterministic tiebreak on
    # id so equal timestamps order stably.
    changelog.sort(key=lambda entry: (str(entry["at"]), str(entry["id"])), reverse=True)

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
