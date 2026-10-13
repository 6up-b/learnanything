"""UX Phase 1, usability round 1 (docs/reviews/ux-phase1.md, "Usability round 1").

Fail-first tests for the blockers and majors two personas hit on the Phase 1
path (sessions in the stage's scratchpad, summarised in the review):

* U1 — in a library with months of practice, every new book's questions were
  refused: "Bootstrap synthesis refused: subject '<new book>' has locked
  identities", because the lock check read the whole library, not the subject
  being built (source-ingestion §8.2: "legal only where nothing touched is
  identity-locked"). The branch scoped the check to the subject; on main
  facet locks are gone altogether (owner, 2026-10-12; the facet-locks
  landing), so at the UX landing the per-subject reading was dropped with
  them: no bootstrap is refused for a goal-scoped facet, in this subject or
  another (main's own pin: ``test_source_set_synthesis.py::
  test_a_vault_whose_facets_used_to_be_locked_still_bootstraps``).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis
from learnloop.content.synthesis.source_set_synthesis import create_study_map
from learnloop.content.synthesis.source_unit_inventory import run_unit_inventory
import learnloop.curriculum.curriculum_locks as curriculum_locks
from learnloop.vault.loader import add_subject, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.test_source_inventory import FakeInventoryClient, _block, _ir, _persist, _register_revision
from tests.test_source_set_synthesis import FakeSynthesisClient, _default_payload, _setup

_CLOCK = FrozenClock(datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC))

# The second book's map: the house payload with its own ids, so the two
# subjects share nothing.
_RENAMES = {
    "concept_symmetric_matrix": "concept_sample_space",
    "facet_symmetry_definition": "facet_sample_space_definition",
    "facet_spectral_applicability": "facet_naive_applicability",
    "lo_diagonalize_symmetric": "lo_count_outcomes",
    "bp_select_and_apply_spectral": "bp_count_outcomes",
    "recipe_spectral": "recipe_count_outcomes",
    "pi_identify_symmetry": "pi_identify_sample_space",
    "pi_select_spectral": "pi_select_naive_definition",
}


def _probability_payload(context, _call_count) -> SourceSetSynthesis:
    text = _default_payload(context).model_dump_json()
    for old, new in _RENAMES.items():
        text = text.replace(f'"{old}"', f'"{new}"')
    return SourceSetSynthesis.model_validate(json.loads(text))


def _lock_linear_algebra(root) -> None:
    """An active goal certifies a linear-algebra facet: its identity locks."""

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    goals = read_yaml(paths.goals_path) if paths.goals_path.exists() else {"schema_version": 2, "goals": []}
    goals.setdefault("goals", []).append({
        "id": "goal_lock", "title": "Lock", "status": "active", "priority": 0.5,
        "target_recall": 0.8,
        "facet_scope": {"concepts": [], "facets": ["facet_symmetry_definition"]},
        "due_at": None, "exam": {"enabled": False, "item_count": 20},
        "created_at": "2026-07-13T12:00:00Z", "updated_at": "2026-07-13T12:00:00Z",
    })
    write_yaml(paths.goals_path, goals)


def _add_probability_book(root, repo) -> None:
    add_subject(root, "probability", "Probability", clock=_CLOCK)
    _register_revision(repo, source_id="src_prob", revision_id="rev_prob")
    _persist(repo, _ir([
        ("chapter_counting", "Probability and counting",
         [_block("s1", "A sample space is the set of all possible outcomes of an experiment."),
          _block("s2", "The naive definition counts favourable outcomes over all outcomes.")],
         "sha256:count", 5),
    ]), revision_id="rev_prob", extraction_id="ext_prob")
    run_unit_inventory(repo, "ext_prob", "chapter_counting", role="primary_textbook",
                       profile="combined", client=FakeInventoryClient(), input_budget_tokens=20000, clock=_CLOCK)
    upsert_source_set(root, {
        "id": "set_prob", "subject_id": "probability", "title": "Probability",
        "members": [{"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "primary_textbook",
                     "scope": [{"unit_id": "chapter_counting"}], "priority": 1}],
    }, clock=_CLOCK)


def test_u1_there_is_no_identity_lock_to_read_any_more():
    # Facet locks were removed on main: the read adapter the branch scoped to
    # a subject is gone with them, and nothing refuses a bootstrap for one.
    assert not hasattr(curriculum_locks, "identity_locks")


def test_u1_a_new_books_questions_are_not_refused_for_another_subjects_locks(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True)
    _lock_linear_algebra(root)
    _add_probability_book(root, repo)

    result = create_study_map(
        root, "set_prob", client=FakeSynthesisClient(builder=_probability_payload),
        repository=repo, clock=_CLOCK, apply=True,
    )

    assert result.proposal_id
    assert result.applied is True
    assert "lo_count_outcomes" in load_vault(root).learning_objects


def test_u1_a_subject_with_a_goal_scoped_facet_rebuilds_too(tmp_path):
    # The branch kept refusing a rebuild of the "locked" subject itself; with
    # facet locks removed on main it is built like any other (a reworded
    # facet is a facet version with an undo when its proposal applies).
    root, repo = _setup(tmp_path, with_exam=False)
    create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, apply=True)
    _lock_linear_algebra(root)

    result = create_study_map(root, "set_la", client=FakeSynthesisClient(), repository=repo, clock=_CLOCK, brief={"x": 1})
    assert result.proposal_id is not None and not result.reused


# ---------------------------------------------------------------------------
# U2 — the original PDF follows the learner even without block geometry: a
# text-only (pypdf) extraction knows each passage's page, and the Reader needs
# that to jump to a section, track the reading position and resume it.
# ---------------------------------------------------------------------------


def test_u2_pdf_view_lists_each_passages_page_for_a_text_only_extraction(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth, PageHealth
    from learnloop.ingest.originals import store_original_bytes
    from tests.helpers import create_basic_vault
    from tests.test_sidecar_reader_p3 import _rpc
    from tests.test_source_inventory import _persist as persist_ir
    from tests.test_source_inventory import _register_revision as register

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    toml = root / "learnloop.toml"
    toml.write_text(toml.read_text(encoding="utf-8") + "\n[tutor_qa]\nreader_enabled = true\n", encoding="utf-8")
    repo = Repository(paths.sqlite_path)
    register(repo, source_id="src1", revision_id="rev1")
    # One block per page, no bbox: what the pypdf extractor writes.
    blocks = [
        DocumentBlock.build(span_id=f"s{n}", block_type="Text", text=f"Page {n} text about probability.",
                            ordinal=n, page=page, bbox=None, section_path=[])
        for n, page in ((1, 0), (2, 2), (3, 3))
    ]
    ir = DocumentIR(
        extractor="pypdf", extractor_version="1",
        units=[DocumentUnit(unit_id="u1", label="Contents", ordinal=0, semantic_hash="sha256:a", span_ids=["s1"]),
               DocumentUnit(unit_id="u2", label="1 Counting", ordinal=1, semantic_hash="sha256:b", span_ids=["s2", "s3"])],
        blocks=blocks, assets=[], health=ExtractionHealth(pages=[PageHealth(page=p, flags=[]) for p in (0, 2, 3)]),
    )
    persist_ir(repo, ir, revision_id="rev1", extraction_id="ext1")
    store_original_bytes(root, "sha256:abc", b"%PDF-1.7 fake body")

    view = _rpc(root, [("reader.pdf_view", {"extractionId": "ext1"})])[1]["result"]

    assert view["available"] is True
    assert view["blocks"] == []  # no geometry to paint
    assert view["pageSpans"] == [
        {"spanId": "s1", "page": 0},
        {"spanId": "s2", "page": 2},
        {"spanId": "s3", "page": 3},
    ]


# ---------------------------------------------------------------------------
# U4 — Today's reading step for a new book is never the table of contents,
# and the Reader's reading position (how far into each section) is what moves
# both the plan and the "one chapter ahead" build.
# ---------------------------------------------------------------------------


def _added_book(tmp_path):
    from learnloop.content.sources.source_outline import resolve_extraction_id
    from tests.test_ux_phase1_add_source import _draining_ctx, call
    from tests.ux_phase1_support import fresh_library, grant_consent, write_book

    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    source_id = call(ctx, "add_source", {"sources": [str(write_book(tmp_path))]})["items"][0]["sourceId"]
    return root, ctx, source_id, resolve_extraction_id(ctx.repository, source_id)


def test_u4_the_reading_step_skips_the_table_of_contents(tmp_path):
    from learnloop.daily_plan.reading import next_reading_target

    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)

    target = next_reading_target(ctx.repository)

    assert target is not None and target.extraction_id == extraction_id
    # u1 is "Contents"; u2 is "1 Probability and counting" (Markdown labels are slugs).
    assert target.section_id == "u2"


def test_u4_reading_through_a_section_moves_the_reading_step_on(tmp_path):
    from learnloop.daily_plan.reading import next_reading_target
    from learnloop.reader.reader_guidance import extraction_sections
    from tests.test_ux_phase1_add_source import call

    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    sections, _blocks, _spans = extraction_sections(ctx.repository.load_document_ir(extraction_id))
    chapter_one = next(section for section in sections if section["id"] == "u2")
    count = len(chapter_one["span_ids"])

    call(ctx, "reader.mark_section_progress",
         {"extractionId": extraction_id, "sectionId": "u2", "spansSeen": count, "spanCount": count})

    assert next_reading_target(ctx.repository).section_id == "u3"  # 2 Conditional probability


def test_u4_reaching_a_section_keeps_the_questions_a_chapter_ahead(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core
    from tests.test_ux_phase1_add_source import call

    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    seen: list[str] = []
    monkeypatch.setattr(core, "plan_reading_advance", lambda jobs, source_id, ext, section: seen.append(section))

    call(ctx, "reader.mark_section_progress",
         {"extractionId": extraction_id, "sectionId": "u3", "spansSeen": 1, "spanCount": 4})

    assert seen == ["u3"]


# ---------------------------------------------------------------------------
# U7 — a scanned PDF: one honest line, the one action that can help, and no
# "Try again" that can only fail the same way.
# ---------------------------------------------------------------------------


def _added_scan(tmp_path):
    from tests.test_ux_phase1_add_source import _draining_ctx, call
    from tests.ux_phase1_support import fresh_library, grant_consent, write_pdf

    root = fresh_library(tmp_path)
    grant_consent(root)
    ctx = _draining_ctx(root)
    # Blank pages: no text layer at all, like a scanned handout.
    source_id = call(ctx, "add_source", {"sources": [str(write_pdf(tmp_path, "recitation.pdf"))]})["items"][0]["sourceId"]
    return root, ctx, source_id


def _card(ctx, source_id):
    from tests.test_ux_phase1_add_source import call

    return next(c for c in call(ctx, "get_source_library", {})["sources"] if c["sourceId"] == source_id)


def test_u7_a_scan_offers_text_recognition_when_it_is_installed(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(core, "text_recognition_available", lambda **_kwargs: True)
    _root, ctx, source_id = _added_scan(tmp_path)

    line = _card(ctx, source_id)["statusLine"]

    assert line["text"] == "This PDF is a scan"
    assert line["action"] == {"kind": "text_recognition", "label": "Read it with text recognition"}


def test_u7_a_scan_says_plainly_when_text_recognition_is_not_installed(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core

    monkeypatch.setattr(core, "text_recognition_available", lambda **_kwargs: False)
    _root, ctx, source_id = _added_scan(tmp_path)

    line = _card(ctx, source_id)["statusLine"]

    assert line["text"] == "This PDF is a scan — LearnLoop can show its pages but can't read them yet"
    assert line["action"] is None  # Try again would fail the same way
    assert "install" not in line["text"].lower()
    assert "text recognition" in line["details"]


def test_u7_reading_a_scan_with_text_recognition_also_builds_its_questions(tmp_path, monkeypatch):
    from learnloop.content.pipeline import add_source as core
    from tests.test_ux_phase1_add_source import call

    monkeypatch.setattr(core, "text_recognition_available", lambda **_kwargs: True)
    root, ctx, source_id = _added_scan(tmp_path)
    ctx.ingest_jobs._ensure_worker = lambda: None  # hold the queue: observe what is enqueued

    batch_id = call(ctx, "source_action", {"sourceId": source_id, "action": "text_recognition"})["batchId"]

    jobs = ctx.repository.ingest_jobs_for_batch(batch_id)
    assert [job["job_type"] for job in jobs] == ["import", core.AUTO_STUDY_MAP_JOB]
    assert jobs[0]["payload"]["pdf_config"] == {"engine": "marker", "force_ocr": True}


# ---------------------------------------------------------------------------
# U8 — "Questions ready … · Undo" sent the learner looking for questions that
# come as they read; the line now says where they come from, and Undo lives
# in details (one quiet line, no surprise verb).
# ---------------------------------------------------------------------------


def test_u8_a_built_book_says_its_questions_come_as_you_read(tmp_path):
    from learnloop.content.pipeline.add_source import source_status_line

    root, ctx, source_id, _extraction_id = _added_book(tmp_path)

    line = source_status_line(ctx.repository, load_vault(root), source_id)

    assert line["text"] == "Questions for Ch. 1–2 come up as you read"
    assert line["action"] is None


# ---------------------------------------------------------------------------
# U10 — a new book's subject never becomes the default subject of the
# learner's other screens: the subjects a library practises come first.
# ---------------------------------------------------------------------------


def test_u10_the_practised_subject_comes_before_a_new_books_subject(tmp_path):
    from learnloop_sidecar.context import vault_summary
    from tests.helpers import create_basic_vault

    root = tmp_path / "vault"
    create_basic_vault(root)
    vault = load_vault(root)
    practised = sorted(vault.subjects)
    assert practised and any(vault.subjects_for_item(item) for item in vault.practice_items.values())
    # A new book filed under a subject that sorts first and has nothing to practise.
    add_subject(root, "a-diagnostic-driven-multi-agent-socratic-teaching-system", "A diagnostic-driven tutor", clock=_CLOCK)

    summary = vault_summary(load_vault(root))

    assert summary["subjects"][0] == practised[0]
    assert summary["subjects"][-1] == "a-diagnostic-driven-multi-agent-socratic-teaching-system"
    assert summary["subjectTitles"][-1] == {
        "id": "a-diagnostic-driven-multi-agent-socratic-teaching-system", "title": "A diagnostic-driven tutor",
    }


def test_u10_a_book_card_names_its_subject_by_title(tmp_path):
    root, ctx, source_id, _extraction_id = _added_book(tmp_path)

    card = _card(ctx, source_id)

    subject = load_vault(root).subjects[card["subjectId"]]
    assert card["subjectTitle"] == subject.metadata.title
    assert card["subjectTitle"] != card["subjectId"]


# ---------------------------------------------------------------------------
# A link still being fetched has a readable name on the shelf, not its URL
# (usability round 1, minor: the video card's title was the raw URL).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "title"),
    [
        ("https://www.youtube.com/watch?v=kYB8IZa5AuE", "YouTube video"),
        ("https://arxiv.org/abs/1706.03762", "arXiv 1706.03762"),
        ("https://example.org/notes/bayes.html", "example.org/notes/bayes.html"),
    ],
)
def test_a_link_being_fetched_has_a_readable_name(tmp_path, source, title):
    from learnloop.content.pipeline.add_source import AddSourceOptions, add_source, pending_adds
    from learnloop.content.pipeline.runner import IngestRunnerError
    from tests.test_ux_phase1_auto_build import _jobs
    from tests.ux_phase1_support import fake_services, fresh_library

    def unreachable(source, category, ctx):
        raise IngestRunnerError("network unreachable", code="fetch_failed", retryable=True)

    root = fresh_library(tmp_path)
    repo, jobs = _jobs(root, fake_services(fetch=unreachable))
    add_source(load_vault(root), jobs, source, AddSourceOptions(), clock=_CLOCK)

    assert [entry["title"] for entry in pending_adds(repo)] == [title]


def test_u4_the_reading_step_continues_where_the_learner_left_off(tmp_path):
    """A learner who jumped to chapter 2 and read some of it continues there,
    not at the chapter they skipped (Codex reviewer: "Continue §1.2 where you
    stopped")."""

    from learnloop.daily_plan.reading import next_reading_target
    from tests.test_ux_phase1_add_source import call

    _root, ctx, _source_id, extraction_id = _added_book(tmp_path)
    # u3 is "2 Conditional probability"; the learner read part of it.
    call(ctx, "reader.mark_section_progress",
         {"extractionId": extraction_id, "sectionId": "u3", "spansSeen": 1, "spanCount": 3})

    assert next_reading_target(ctx.repository).section_id == "u3"
