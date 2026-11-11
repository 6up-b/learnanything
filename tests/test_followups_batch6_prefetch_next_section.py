"""Follow-ups batch 6 (E): the section trigger's next section follows RW7b's reading path.

RW5d P5's ``section`` trigger prebuilt for the next section in book order (deviation 7: RW7b's
path was not consulted). With an active reading path for the reading (``reading_paths.plan_path``
followed: judged for the learner's current state), the next section is the next one the path
plans (core or prerequisite, not held out); otherwise book order, as before.

The path itself is ``plan_path``'s (pinned by tests/test_plan_follows_path.py); here it is a
constructed ``PlanPath`` so each state is exact. Fakes only: the judge and the author.
"""

from __future__ import annotations

import pytest

from learnloop.figures import power as P
from learnloop.figures import prefetch as PF
from learnloop.figures import service as FS
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.source_retrieval import reading_paths as RP
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import set_config, upsert_source_set
from tests.figures_prefetch_helpers import JudgeFake, decisions, env_for, make_vault
from tests.source_inventory_helpers import _persist

THREE = "ext_three"
SECTIONS = (
    ("t1", "1 Waves", (("r1", "SectionHeader", "1 Waves"), ("r2", "Equation", "v = f \\lambda"))),
    ("t2", "2 Interference", (("r3", "SectionHeader", "2 Interference"), ("r4", "Equation", "I = I_1 + I_2"))),
    ("t3", "3 Damping", (("r5", "SectionHeader", "3 Damping"), ("r6", "Equation", "A(t) = A_0 e^{-\\gamma t}"))),
)


@pytest.fixture(autouse=True)
def mains():
    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    yield
    P.set_power_reader(None)


def _three_sections(tmp_path, *, paths_on: bool = True):
    paths, repository, _vault = make_vault(tmp_path)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, display_title, current_revision_id, "
            "reader_enabled, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("src_three", "pdf", "file:///src_three.pdf", "Three Sections", "rev_three", 1,
             "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"))
        connection.execute(
            "INSERT INTO source_revisions(id, source_id, asset_hash, original_uri, created_at) VALUES (?,?,?,?,?)",
            ("rev_three", "src_three", "sha256:src_three", None, "2026-01-01T00:00:00Z"))
        connection.commit()
    blocks, units, ordinal = [], [], 0
    for index, (unit_id, label, spec) in enumerate(SECTIONS):
        for span, kind, text in spec:
            ordinal += 1
            blocks.append(DocumentBlock.build(span_id=span, block_type=kind, text=text, ordinal=ordinal, page=1,
                                              bbox=[72.0, 40.0 * ordinal, 540.0, 40.0 * ordinal + 30],
                                              section_path=["/page/1/SectionHeader/1"],
                                              extractor_block_id=f"/page/1/{kind}/{ordinal}"))
        units.append(DocumentUnit(unit_id=unit_id, label=label, ordinal=index, semantic_hash=f"sha256:{unit_id}",
                                  page_start=1, page_end=1, span_ids=[span for span, _kind, _text in spec]))
    _persist(repository, DocumentIR(extractor="marker", extractor_version="1", units=units, blocks=blocks, assets=[],
                                    health=ExtractionHealth()), revision_id="rev_three", extraction_id=THREE)
    upsert_source_set(paths.root, {
        "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
        "members": [
            {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
            {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
            {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"},
            {"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "primary_textbook"},
            {"source_id": "src_three", "revision_id": "rev_three", "default_role": "primary_textbook"},
        ],
    })
    set_config(paths, "reading_paths", enabled=paths_on)
    return paths, repository, load_vault(paths.root)


def _path(status: str = "path", **labels: str) -> RP.PlanPath:
    refs = tuple(RP.PlanSectionRef(section_id=section, label=label, judgment_row_id=f"rps_{section}")
                 for section, label in labels.items())
    return RP.PlanPath(extraction_id=THREE, status=status, depth="learn_to_use_it", state_key="k",
                       fresh=status == "path", sections=refs if status == "path" else ())


def _reads(monkeypatch, path: RP.PlanPath | Exception) -> list[tuple]:
    calls: list[tuple] = []

    def plan_path(vault, repository, extraction_id):
        calls.append((extraction_id,))
        if isinstance(path, Exception):
            raise path
        return path

    monkeypatch.setattr(RP, "plan_path", plan_path)
    return calls


def _section_pass(vault, repository, judge=None):
    judge = judge or JudgeFake()
    result = PF.run_trigger(env_for(vault, repository, judge=judge),
                            PF.Trigger("section", f"{THREE}:t1", extraction_id=THREE, section_id="t1"))
    return judge, result


def test_without_a_path_the_next_section_is_book_order(tmp_path, monkeypatch):
    _paths, repository, vault = _three_sections(tmp_path)
    calls = _reads(monkeypatch, _path("not_judged"))
    assert PF.next_section(env_for(vault, repository), THREE, "t1") == "t2"
    assert calls == [(THREE,)]


def test_an_active_path_skips_what_it_does_not_plan(tmp_path, monkeypatch):
    _paths, repository, vault = _three_sections(tmp_path)
    _reads(monkeypatch, _path(t1="core", t2="enrichment", t3="core"))
    judge, _result = _section_pass(vault, repository)
    assert judge.contexts[0]["blocks"][0]["text"] == "3 Damping"
    (row,) = decisions(repository)
    assert row["trigger_ref"] == f"{THREE}:t3"
    # A prerequisite is planned too; "skip it" and "already shown" are not.
    _reads(monkeypatch, _path(t1="core", t2="prerequisite", t3="core"))
    assert PF.next_section(env_for(vault, repository), THREE, "t1") == "t2"
    _reads(monkeypatch, _path(t1="core", t2="already_shown", t3="skipped"))
    assert PF.next_section(env_for(vault, repository), THREE, "t1") is None


def test_a_stale_or_unjudged_path_keeps_book_order(tmp_path, monkeypatch):
    _paths, repository, vault = _three_sections(tmp_path)
    for status in ("stale", "not_judged", "no_depth"):
        _reads(monkeypatch, _path(status))
        assert PF.next_section(env_for(vault, repository), THREE, "t1") == "t2", status


def test_a_path_held_out_for_an_exam_plans_no_next_section(tmp_path, monkeypatch):
    _paths, repository, vault = _three_sections(tmp_path)
    _reads(monkeypatch, _path("withheld"))
    judge, result = _section_pass(vault, repository)
    assert judge.calls == 0 and decisions(repository) == [] and result.status == "ok"


def test_the_path_never_opens_a_held_out_section(tmp_path, monkeypatch):
    _paths, repository, vault = _three_sections(tmp_path)
    _reads(monkeypatch, _path(t1="core", t2="core", t3="core"))
    real = FS.withheld_message
    monkeypatch.setattr(FS, "withheld_message",
                        lambda v, r, e, found: "held out" if "r3" in set(found) else real(v, r, e, found))
    assert PF.next_section(env_for(vault, repository), THREE, "t1") == "t3"


def test_reading_paths_off_or_an_unreadable_path_keeps_book_order(tmp_path, monkeypatch):
    _paths, repository, vault = _three_sections(tmp_path, paths_on=False)
    calls = _reads(monkeypatch, _path(t1="core", t2="enrichment", t3="core"))
    assert PF.next_section(env_for(vault, repository), THREE, "t1") == "t2" and calls == []
    _paths, repository, vault = _three_sections(tmp_path / "on")
    _reads(monkeypatch, RuntimeError("path store unreadable"))
    assert PF.next_section(env_for(vault, repository), THREE, "t1") == "t2"
