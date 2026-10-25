"""E0 corpus: copies, policy before encoding, units, windows, invalidation (spec §4)."""
from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.pins import token_estimate
from tests.e0_fakes import EXAM, LONG_BLOCK, build_e0_vault


from tests.e0_fakes import verified_prices  # noqa: F401 - the fixture below

#: Every metered pin priced as verified (E0 admission refuses unverified prices; fix round 4).
pytestmark = pytest.mark.usefixtures("verified_prices")


def _snapshot(paths):
    return C.build_snapshot(C.open_copy(paths.root))


def test_exam_and_solution_material_never_enter_a_unit(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    texts = "\n".join(unit.text for unit in snapshot.units)
    assert EXAM not in texts
    assert "Solution: apply linearity" not in texts
    assert not any(unit.extraction_id == "ext_exam" for unit in snapshot.units)
    reasons = set(snapshot.policy.withheld.values())
    assert "exam_or_held_out" in reasons and "solution" in reasons


def test_a_withheld_block_is_a_hard_boundary_for_units_and_windows(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    exercise = next(unit for unit in snapshot.units if unit.text.startswith("Exercise 2.1"))
    example = next(unit for unit in snapshot.units if unit.text.startswith("Example 2.2"))
    # The solution between them is withheld: they sit in different policy segments,
    # so no window joins them.
    assert exercise.segment != example.segment
    for window in snapshot.windows:
        members = {snapshot.unit(unit_id).segment for unit_id in window.unit_ids}
        assert len(members) == 1


def test_units_are_deterministic_and_keep_original_offsets(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    first, second = _snapshot(paths), _snapshot(paths)
    assert [unit.unit_id for unit in first.units] == [unit.unit_id for unit in second.units]
    assert [window.window_id for window in first.windows] == [window.window_id for window in second.windows]
    pieces = [unit for unit in first.units if unit.kind == "split"]
    assert len(pieces) >= 2
    span = pieces[0].members[0].span_id
    covered = sorted((member.start, member.end) for unit in pieces for member in unit.members if member.span_id == span)
    assert covered[0][0] == 0 and covered[-1][1] == len(LONG_BLOCK)
    assert all(left[1] == right[0] for left, right in zip(covered, covered[1:]))
    assert "".join(LONG_BLOCK[start:end] for start, end in covered) == LONG_BLOCK
    assert all(unit.tokens <= pins.UNIT_MAX_TOKENS for unit in first.units)


def test_split_offsets_cover_text_exactly_and_respect_the_bound():
    text = "Alpha beta. " * 900 + "tail without boundary " * 50
    pieces = C.split_offsets(text, 200)
    assert pieces[0][0] == 0 and pieces[-1][1] == len(text)
    assert all(a[1] == b[0] for a, b in zip(pieces, pieces[1:]))
    assert all(token_estimate(text[start:end]) <= 200 for start, end in pieces)
    assert C.split_offsets(text, 200) == pieces


def test_a_bare_equation_attaches_to_its_explanatory_text(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    proof = next(unit for unit in snapshot.units if unit.text.startswith("Proof."))
    assert proof.kind == "equation_attached"
    assert proof.text.endswith("$$0 = 0 + 0' = 0'$$")
    assert len(proof.members) == 2


def test_transcript_captions_merge_toward_the_target_within_one_sequence(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    captions = [unit for unit in snapshot.units if unit.extraction_id == "ext_talk"]
    assert all(unit.kind == "captions" for unit in captions)
    assert len(captions) < 12  # merged
    low, high = pins.CAPTION_TARGET_TOKENS
    assert all(unit.tokens <= high for unit in captions)
    assert all(unit.tokens >= low for unit in captions[:-1])
    assert sum(len(unit.members) for unit in captions) == 12


def test_numbered_environments_open_their_own_units(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    definition = next(unit for unit in snapshot.units if unit.text.startswith("Definition 1.1"))
    theorem = next(unit for unit in snapshot.units if unit.text.startswith("Theorem 1.2"))
    assert definition.unit_id != theorem.unit_id
    assert len(definition.members) == 1 and len(theorem.members) == 1


def test_windows_partition_units_within_the_token_bound(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    C.assert_partition(snapshot.units, snapshot.windows)
    assert all(window.tokens <= pins.WINDOW_TOKENS for window in snapshot.windows)
    small = C.build_windows(snapshot.units, window_tokens=1100)
    C.assert_partition(snapshot.units, small)
    assert all(window.tokens <= 1100 for window in small)


def test_whole_source_windows_only_when_the_whole_segment_fits(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    assert C.whole_segment_windows(snapshot.units, limit_tokens=10) == []
    big = C.whole_segment_windows(snapshot.units, limit_tokens=10**6)
    segments = {(unit.extraction_id, unit.segment) for unit in snapshot.units}
    assert len(big) == len(segments)


def test_references_resolve_to_units_across_sections(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    user = next(unit for unit in snapshot.units if unit.text.startswith("By Theorem 1.2"))
    theorem = next(unit for unit in snapshot.units if unit.text.startswith("Theorem 1.2"))
    assert theorem.unit_id in snapshot.dependencies[user.unit_id]["targets"]


def test_a_later_held_out_mark_invalidates_dependent_artifacts(tmp_path):
    paths, repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    artifacts = {window.window_id: snapshot.window_dependency(window) for window in snapshot.windows}
    artifacts |= {unit.unit_id: snapshot.unit_dependency(unit) for unit in snapshot.units}
    assert C.invalidate(artifacts, snapshot.policy) == {}
    save_unit_selection(repository, "ext_book", ["ext_book_u0", "ext_book_u1"],
                        exam_use_modes={"ext_book_u0": "held_out_evaluation"})
    later = _snapshot(paths)
    stale = C.invalidate(artifacts, later.policy)
    chapter_one = [unit.unit_id for unit in snapshot.units if unit.section and unit.section[0].startswith("Chapter 1")]
    assert chapter_one and all(unit_id in stale for unit_id in chapter_one)
    assert all(any(reason.startswith("now_withheld") for reason in stale[unit_id]) for unit_id in chapter_one)
    talk = next(unit.unit_id for unit in snapshot.units if unit.extraction_id == "ext_talk")
    assert talk not in stale
    assert not any(unit.section and unit.section[0].startswith("Chapter 1") for unit in later.units)


def test_re_extraction_invalidates_by_fingerprint(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    unit = snapshot.units[0]
    dependency = snapshot.unit_dependency(unit)
    moved = C.ArtifactDependency(dependency.extraction_id, (dependency.extraction_fingerprint[0] + 1,
                                                            dependency.extraction_fingerprint[1]),
                                 dependency.keys, dependency.policy_fingerprint)
    assert C.stale_reasons(moved, snapshot.policy) == ["re_extracted"]
    gone = C.ArtifactDependency("ext_missing", (1, 1), dependency.keys, dependency.policy_fingerprint)
    assert "extraction_not_current" in C.stale_reasons(gone, snapshot.policy)


def test_policy_failure_fails_closed(tmp_path, monkeypatch):
    paths, _repository = build_e0_vault(tmp_path)

    def broken(*_args, **_kwargs):
        raise RuntimeError("unresolvable mark")

    monkeypatch.setattr(C, "model_reader_withheld", broken)
    with pytest.raises(C.PolicyUnavailable):
        _snapshot(paths)


def test_open_copy_is_read_only_and_never_migrates(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    before = Path(paths.sqlite_path).read_bytes()
    handle = C.open_copy(paths.root)
    with pytest.raises(Exception):
        with handle.repository.connection() as connection:
            connection.execute("CREATE TABLE e0_probe(x)")
    C.build_snapshot(handle)
    assert Path(paths.sqlite_path).read_bytes() == before


def test_prepare_copies_uses_the_backup_api_under_fixtures_local_only(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    with pytest.raises(ValueError, match="fixtures-local"):
        C.prepare_copies([paths.root], tmp_path / "elsewhere", label="x")
    forbidden = tmp_path / "arxiv_v2"
    forbidden.mkdir()
    (forbidden / "learnloop.toml").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="arxiv_v2"):
        C.prepare_copies([forbidden], tmp_path / "fixtures-local" / "copies", label="x")
    copies = C.prepare_copies([paths.root], tmp_path / "fixtures-local" / "copies", label="t")
    copied = Path(copies[0]["copy"])
    assert copies[0]["databases"] >= 1
    with connect(copied / "state.sqlite", read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_document_blocks").fetchone()[0] > 0
    assert C.build_snapshot(C.open_copy(copied)).inventory()["units"] == _snapshot(paths).inventory()["units"]


def test_families_group_editions_and_reservation_is_fixed_before_questions(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    snapshot = _snapshot(paths)
    assert len(set(snapshot.family_of_source.values())) == 3
    assert set(snapshot.family_status.values()) == {"development"}
    reserved = C.reserve_families(["a", "b", "c", "d"], share=0.5)
    assert sorted(reserved.values()).count("reserved") == 2
    assert reserved == C.reserve_families(["d", "c", "b", "a"], share=0.5)


def test_inventory_is_aggregate_only(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    inventory = _snapshot(paths).inventory()
    text = str(inventory)
    assert "Linear Algebra Book" not in text and "Definition 1.1" not in text and "ext_book" not in text
    assert inventory["units"] > 0 and inventory["policy"]["withheld"]


def test_wal_copies_are_converted_and_a_wal_copy_is_refused(tmp_path):
    import sqlite3

    paths, _repository = build_e0_vault(tmp_path)
    with sqlite3.connect(paths.sqlite_path) as raw:
        assert raw.execute("PRAGMA journal_mode = WAL").fetchone()[0] == "wal"
    assert C.is_wal(Path(paths.sqlite_path))
    with pytest.raises(ValueError, match="WAL"):
        C.open_copy(paths.root)
    copies = C.prepare_copies([paths.root], tmp_path / "fixtures-local" / "copies", label="w")
    copied = Path(copies[0]["copy"])
    assert copies[0]["journal_mode"] == "delete" and not C.is_wal(copied / "state.sqlite")
    assert not (copied / "state.sqlite-wal").exists() and not (copied / "state.sqlite-shm").exists()
    from learnloop.experiments.contextual_embeddings.runner import tree_digest

    before = tree_digest(copied)
    C.build_snapshot(C.open_copy(copied))
    assert tree_digest(copied) == before
