"""Accepted video chapters feed section coverage (owner decision 2026-11-23; spec §7.9: an accepted chapter "can"
feed it through the coverage correction). Accepting a judged chapter makes its time range coverage of the LOs it is
tagged with: one learner row per transcript section wholly inside the range, with a ledger verdict naming the chapter,
once per chapter. "Not this" feeds nothing; the learner's own correction stands and corrects a wrong acceptance; a
row written against an earlier transcript no longer stands. No model is called."""
from __future__ import annotations

import json

from learnloop.source_retrieval import section_coverage as SC
from learnloop.source_retrieval import video_chapters as VC
from learnloop.vault.loader import load_vault
from tests.reader_rd10_helpers import VIDEO, build_video_vault
from tests.reading_path_fixtures import call, context


def _chapter(repository, chapter_id: str, t0: float, t1: float, los: list[str], title: str = "eigenvalues") -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO video_chapters (chapter_id, extraction_id, source_id, t0, t1, title, lo_ids_json, state, "
            "judgment_ref, suggested_at) VALUES (?, ?, 'src_vid', ?, ?, ?, ?, 'suggested', 'jl_chapters', "
            "'2026-11-23T09:00:00Z')", (chapter_id, VIDEO, t0, t1, title, json.dumps(los)))
        connection.commit()


def _rows(repository, where: str = "", params: tuple = ()) -> list[dict]:
    with repository.connection() as connection:
        cursor = connection.execute(f"SELECT * FROM section_coverage WHERE extraction_id = ? {where} ORDER BY rowid",
                                    (VIDEO, *params))
        names = [column[0] for column in cursor.description]
        return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def _standing(paths, repository, lo_id: str) -> dict:
    vault = load_vault(paths.root)
    return SC.standing(vault, repository, SC.Library(vault, repository), [lo_id]).get(lo_id, {})


