"""Reader workbench RW3b: cue value and the density control (spec_reader_workbench_v1 §6.2 item 4; G42).

Cues are ordered by the stored ``p_open``, then the judge's pick rank, Guide
first on ties; a target already given a mark in an earlier section ranks after
every target not yet given one; the order uses no hand-set weight (any
monotone rescaling of ``p_open`` gives the same order); the density control
changes only how many show; ``cues.value_order_enabled`` off gives the
judge's order, the Guide's first. Targets are injected here so ``p_open`` is
controlled; ``test_passage_links.py`` reads the real ones. Fakes only.
"""

from __future__ import annotations

import pytest

from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.source_retrieval import passage_cues as PC
from tests.passage_cue_fakes import build_cue_vault, guide_cue, loaded, seed_link, set_config, target


def _setup(tmp_path, monkeypatch, targets, links, *, density: str = "more", guide: list[str] | None = None,
           config: dict | None = None):
    paths, repository, spans = build_cue_vault(tmp_path / "v", misconception=False)
    if guide:
        guide_cue(paths, repository, guide)
    set_config(paths, "cues", density=density, holdout_rate=0.0, **(config or {}))
    for entry in links:
        seed_link(repository, *entry[:2], **(entry[2] if len(entry) > 2 else {}))
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: list(targets))
    vault = loaded(paths)
    plan = build_guide_plan(vault, repository, extraction_id="ext_text")
    return PC.merged_cues(vault, repository, extraction_id="ext_text", plan=plan), spans


def _order(cues, section: str | None = None) -> list[tuple[str, str]]:
    marks = [mark for mark in cues["marks"] if section is None or mark["section_id"] == section]
    marks.sort(key=lambda mark: (mark["section_id"], mark["section_rank"]))
    return [(mark["found_by"], mark["span_id"]) for mark in marks]


def test_cues_in_a_section_are_ordered_by_p_open_then_pick_rank_with_the_guide_first_on_ties(tmp_path, monkeypatch):
    high, mid, low, tie = (target("hypothesis", "h_high", p_open=0.9), target("hypothesis", "h_mid", p_open=0.6),
                           target("hypothesis", "h_low", p_open=0.2), target("misconception", "m_tie", p_open=1.0,
                                                                             source="misconception_lifecycle"))
    cues, _spans = _setup(tmp_path, monkeypatch, [high, mid, low, tie],
                          [(low, "t2"), (high, "t3", {"pick_rank": 2}), (mid, "t1"), (tie, "t3", {"pick_rank": 1})],
                          guide=["t2"])
    # t2 has the Guide's mark (Guide first on a passage); t3's best pick is the tie's.
    ch5 = _order(cues, "ch5")
    assert ch5[0] == ("guide", "t2")
    assert [mark["p_open"] for mark in sorted(
        [m for m in cues["marks"] if m["section_id"] == "ch5"], key=lambda m: m["section_rank"])] == [1.0, 1.0, 0.6]
    by_span = {mark["span_id"]: mark for mark in cues["marks"]}
    assert by_span["t3"]["target_id"] == "misconception:m_tie" and by_span["t3"]["p_open_source"] == "misconception_lifecycle"
    assert by_span["t2"]["p_open_source"] == "error_lifecycle"


def test_the_order_uses_no_hand_set_weight_a_monotone_rescaling_keeps_it(tmp_path, monkeypatch):
    raw = [0.95, 0.5, 0.3, 0.05]
    spans = ["t1", "t2", "t3", "t5"]

    def run(path, transform):
        targets = [target("hypothesis", f"h{index}", p_open=transform(value)) for index, value in enumerate(raw)]
        cues, _ = _setup(path, monkeypatch, targets, [(t, span) for t, span in zip(targets, spans)])
        return [mark["target_id"] for mark in sorted(cues["marks"], key=lambda m: (m["section_id"], m["section_rank"]))]

    assert run(tmp_path / "a", lambda p: p) == run(tmp_path / "b", lambda p: p ** 3)


@pytest.mark.parametrize("density,shown", [("off", 0), ("fewer", 1), ("normal", 2), ("more", 3)])
def test_the_density_control_changes_only_how_many_show(tmp_path, monkeypatch, density, shown):
    targets = [target("hypothesis", f"h{index}", p_open=p) for index, p in enumerate((0.9, 0.5, 0.1))]
    cues, _ = _setup(tmp_path, monkeypatch, targets, [(t, span) for t, span in zip(targets, ("t3", "t1", "t2"))],
                     density=density)
    order = [mark["target_id"] for mark in sorted(cues["marks"], key=lambda m: m["section_rank"])]
    assert order == ["hypothesis:h0", "hypothesis:h1", "hypothesis:h2"][:shown]
    assert [entry["reason"] for entry in cues["discovery"]["suppressed"]] == ["density"] * (3 - shown)
    assert cues["withheld"]["density"] == 3 - shown


def test_a_target_marked_in_an_earlier_section_ranks_after_targets_not_yet_marked(tmp_path, monkeypatch):
    repeat, fresh = target("misconception", "m_repeat", p_open=1.0), target("hypothesis", "h_fresh", p_open=0.4)
    # m_repeat is marked in ch5 (t3); in the worked section it also links t5, as does h_fresh (lower p_open).
    cues, _ = _setup(tmp_path, monkeypatch, [repeat, fresh], [(repeat, "t3"), (repeat, "t5"), (fresh, "t4")],
                     density="fewer")
    worked = [mark for mark in cues["marks"] if mark["section_id"] == "worked"]
    assert [mark["target_id"] for mark in worked] == ["hypothesis:h_fresh"]


def test_value_order_off_is_the_judges_order_with_the_guide_first(tmp_path, monkeypatch):
    low, high = target("hypothesis", "h_low", p_open=0.1), target("hypothesis", "h_high", p_open=0.9)
    cues, _ = _setup(tmp_path, monkeypatch, [low, high],
                     [(low, "t1", {"pick_rank": 1}), (high, "t3", {"pick_rank": 2})], guide=["t2"],
                     config={"value_order_enabled": False})
    assert cues["discovery"]["value_order"] is False
    assert [m["span_id"] for m in sorted([m for m in cues["marks"] if m["section_id"] == "ch5"],
                                         key=lambda m: m["section_rank"])] == ["t2", "t1", "t3"]


def test_a_new_application_is_ordered_by_the_predictors_p_failure_on_its_passages_lo(tmp_path, monkeypatch):
    shown = target("demonstrated_facet", "facet_eigen", p_open=None, source="unavailable", topic="Eigenvalues")
    paths, repository, _spans = build_cue_vault(tmp_path / "v", misconception=False)
    set_config(paths, "cues", density="more", holdout_rate=0.0)
    seed_link(repository, shown, "t2", relation="new_application")
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: [shown])
    vault = loaded(paths)
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text",
                          plan=build_guide_plan(vault, repository, extraction_id="ext_text"))
    (mark,) = cues["marks"]
    assert mark["kind"] == "application" and mark["p_open_source"] == "predictor"
    assert 0.0 < mark["p_open"] < 1.0
    assert mark["note"] == "A new use of something you've shown: Eigenvalues."
