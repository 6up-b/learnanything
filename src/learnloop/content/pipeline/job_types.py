"""What each ingest job type is: one row per type.

A row names the type's handler and what the host, the runner and the sidecar need to know about it:

- ``applies_vault``: its completion can change vault content (an applied study map, a canonical note, practice
  items). The sidecar reloads its in-memory vault after one finishes in the background drain, or the screens that
  read the loaded vault (Today, the knowledge map) keep serving the pre-apply snapshot.
- ``affects_queue``: it can add or replace scheduler-visible practice, so the runner bumps the durable queue revision
  once the job row itself is completed, never before: a Today poll must not see the revision before the sidecar can
  reload the newly written vault state.
- ``parallel``: it runs in the bounded parallel lane beside the single vault-writing worker. Only work that writes
  durable SQLite rows and never vault YAML may, or the single-writer invariant breaks.
- ``waits_for_ai_ok``: its whole purpose is model work, so without the learner's one OK to use AI it waits for it
  before it starts instead of failing and being tried again. A job of another type that reaches a model call waits
  the same way, from the refusal itself.
- ``client_routes``: the AI routes of the clients the runner's services give its handler when no test injects one
  (empty when the handler asks the services for no model client; its feature then resolves its own route).

A new job type is its handler, beside its feature, and one row here. This is a plain table, not a registry: nothing
is discovered and nothing registers itself.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from learnloop.content.pipeline.runner import Handler

_IMPORT = "learnloop.content.pipeline.import_jobs"
_SYNTHESIS = "learnloop.content.synthesis.jobs"
_AUTHORING = "learnloop.content.authoring.jobs"
_FIGURES = "learnloop.figures.jobs"
_RETRIEVAL = "learnloop.source_retrieval.jobs"


@dataclass(frozen=True)
class JobType:
    name: str
    #: ``module:function``. A name, not the function: the runner and the sidecar read the rows' facts without
    #: importing every feature's job module, and only the runner that dispatches resolves it
    #: (:func:`resolve_handler`).
    handler: str
    applies_vault: bool = False
    affects_queue: bool = False
    parallel: bool = False
    waits_for_ai_ok: bool = False
    client_routes: tuple[str, ...] = ()


JOB_TYPES: tuple[JobType, ...] = (
    JobType("import", f"{_IMPORT}:handle_import"),
    JobType("auto_study_map", f"{_IMPORT}:handle_auto_study_map"),
    JobType("legacy_ingest", f"{_IMPORT}:handle_legacy_ingest", applies_vault=True, waits_for_ai_ok=True,
            client_routes=("canonical_ingest",)),
    JobType("exam_ingest", f"{_IMPORT}:handle_legacy_ingest", applies_vault=True, waits_for_ai_ok=True,
            client_routes=("canonical_ingest",)),
    JobType("inventory", f"{_SYNTHESIS}:handle_inventory", waits_for_ai_ok=True, client_routes=("canonical_ingest",)),
    JobType("bootstrap_synthesis", f"{_SYNTHESIS}:handle_bootstrap_synthesis", applies_vault=True, waits_for_ai_ok=True,
            client_routes=("canonical_ingest",)),
    JobType("append_synthesis", f"{_SYNTHESIS}:handle_append_synthesis", applies_vault=True, waits_for_ai_ok=True,
            client_routes=("canonical_ingest",)),
    JobType("extraction_repair", f"{_IMPORT}:handle_extraction_repair"),
    # Database rows only (an authored check), so it may run beside the vault writer.
    JobType("reader_quick_check", f"{_AUTHORING}:handle_reader_quick_check", parallel=True, waits_for_ai_ok=True,
            client_routes=("canonical_ingest",)),
    # Reader-selected textbook exercises become vault practice items directly.
    JobType("reader_exercise_import", f"{_AUTHORING}:handle_reader_exercise_import", applies_vault=True, affects_queue=True,
            waits_for_ai_ok=True, client_routes=("canonical_ingest",)),
    # Picked textbook exercise proposals too (canonical sources S1).
    JobType("source_exercise_import", f"{_AUTHORING}:handle_source_exercise_import", applies_vault=True, waits_for_ai_ok=True,
            client_routes=("canonical_ingest",)),
    # Reader-driven progressive generation auto-applies grounded items.
    JobType("practice_expansion", f"{_AUTHORING}:handle_practice_expansion", applies_vault=True, affects_queue=True,
            waits_for_ai_ok=True, client_routes=("canonical_ingest",)),
    # Goal-wizard population applies generated practice directly.
    JobType("goal_population", f"{_AUTHORING}:handle_goal_population", applies_vault=True, affects_queue=True, waits_for_ai_ok=True,
            client_routes=("canonical_ingest",)),
    # Open-question promotions may materialize a note and auto-apply practice.
    JobType("question_promotion", f"{_AUTHORING}:handle_question_promotion", applies_vault=True, affects_queue=True,
            waits_for_ai_ok=True, client_routes=("tutor_qa", "authoring")),
    # Learner-requested easier/harder variants auto-apply when grounded.
    JobType("rung_variant", f"{_AUTHORING}:handle_rung_variant", applies_vault=True, affects_queue=True, waits_for_ai_ok=True,
            client_routes=("rung_variant",)),
    JobType("concept_animation", f"{_AUTHORING}:handle_concept_animation", waits_for_ai_ok=True,
            client_routes=("animation", "video_generation")),
    JobType("figure_rich", f"{_FIGURES}:handle_figure_rich", waits_for_ai_ok=True),
    JobType("source_embedding_backfill", f"{_RETRIEVAL}:handle_source_embedding_backfill", waits_for_ai_ok=True),
    JobType("curriculum_coverage_on_extract", f"{_RETRIEVAL}:handle_curriculum_coverage_on_extract"),
    JobType("local_source_index", f"{_RETRIEVAL}:handle_local_source_index"),
    JobType("source_fallback_backfill", f"{_RETRIEVAL}:handle_source_fallback_backfill"),
)

_BY_NAME = {row.name: row for row in JOB_TYPES}


def job_type(name: str) -> JobType | None:
    """The row for ``name``, or None for a type the table does not hold (a handler a test injects)."""

    return _BY_NAME.get(name)


def resolve_handler(reference: str) -> Handler:
    """The handler a row's ``module:function`` names, importing its module."""

    module, _, function = reference.partition(":")
    return getattr(importlib.import_module(module), function)


def default_handlers() -> dict[str, Handler]:
    return {row.name: resolve_handler(row.handler) for row in JOB_TYPES}


def applying_job_types() -> tuple[str, ...]:
    return tuple(row.name for row in JOB_TYPES if row.applies_vault)


def parallel_job_types() -> tuple[str, ...]:
    return tuple(row.name for row in JOB_TYPES if row.parallel)