def test_accepting_a_chapter_writes_its_range_as_coverage_of_its_topics_once(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    _chapter(repository, "vc_eigen", 20.0, 40.0, ["lo_eigen"])
    ctx = context(paths.root)
    call(ctx, "chapters.decide", {"chapter_id": "vc_eigen", "decision": "accept"})
    [row] = _rows(repository)
    assert (row["section_id"], row["learning_object_id"], row["origin"], row["learner_override"]) == (
        "v_eigen", "lo_eigen", "learner", "is_about")
    assert row["state_key"] == "chapter:vc_eigen" and row["prompt_version"] == SC.CHAPTER_VERSION
    with repository.connection() as connection:
        verdict, judge, rationale = connection.execute(
            "SELECT verdict, judge, rationale FROM judgment_ledger WHERE id = ?", (row["ledger_id"],)).fetchone()
    assert (verdict, judge) == ("is_about", "learner_card")
    said = json.loads(rationale)
    assert {key: said.get(key) for key in ("source", "chapter_id", "chapter_judgment_ref")} == {
        "source": "accepted_chapter", "chapter_id": "vc_eigen", "chapter_judgment_ref": "jl_chapters"}
    entry = _standing(paths, repository, "lo_eigen")[(VIDEO, "v_eigen")]
    assert entry.chapter_id == "vc_eigen" and entry.treatment is None and entry.by == "learner"
    # Once: deciding it again answers the stored decision and writes nothing.
    call(ctx, "chapters.decide", {"chapter_id": "vc_eigen", "decision": "accept"})
    assert len(_rows(repository)) == 1


def test_not_this_feeds_nothing(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    _chapter(repository, "vc_eigen", 20.0, 40.0, ["lo_eigen"])
    call(context(paths.root), "chapters.decide", {"chapter_id": "vc_eigen", "decision": "dismiss"})
    assert _rows(repository) == []


def test_only_sections_wholly_inside_the_range_are_covered(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    # 15 s to 60 s: half the introduction (0-20 s), all of eigenvalues (20-40 s) and determinants (40-60 s).
    _chapter(repository, "vc_wide", 15.0, 60.0, ["lo_eigen", "lo_det"])
    VC.decide(load_vault(paths.root), repository, "vc_wide", "accept")
    assert sorted((row["section_id"], row["learning_object_id"]) for row in _rows(repository)) == [
        ("v_det", "lo_det"), ("v_det", "lo_eigen"), ("v_eigen", "lo_det"), ("v_eigen", "lo_eigen")]


def test_the_learners_own_correction_stands_and_corrects_a_wrong_acceptance(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    vault = load_vault(paths.root)
    # An earlier "not about this" on the determinants section keeps it: the chapter writes only the other section.
    SC.correct(vault, repository, VIDEO, "v_det", "lo_det", "not_about")
    _chapter(repository, "vc_both", 20.0, 60.0, ["lo_det"])
    VC.decide(vault, repository, "vc_both", "accept")
    written = _rows(repository, "AND prompt_version = ?", (SC.CHAPTER_VERSION,))
    assert [(row["section_id"], row["learning_object_id"]) for row in written] == [("v_eigen", "lo_det")]
    assert _standing(paths, repository, "lo_det")[(VIDEO, "v_det")].treatment == "not_about"
    # Decisions are final: a wrong acceptance is corrected by the coverage correction, which stands over it.
    SC.correct(vault, repository, VIDEO, "v_eigen", "lo_det", "not_about")
    entry = _standing(paths, repository, "lo_det")[(VIDEO, "v_eigen")]
    assert entry.treatment == "not_about" and entry.chapter_id is None


def test_a_chapters_row_no_longer_stands_once_the_transcript_changed(tmp_path):
    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    _chapter(repository, "vc_eigen", 20.0, 40.0, ["lo_eigen"])
    VC.decide(load_vault(paths.root), repository, "vc_eigen", "accept")
    assert (VIDEO, "v_eigen") in _standing(paths, repository, "lo_eigen")
    from learnloop.ingest.ir import DocumentBlock

    ir = repository.load_document_ir(VIDEO)
    blocks = [DocumentBlock.build(span_id=block.span_id, block_type=block.block_type, ordinal=block.ordinal,
                                  section_path=list(block.section_path), text="Eigenvalues, said again in other words.")
              .model_copy(update={"extractor_block_id": block.extractor_block_id}) if block.span_id == "c3"
              else block for block in ir.blocks]
    repository.persist_document_ir(VIDEO, ir.model_copy(update={"blocks": blocks}))
    assert (VIDEO, "v_eigen") not in _standing(paths, repository, "lo_eigen")
    # A learner's own correction, by contrast, stands across a change (unchanged rule).
    SC.correct(load_vault(paths.root), repository, VIDEO, "v_det", "lo_det", "is_about")
    assert (VIDEO, "v_det") in _standing(paths, repository, "lo_det")


def test_with_the_curriculum_off_accepting_writes_no_coverage(tmp_path):
    from tests.ux_phase1_support import set_config

    paths, repository = build_video_vault(tmp_path / "vault", cover=False)
    set_config(paths.root, {("curriculum", "enabled"): False})
    _chapter(repository, "vc_eigen", 20.0, 40.0, ["lo_eigen"])
    assert VC.decide(load_vault(paths.root), repository, "vc_eigen", "accept")["state"] == "accepted"
    assert _rows(repository) == []


def _relabel(repository, span_id: str, text: str) -> None:
    from learnloop.ingest.ir import DocumentBlock

    ir = repository.load_document_ir(VIDEO)
    blocks = [DocumentBlock.build(span_id=block.span_id, block_type=block.block_type, ordinal=block.ordinal,
                                  section_path=list(block.section_path), text=text)
              .model_copy(update={"extractor_block_id": block.extractor_block_id}) if block.span_id == span_id
              else block for block in ir.blocks]
    repository.persist_document_ir(VIDEO, ir.model_copy(update={"blocks": blocks}))


def test_the_goal_lens_reads_an_accepted_chapters_range_as_a_place_the_topic_is_taught(tmp_path):
    from tests.goal_lens_helpers import lens_context, levels, scoped_goal, summary

    paths, repository = build_video_vault(tmp_path / "vault")
    goal_id = scoped_goal(paths, repository)
    ctx = lens_context(paths)
    before = levels(ctx, goal_id, VIDEO)
    # The coverage judge read the introduction as not about the goal's topics: skippable.
    assert summary(before["v_intro"])[:2] == ("skippable", "mapped")
    # The learner accepts a chapter over the introduction tagged with the goal's topic: their act stands over the
    # judge's row, as their "also about" does, and the section is a place the topic is taught again.
    _chapter(repository, "vc_intro", 0.0, 20.0, ["lo_eigen"])
    call(ctx, "chapters.decide", {"chapter_id": "vc_intro", "decision": "accept"})
    after = levels(ctx, goal_id, VIDEO)
    assert summary(after["v_intro"]) == ("supporting", "mapped", "chapter_about", ["lo_eigen"])
    assert after["v_intro"]["coverageLine"].startswith("A chapter you accepted links this section to “")
    # Every other section's level is unchanged: a chapter only adds a place the topic is taught.
    assert {key: summary(value) for key, value in after.items() if key != "v_intro"} == {
        key: summary(value) for key, value in before.items() if key != "v_intro"}
    # The transcript changed under the chapter: what it said is unknown now, partial, never skippable.
    _relabel(repository, "c1", "Welcome back; this introduction was recorded again.")
    stale = levels(ctx, goal_id, VIDEO)["v_intro"]
    assert stale["level"] == "partial" and stale["reasonKey"] == "partial_unsettled"
