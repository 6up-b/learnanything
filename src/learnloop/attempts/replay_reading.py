"""What replay reads of a persisted grade where the evidence reading fixes (mvp-0.61) changed it.

Replay (``attempts.replay_existing_attempt`` and the grade channel of ``apply_attempt``) re-applies each stored
answer from what was recorded. Two of its readings were wrong for a grade that was replaced or that carried no
reliability (refactor bug ledger K5-11, K5-12), and a request for a variant was read as a review of its source item
live and on replay alike (K5-8); from the tag they read as below, and below it exactly as before.
Each function takes the vault's config through ``vault`` and answers the predecessor's reading below the tag.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from learnloop.algorithm_versions import evidence_reading_fixes_on

#: The ``grading_evidence`` tier a model grader writes (a live model grade and a regrade alike).
MODEL_GRADER_TIER = 3
#: The grading sources of a model grader (the soft-score lane; ``attempts._interpretation_variance``).
MODEL_GRADING_SOURCES = frozenset({"ai", "codex"})
#: The ``agent_runs.purpose`` of a run that grades an answer (``attempts.grading``, ``attempts.regrade``,
#: ``attempts.blind_grading``, ``attempts.clarification``, ``tutor.teach_back``): only such a run can name a
#: replacement grade's source.
GRADING_RUN_PURPOSES = frozenset(
    {"grading", "grading_regrade", "blind_grading", "grading_clarification_resolution", "teach_back"}
)


def replayed_grader_confidence(vault: Any, stored: Any) -> float:
    """The grader confidence a persisted grade replays with.

    A grader may answer exactly 0.0 (``blind_grading``): the grade then carries no reliability, live. Below the
    evidence reading fixes replay read that 0.0 as missing (``or 1.0``), so every rebuild or regrade replay gave the
    grade full reliability and wrote 1.0 back to the attempt (K5-12). From the tag only a missing value (a legacy
    NULL) falls back to 1.0. A 0.0 an earlier rebuild already wrote over on the attempt row is not read back."""

    if not evidence_reading_fixes_on(vault.config):
        return float(stored or 1.0)
    return 1.0 if stored is None else float(stored)


def replayed_grading_source(vault: Any, repository: Any, attempt: Mapping[str, Any], current_rows: Sequence[Any]) -> str:
    """The grading source a persisted grade replays under.

    The feedback row records the source of the attempt's FIRST grade, and no regrade rewrites it, so below the
    evidence reading fixes a model regrade of a self-grade (the startup's deferred regrade) replayed as "self": no
    channel variance, and "self" in the grade channel (K5-11). From the tag the source is the current grading
    epoch's: when the attempt has been graded more than once, a model run other than the first grade's wrote the
    current epoch (``current_rows``), and the recorded source is not a model's, the source is that run's
    (:func:`grading_source_for_run`). A recorded model source stands (a model regrade of a model grade stays on the
    model's lane, and a run's provider column can be a default rather than a name), and so does every other case:
    the first grade still current, or a replacement no model run wrote (an owner's adjudication revises a grade
    without grading it again). The source is never invented: the current rows must name exactly one model run other
    than the first grade's, and that run must exist and be a grading run (:data:`GRADING_RUN_PURPOSES`); a missing,
    pruned or unrelated run, or two candidate runs, keep the recorded source."""

    attempt_id = str(attempt["id"])
    feedback = repository.raw_attempt_feedback_metadata(attempt_id) or {}
    recorded = feedback.get("grading_source", "self")
    if not evidence_reading_fixes_on(vault.config) or recorded in MODEL_GRADING_SOURCES:
        return recorded
    if not _graded_more_than_once(repository, attempt_id):
        return recorded
    first_run = feedback.get("agent_run_id")
    runs = sorted(
        {
            str(row.agent_run_id)
            for row in current_rows
            if row.agent_run_id and int(row.grader_tier) == MODEL_GRADER_TIER
        }
        - {first_run}
    )
    if len(runs) != 1:
        return recorded
    run = repository.agent_run(runs[0])
    if run is None or run.get("purpose") not in GRADING_RUN_PURPOSES:
        return recorded
    return grading_source_for_run(run)


def grading_source_for_run(run: Mapping[str, Any]) -> str:
    """The grading source of a model grading run, from its ``agent_runs`` row: ``codex`` for a provider
    ``CODEX_PROVIDER_NAMES`` lists, else ``ai``: the split the regrade door makes when it names a provider's source
    (``learnloop_sidecar.handlers.ai_providers.grading_source_for_provider``), by the provider name alone."""

    from learnloop.config.schema import CODEX_PROVIDER_NAMES

    return "codex" if run.get("provider") in CODEX_PROVIDER_NAMES else "ai"


def replaced_exam_purpose(vault: Any, repository: Any, attempt_id: str, replayed: bool) -> str | None:
    """The administration purpose an exam answer's grade channel is written under by ``apply_attempt``, or None
    when it writes none there.

    The exam path writes an exam answer's grade channel once, at the sitting (or not at all, for an import), so below
    the evidence reading fixes a regrade's replacement never reached a channel (K5-11). From the tag the replay
    (``replayed``) of an exam answer graded more than once writes the replacement on the exam channel's
    administration (``grade_resolution.EXAM_GRADE_PURPOSE``), appended once like a practice regrade; an exam answer
    graded once is still the exam path's alone."""

    if not replayed or not evidence_reading_fixes_on(vault.config) or not _graded_more_than_once(repository, attempt_id):
        return None
    from learnloop.attempts.grade_resolution import EXAM_GRADE_PURPOSE

    return EXAM_GRADE_PURPOSE


def withholds_review_as_variant_request(vault: Any, repository: Any, attempt_id: str) -> bool:
    """Whether this attempt is a request for an easier or harder variant whose source item it leaves unreviewed.

    A request is recorded as a ``self_report`` attempt on the source item (``content.authoring.rung_variants``): its
    belief write is the evidence the request is. Below the evidence reading fixes it was also an FSRS review of the
    source item, as any unprimed self-report is, which moved the item's forgetting clock, memory state and due date
    although the learner answered nothing (refactor bug ledger K5-8). From the tag it leaves all three as they were,
    live and on replay alike. The request is recognized by its row in ``rung_variant_requests`` naming the attempt
    (written before the attempt is applied), never by the answer text or the entry surface: the text is generated and
    older rows carry the surface ``unknown``. An attempt no request row names keeps the self-report's review."""

    if not evidence_reading_fixes_on(vault.config):
        return False
    return repository.rung_variant_request_for_attempt(attempt_id) is not None


def _graded_more_than_once(repository: Any, attempt_id: str) -> bool:
    """A second write replaced the attempt's first grade. Counting epoch keys is not enough: revision-less rows share
    ``legacy:<created_at>``, so a regrade written in its original's second falls under the original's key;
    ``grading_epochs.only_grade`` also reads a superseded row or a second run as a second write. No rows: no grade."""

    from learnloop.grading_epochs import graded_more_than_once

    return graded_more_than_once(repository.fetch_grading_evidence(attempt_id, include_superseded=True))


__all__ = [
    "GRADING_RUN_PURPOSES",
    "MODEL_GRADER_TIER",
    "MODEL_GRADING_SOURCES",
    "grading_source_for_run",
    "replaced_exam_purpose",
    "replayed_grader_confidence",
    "replayed_grading_source",
    "withholds_review_as_variant_request",
]
