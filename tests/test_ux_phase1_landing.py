"""UX Phase 1 landing on main: the composition checks main's tracks ask of it.

* Exams (main's facet-locks landing: ``held_out_evaluation`` units are exam
  material whatever their member's role, withheld from tutor and models): an
  automatic build never takes exam material as teaching, and the reading step
  never offers it as reading. Both read main's exam predicate
  (``source_retrieval.corpus``), the book's own held-out units included
  before its first study map exists.
* Spend (the owner's 2026-10-13 caps direction): the request gate an
  automatic build installs works with no money limit (no per-operation cap)
  and still stops a cancelled build's requests.
* RW1a's passage-scoped quick check: the landing refused it for a book kept
  on this computer (UX review F1). That per-book choice is retired (owner,
  2026-10-13; reading-hardening part 3), so the two tests below now pin that
  a book still carrying it gets its check like any other.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.content.pipeline import add_source as core
from learnloop.content.pipeline.add_source import AddSourceOptions, add_source, outline_chapters
from learnloop.content.sources.source_outline import build_source_outline, resolve_extraction_id
from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.vault.loader import load_vault

from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, grant_consent, repository, route, set_config, write_book


def _added_book(tmp_path):
    from learnloop.content.pipeline.jobs import DurableIngestJobs

    root = fresh_library(tmp_path)
    grant_consent(root)
    set_config(root, {("ingest", "auto_build"): False})
    repo = repository(root)
    jobs = DurableIngestJobs()
    jobs.bind(repo, root, background=False, clock=CLOCK, services=fake_services())
    item = add_source(load_vault(root), jobs, str(write_book(tmp_path)), AddSourceOptions(), clock=CLOCK)
    set_config(root, {("ingest", "auto_build"): True})
    return root, repo, item["source_id"]


def _hold_out(repo, source_id, label):
    extraction_id = resolve_extraction_id(repo, source_id)
    outline = build_source_outline(repo, extraction_id)
    chapter = next(chapter for chapter in outline_chapters(outline) if chapter.label == label)
    save_unit_selection(repo, extraction_id, [unit.unit_id for unit in outline.units],
                        exam_use_modes={chapter.unit_id: "held_out_evaluation"}, clock=CLOCK)
    return chapter


def test_an_automatic_build_never_takes_a_held_out_unit_as_teaching(tmp_path):
    root, repo, source_id = _added_book(tmp_path)
    before = core.preview_auto_build(root, repo, source_id, whole_book=True, route=route(), now=CLOCK.now())
    assert "2 Conditional probability" in before["chapters"]

    held = _hold_out(repo, source_id, "2 Conditional probability")
    after = core.preview_auto_build(root, repo, source_id, whole_book=True, route=route(), now=CLOCK.now())
    assert "2 Conditional probability" not in after["chapters"]
    assert held.unit_id not in after["chapter_ids"]
    assert after["chapters"] == [label for label in before["chapters"] if label != "2 Conditional probability"]
    # Reading order (no chapter chosen) skips it too.
    vault = load_vault(root)
    choice = core._choose_scope(repo, vault.config, vault, source_id, core._completed_extraction(repo, source_id),
                                chapter_ids=None, start_unit_id=held.unit_id, exclude_job_id=None)
    assert choice is not None and not set(held.unit_ids) & set(choice.unit_ids)
    assert set(held.unit_ids) <= choice.withheld_unit_ids


def test_a_book_that_is_exam_material_builds_nothing(tmp_path, monkeypatch):
    from learnloop.source_retrieval import corpus

    root, repo, source_id = _added_book(tmp_path)
    extraction_id = resolve_extraction_id(repo, source_id)
    monkeypatch.setattr(corpus, "source_exam_exclusions",
                        lambda *_args, **_kwargs: corpus.Exclusions(frozenset({extraction_id}), frozenset()))
    report = core.preview_auto_build(root, repo, source_id, whole_book=True, route=route(), now=CLOCK.now())
    assert report["status"] == "nothing_to_build"


def _reading_book(tmp_path):
    from learnloop.db.repositories import Repository
    from tests.helpers import create_daily_plan_vault
    from tests.test_ux_phase1_round2_review import _section_ids, _seed_book

    paths = create_daily_plan_vault(tmp_path / "vault")
    extraction_id = _seed_book(paths)
    repo = Repository(paths.sqlite_path)
    return paths, repo, extraction_id, _section_ids(repo, extraction_id)


def _section_spans(repo, extraction_id, section_id):
    from learnloop.reader.reader_guidance import extraction_sections

    rows, _blocks, _spans = extraction_sections(repo.load_document_ir(extraction_id))
    return next(list(row["span_ids"]) for row in rows if str(row["id"]) == section_id)


def test_the_reading_step_never_offers_exam_material(tmp_path):
    from learnloop.daily_plan.reading import next_reading_target

    _paths, repo, extraction_id, ids = _reading_book(tmp_path)
    assert next_reading_target(repo).section_id == ids["1-vectors"]
    exam = SimpleNamespace(
        extractions=frozenset(),
        spans=frozenset((extraction_id, span) for span in _section_spans(repo, extraction_id, ids["1-vectors"])),
    )
    assert next_reading_target(repo, exam=exam).section_id == ids["2-matrices"]
    # A whole exam extraction offers no step.
    assert next_reading_target(repo, exam=SimpleNamespace(extractions=frozenset({extraction_id}),
                                                          spans=frozenset())) is None
    # DL1's selection (the switch off) is DL1's exactly: the predicate is not read there.
    assert next_reading_target(repo, from_furthest=False, exam=exam).section_id == ids["contents"]


@pytest.mark.parametrize("readable", [True, False])
def test_todays_plan_reads_mains_exam_predicate_for_the_reading_step(tmp_path, monkeypatch, readable):
    from datetime import UTC, datetime

    import learnloop.clock as clock_module
    from learnloop.source_retrieval import corpus
    from learnloop_sidecar.context import SidecarContext
    from tests.test_ux_phase1_add_source import call

    paths, repo, extraction_id, ids = _reading_book(tmp_path)
    held = frozenset((extraction_id, span) for span in _section_spans(repo, extraction_id, ids["1-vectors"]))

    def exam_exclusions(_vault, _repository):
        if not readable:
            raise RuntimeError("unreadable")
        return corpus.Exclusions(frozenset(), held)

    monkeypatch.setattr(corpus, "exam_exclusions", exam_exclusions)
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: datetime(2026, 10, 12, 9, 0, tzinfo=UTC))
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    plan = call(ctx, "set_plan_minutes", {"minutes": 60})["plan"]
    titles = [row["readingTitle"] for row in plan["projected"] if row["readingTitle"]]
    # Unreadable, the step fails closed: no reading step rather than exam material.
    assert titles == (["2-matrices"] if readable else [])


def test_the_request_gate_works_without_a_money_limit():
    from learnloop.ai.spend import MeteredRequestGate, SpendCancelled

    class Metered:
        provider_name = "openrouter"
        model = "m"

    stopped = {"value": False}
    gate = MeteredRequestGate(limit_usd=None, price_per_token=lambda _provider: 1.0,
                              is_subscription=lambda _client: False, cancelled=lambda: stopped["value"])
    assert gate.limit_usd is None
    admission = gate.admit(Metered(), purpose="chat_request", prompt="x" * 4_000, budget=1_000_000)
    gate.settle(admission, {"cost": 123.0})
    assert gate.spent_usd == 123.0 and gate.refusal is None
    stopped["value"] = True
    with pytest.raises(SpendCancelled):
        gate.admit(Metered(), purpose="chat_request", prompt="x", budget=10)


# -- RW1a's passage check for a book that kept the retired choice -------------
#
# The landing refused RW1a's reconnect quick check for a book kept on this
# computer, when asked and when its job ran. The per-book choice is retired
# (owner, 2026-10-13): a book whose ``source_artifacts.keep_local`` is still
# set gets its check, both ways.


def _carry_retired_keep_local(repo, source_id):
    with repo.connection() as connection:
        connection.execute("UPDATE source_artifacts SET keep_local = 1 WHERE id = ?", (source_id,))
        connection.commit()


def test_a_book_with_the_retired_keep_local_gets_its_passage_check_when_asked(tmp_path, monkeypatch):
    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.db.repositories import Repository
    from learnloop.reader import reader_dialogue as RD
    from learnloop_sidecar.handlers import reader
    from tests.test_sidecar_reader import _init, _rpc
    from tests.test_sidecar_reader import _setup as _rpc_setup

    root_dir = _rpc_setup(tmp_path)
    monkeypatch.setattr(reader, "ready_tutor_qa_provider",
                        lambda vault: ("stub", SimpleNamespace(ready=True), RD.StubReaderClient()))
    monkeypatch.setattr(reader, "ready_canonical_ingest_provider",
                        lambda vault: ("stub", SimpleNamespace(ready=True), object()), raising=False)
    queued: list[dict] = []
    monkeypatch.setattr(DurableIngestJobs, "enqueue_reader_inquiry_check",
                        lambda self, **payload: queued.append(payload) or "batch_1", raising=False)
    asked = _rpc([_init(root_dir), {"jsonrpc": "2.0", "id": 2, "method": "reader.ask",
                                    "params": {"extractionId": "ext1", "spanId": "s1", "question": "Root"}}])[1]["result"]
    _carry_retired_keep_local(Repository(root_dir / "state.sqlite"), "src1")
    responses = _rpc([
        _init(root_dir),
        {"jsonrpc": "2.0", "id": 2, "method": "reader.reconnect_answer",
         "params": {"extractionId": "ext1", "exchangeId": asked["readerAnswerEventId"], "answer": "quick_check",
                    "via": "rail"}},
    ])
    assert "error" not in responses[1], responses[1]
    assert len(queued) == 1


def test_a_queued_passage_check_runs_for_a_book_with_the_retired_keep_local(tmp_path):
    from learnloop.content.pipeline.jobs import handle_reader_quick_check
    from tests.test_reader_reconnect import FakeClient, _ask
    from tests.test_reader_reconnect import _setup as _reconnect_setup
    from tests.test_reader_dialogue import _CLOCK

    vault, repo = _reconnect_setup(tmp_path)
    root = _ask(vault, repo, "Root", selection_span_ids=["s1"], selection_quote_md="A^T = A")
    with repo.connection() as connection:
        source_id = connection.execute(
            "SELECT r.source_id FROM source_extraction_runs e JOIN source_revisions r ON r.id = e.revision_id "
            "WHERE e.id = 'ext1'").fetchone()[0]
    _carry_retired_keep_local(repo, source_id)
    client = FakeClient()
    ctx = SimpleNamespace(
        payload={"extraction_id": "ext1", "scope_kind": "inquiry",
                 "inquiry_root_event_id": root["reader_answer_event_id"], "anchor_span_ids": ["s1"]},
        repo=repo, clock=_CLOCK, report=lambda *a, **k: None, vault_root=vault.root,
        job={"id": "ijob_1"}, cancelled=lambda: False,
        services=SimpleNamespace(quick_check_client=lambda ctx: client),
    )
    result = handle_reader_quick_check(ctx)
    assert result.get("question_id")
    assert len(client.calls) == 1
