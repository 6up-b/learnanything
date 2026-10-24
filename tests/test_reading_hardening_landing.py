"""Reading-hardening landed onto main (mvp-0.22, exam protection, the Decider).

The branch retired the per-book AI opt-out (``source_artifacts.keep_local``)
and made one check-offer rule the Reader's only offer path. Main had since
added a keep-local guard on the Decider's span-support check, and exam
protection's held-out refusals at every Reader model boundary. These pin how
they compose: nothing consults ``keep_local``; a held-out section's check is
never offered, because the guide plan never lists one and the authoring RPC
refuses before anything is queued or sent. Fakes only, no network, no paid call.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from tests.source_service_fakes import build_textbook_vault, loaded

SRC = Path(__file__).resolve().parents[1] / "src"


# -- keep_local is never consulted ---------------------------------------------------------------


def test_nothing_in_src_consults_the_retired_keep_local():
    """Only doctor's warning reads the column's value (through the repository's
    ``sources_with_retired_keep_local``); the other mentions are prose. The
    Decider landing's span-support guard (``source_kept_local``) is gone."""

    readers = {"src/learnloop/db/repositories.py", "src/learnloop/ops/doctor.py"}
    prose = {"src/learnloop/content/pipeline/add_source.py",
             "src/learnloop/content/facet_identity/span_support.py",
             # The AD guard's column registry names every column (AD23 redesign round 5); it reads nothing.
             "src/learnloop/adaptive_difficulty/column_classes.py"}
    mentions: dict[str, list[str]] = {}
    for path in sorted(SRC.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(SRC.parent).as_posix()
        assert not re.search(r"source_kept_local|set_source_keep_local|kept_on_this_computer", text), rel
        lines = [line for line in text.splitlines() if "keep_local" in line]
        if lines:
            mentions[rel] = lines
    assert set(mentions) <= readers | prose, sorted(set(mentions) - readers - prose)
    for rel in prose & set(mentions):
        # Docstring prose only: no attribute, key or SQL read of the column.
        for line in mentions[rel]:
            assert not re.search(r"\[\s*['\"]keep_local['\"]\s*\]|(?<!source_artifacts)\.keep_local\b|get\(\s*['\"]keep_local", line), line


# -- a held-out section's check is never offered -------------------------------------------------


@pytest.fixture
def held_out_book(tmp_path):
    """The textbook vault with a proposed check authored for two sections,
    then its exercises unit marked held out (the check came before the mark)."""

    from learnloop.reader.reader_guidance import extraction_sections

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    section_rows, _blocks, _sections = extraction_sections(repository.load_document_ir("ext_text"))
    held = next(row["id"] for row in section_rows if spans["exercises"][1] in row["span_ids"])
    other = next(row["id"] for row in section_rows if row["id"] != held and row["span_ids"])
    for section_id in (held, other):
        repository.insert_reader_authored_question(fields={
            "extraction_id": "ext_text", "section_id": section_id, "source_id": None,
            "question_md": f"Explain {section_id}.", "expected_answer_md": "An answer.",
            "span_ids": [], "prompt_version": "test", "provider": "fake", "model": "fake",
        })
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"exercises": "held_out_evaluation"})
    return paths, repository, held, other


def test_the_guide_plan_never_lists_a_check_for_a_held_out_section(held_out_book):
    """The check-offer rule (``checkOffer.ts``) offers only a section whose plan
    carries a check (``readingPhase`` null is ``no_check``), so a check
    authored before the mark is withheld here; every other section keeps its
    check and the rule's reading conditions."""

    from learnloop.reader.reader_guidance import build_guide_plan

    paths, repository, held, other = held_out_book
    plan = build_guide_plan(loaded(paths), repository, extraction_id="ext_text")
    by_id = {section["id"]: section for section in plan["sections"]}
    assert by_id[held]["question"] is None
    assert by_id[other]["question"]["placement"] == "auto_authored"
    assert by_id[other]["question"]["reading_phase"] == "after_section"


def _author_rpc_ctx(paths, repository, enqueued):
    vault = loaded(paths)
    return SimpleNamespace(
        require_vault=lambda: (vault, repository),
        ingest_jobs=SimpleNamespace(
            enqueue_reader_quick_check=lambda **payload: enqueued.append(payload) or "batch_1"),
    )


def test_asking_for_a_held_out_sections_check_is_refused_before_anything_is_queued(held_out_book, monkeypatch):
    """``reader.author_section_question`` (the Reader's producer and its "Try
    again") refuses with ``exam_material`` before handing back the check
    authored before the mark or queueing a job; another section's existing
    check is still handed back."""

    from learnloop.content.sources.exam_material import HELD_OUT_REFUSAL
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import ai_providers
    from learnloop_sidecar.handlers import reader

    paths, repository, held, other = held_out_book
    monkeypatch.setattr(ai_providers, "ready_canonical_ingest_provider",
                        lambda vault: pytest.fail("no provider is resolved for a held-out section"))
    enqueued: list[dict] = []
    ctx = _author_rpc_ctx(paths, repository, enqueued)
    with pytest.raises(SidecarError) as refused:
        reader.reader_author_section_question(
            ctx, reader.ReaderAuthorSectionQuestionInput(extraction_id="ext_text", section_id=held))
    assert refused.value.code == "exam_material"
    assert refused.value.message == HELD_OUT_REFUSAL
    assert enqueued == []
    handed = reader.reader_author_section_question(
        ctx, reader.ReaderAuthorSectionQuestionInput(extraction_id="ext_text", section_id=other))
    assert handed["status"] == "exists" and handed["question"]["status"] == "proposed"


def test_the_section_check_job_still_refuses_held_out_material(held_out_book):
    """Exam protection's job refusal is unchanged by the landing (main's
    ``test_a_reader_check_over_held_out_material_is_refused_before_any_model_call``
    covers it from an empty section; this one has a check authored before the
    mark, which the job does not hand back)."""

    from learnloop.clock import FrozenClock
    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import IngestRunnerError

    paths, repository, held, _other = held_out_book
    built: list[str] = []
    ctx = SimpleNamespace(
        payload={"extraction_id": "ext_text", "section_id": held}, repo=repository,
        clock=FrozenClock(datetime(2026, 10, 13, tzinfo=UTC)), report=lambda *a, **k: None,
        vault_root=paths.root, job={"id": "job_1", "attempt_count": 1}, cancelled=lambda: False,
        services=SimpleNamespace(quick_check_client=lambda ctx: built.append("client") or object()))
    with pytest.raises(IngestRunnerError) as refused:
        jobs.handle_reader_quick_check(ctx)
    assert refused.value.code == "exam_material" and built == []
