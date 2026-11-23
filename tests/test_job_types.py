"""What an ingest job type is: its handler and its four flags.

``EXPECTED`` is the characterization: for every job type the host runs, the
handler that runs it and whether it applies vault content (the sidecar reloads
its vault after one), bumps Today's queue revision when it completes, runs in
the parallel lane, and waits for the learner's one AI OK before it starts.
"""

from __future__ import annotations

import pytest

#: type: (handler name, applies_vault, affects_queue, parallel, waits_for_ai_ok)
EXPECTED: dict[str, tuple[str, bool, bool, bool, bool]] = {
    "import": ("handle_import", False, False, False, False),
    "auto_study_map": ("handle_auto_study_map", False, False, False, False),
    "legacy_ingest": ("handle_legacy_ingest", True, False, False, True),
    "exam_ingest": ("handle_legacy_ingest", True, False, False, True),
    "inventory": ("handle_inventory", False, False, False, True),
    "bootstrap_synthesis": ("handle_bootstrap_synthesis", True, False, False, True),
    "append_synthesis": ("handle_append_synthesis", True, False, False, True),
    "extraction_repair": ("handle_extraction_repair", False, False, False, False),
    "reader_quick_check": ("handle_reader_quick_check", False, False, True, True),
    "reader_exercise_import": ("handle_reader_exercise_import", True, True, False, True),
    "source_exercise_import": ("handle_source_exercise_import", True, False, False, True),
    "practice_expansion": ("handle_practice_expansion", True, True, False, True),
    "goal_population": ("handle_goal_population", True, True, False, True),
    "question_promotion": ("handle_question_promotion", True, True, False, True),
    "rung_variant": ("handle_rung_variant", True, True, False, True),
    "concept_animation": ("handle_concept_animation", False, False, False, True),
    "figure_rich": ("handle_figure_rich", False, False, False, True),
    "source_embedding_backfill": ("handle_source_embedding_backfill", False, False, False, True),
    "curriculum_coverage_on_extract": ("handle_curriculum_coverage_on_extract", False, False, False, False),
    "local_source_index": ("handle_local_source_index", False, False, False, False),
    "source_fallback_backfill": ("handle_source_fallback_backfill", False, False, False, False),
}


def _observed() -> dict[str, tuple[str, bool, bool, bool, bool]]:
    from learnloop.content.pipeline import jobs, runner

    return {
        job_type: (
            handler.__name__,
            job_type in jobs.APPLYING_JOB_TYPES,
            job_type in runner._QUEUE_AFFECTING_JOB_TYPES,
            job_type in jobs._PARALLEL_JOB_TYPES,
            job_type in runner.WAITS_FOR_AI_OK_JOB_TYPES,
        )
        for job_type, handler in jobs.DEFAULT_HANDLERS.items()
    }


def test_every_job_type_runs_as_characterized() -> None:
    assert _observed() == EXPECTED


@pytest.mark.parametrize("column", [1, 2, 3, 4])
def test_no_flag_names_a_type_without_a_handler(column: int) -> None:
    from learnloop.content.pipeline import jobs, runner

    flagged = [jobs.APPLYING_JOB_TYPES, runner._QUEUE_AFFECTING_JOB_TYPES, jobs._PARALLEL_JOB_TYPES,
               runner.WAITS_FOR_AI_OK_JOB_TYPES][column - 1]
    assert set(flagged) <= set(jobs.DEFAULT_HANDLERS)
