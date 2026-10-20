"""Reader workbench RW3b: cue value and the density control (spec_reader_workbench_v1 §6.2 item 4; G42).

Cues are ordered by the stored ``p_open``, then the judge's pick rank, Guide
first on ties; a target the learner already had in view this visit (its
impressions) ranks after every target not yet seen, and a target given a slot
in a section waits behind targets not yet given one (Codex review F10); the order uses no hand-set weight (any
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


def _shown(repository, cue_id: str, *, visit_id: str = "visit_1", at: str | None = None) -> None:
    from learnloop.clock import utc_now_iso
    from learnloop.db.stores import reader_cue_links as store

    with repository.connection() as connection:
        store.insert_impression(connection, {
            "id": f"cimp_{cue_id}", "cue_id": cue_id, "link_id": f"plink_{cue_id[len('dcue_'):]}"
            if cue_id.startswith("dcue_") else None, "extraction_id": "ext_text", "span_id": "t3",
            "learning_object_id": "lo_matrices", "kind": "distinction", "visit_id": visit_id, "shown": True,
            "suppressed_reason": None, "propensity": 1.0, "seed": "s", "p_open": 1.0, "p_open_source": "x",
            "density": "fewer", "created_at": at or utc_now_iso()})
        connection.commit()


def test_a_target_seen_this_visit_ranks_after_targets_not_yet_seen_and_placement_alone_never_demotes(
        tmp_path, monkeypatch):
    """Codex review F10: "already shown" is what the learner had in view this
    visit (its impressions), never a mark placed in an earlier section."""

    repeat, fresh = target("misconception", "m_repeat", p_open=1.0), target("hypothesis", "h_fresh", p_open=0.4)
    links = [(repeat, "t3"), (repeat, "t5"), (fresh, "t4")]
    # m_repeat has a mark in ch5 (t3), never seen: in the worked section it still outranks h_fresh.
    cues, _ = _setup(tmp_path / "a", monkeypatch, [repeat, fresh], links, density="fewer")
    worked = [mark for mark in cues["marks"] if mark["section_id"] == "worked"]
    assert [mark["target_id"] for mark in worked] == ["misconception:m_repeat"]
    # Once its ch5 mark was in view this visit, the next plan puts h_fresh first there.
    paths, repository, _spans = build_cue_vault(tmp_path / "b", misconception=False)
    set_config(paths, "cues", density="fewer", holdout_rate=0.0)
    for entry in links:
        seed_link(repository, *entry)
    monkeypatch.setattr(PC, "cue_targets", lambda *args, **kwargs: [repeat, fresh])
    vault = loaded(paths)
    plan = build_guide_plan(vault, repository, extraction_id="ext_text")
    first = PC.merged_cues(vault, repository, extraction_id="ext_text", plan=plan)
    seen_mark = next(mark for mark in first["marks"] if mark["span_id"] == "t3")
    _shown(repository, seen_mark["cue_id"])
    again = PC.merged_cues(vault, repository, extraction_id="ext_text", plan=plan)
    worked = [mark for mark in again["marks"] if mark["section_id"] == "worked"]
    assert [mark["target_id"] for mark in worked] == ["hypothesis:h_fresh"]
    # A visit long past (more than a reader session's gap) is not this visit.
    paths_c, repository_c, _ = build_cue_vault(tmp_path / "c", misconception=False)
    set_config(paths_c, "cues", density="fewer", holdout_rate=0.0)
    for entry in links:
        seed_link(repository_c, *entry)
    vault_c = loaded(paths_c)
    _shown(repository_c, seen_mark["cue_id"], at="2026-01-01T00:00:00Z")
    old = PC.merged_cues(vault_c, repository_c, extraction_id="ext_text",
                         plan=build_guide_plan(vault_c, repository_c, extraction_id="ext_text"))
    assert [m["target_id"] for m in old["marks"] if m["section_id"] == "worked"] == ["misconception:m_repeat"]


def test_a_targets_second_passage_in_a_section_waits_behind_targets_not_yet_given_a_slot(tmp_path, monkeypatch):
    """Codex review F10: one sort of a section let a repeated target take two
    slots ahead of an unseen one; the greedy order gives each target one first."""

    repeat, fresh = target("misconception", "m_repeat", p_open=1.0), target("hypothesis", "h_fresh", p_open=0.4)
    cues, _ = _setup(tmp_path, monkeypatch, [repeat, fresh], [(repeat, "t1"), (repeat, "t3"), (fresh, "t2")],
                     density="normal")
    ch5 = sorted((m for m in cues["marks"] if m["section_id"] == "ch5"), key=lambda m: m["section_rank"])
    assert [m["target_id"] for m in ch5] == ["misconception:m_repeat", "hypothesis:h_fresh"]


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
