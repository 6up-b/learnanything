"""Reader workbench RW3b: discovered links (spec_reader_workbench_v1 §6.2 items 1-5, §6.3, §6.4; G15, G42, G44).

Targets are read from existing state; the shortlist is T6's retrieval over the
open source with the contrast and correction-span lists fused in (in the
manifest, G42); the listwise judge decides (G15: stubbed to ``none``, no
discovered cue whatever retrieval ranks; every cue has a ledger verdict and a
verified quote); a target's state key recomputes only its own links; the
ledger serves a repeat without a call; caps and the metered daily cap hold;
roles are proposals used only to add candidates (G44). Fakes only.
"""

from __future__ import annotations

import json

import pytest

from learnloop.db.stores import reader_cue_links as store
from learnloop.reader.reader_guidance import build_guide_plan
from learnloop.source_retrieval import passage_cues as PC
from tests.passage_cue_fakes import STATEMENT, CueJudgeFake, build_cue_vault, loaded, set_config


def _links(repository, extraction_id: str = "ext_text") -> list[dict]:
    with repository.connection() as connection:
        return store.links_for_extraction(connection, extraction_id)


def _ledger(repository, left_kind: str = PC.TARGET_LEFT_KIND) -> list[dict]:
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = 'passage_cue' AND left_kind = ? ORDER BY id", (left_kind,))]


def _receipts(repository) -> int:
    with repository.connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM model_call_receipts WHERE purpose = 'passage_cue_judge'").fetchone()[0]


# -- targets ------------------------------------------------------------------------------------


def test_targets_are_the_open_sources_states_each_with_its_statement_and_p_open(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    targets = PC.cue_targets(vault, repository, "ext_text")
    assert [(t.kind, t.id, t.statement, t.p_open, t.p_open_source) for t in targets] == [
        ("misconception", "mis_swap", STATEMENT, 1.0, "misconception_lifecycle")]
    # The state key is the statement and status: a resolved target is no target.
    repository.update_misconception("mis_swap", status="resolved")
    assert PC.cue_targets(vault, repository, "ext_text") == []


def test_a_source_teaching_none_of_the_targets_los_has_no_targets(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    assert PC.cue_targets(loaded(paths), repository, "ext_exam") == []


# -- the shortlist: protected before the judge, lists in the manifest (G42) ---------------------


def test_the_shortlist_never_carries_a_solution_or_held_out_passage(tmp_path):
    paths, repository, spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    (target,) = PC.cue_targets(vault, repository, "ext_text")
    listed = PC.shortlist(vault, repository, target, "ext_text")
    assert listed.keys and all(key[0] == "ext_text" for key in listed.keys)
    assert not {key[1] for key in listed.keys} & set(spans["solutions"])
    assert listed.withheld.get("solution", 0) >= 1  # the solution matched and was dropped before the judge


def test_contrast_and_correction_lists_join_the_fusion_and_the_manifest(tmp_path):

    paths, repository, _spans = build_cue_vault(tmp_path / "v", correction_source_ids=["src_text"])
    vault = loaded(paths)
    # Earlier cue judgments proposed t2 as a contrast on lo_matrices (RW3b's own roles).
    _seed_role_link(repository, span_id="t2", roles=[{"role": "contrast", "confidence": "high"}])
    (target,) = PC.cue_targets(vault, repository, "ext_text")
    listed = PC.shortlist(vault, repository, target, "ext_text")
    manifest = listed.manifest()
    assert manifest["lists"].get("contrast") == 1
    assert manifest["lists"].get("correction_sources", 0) >= 1
    assert ("ext_text", "t2") in listed.keys
    assert "contrast" in listed.ranks[("ext_text", "t2")]


def _seed_role_link(repository, *, span_id: str, roles: list[dict], target_id: str = "mis_old") -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
            "judge_model, prompt_version, input_hash, verdict, score, rationale) VALUES (?, '2026-10-01T00:00:00Z', "
            "'passage_cue', 'cue_target', 'ext_text|misconception:mis_old|old', 'reader_span', ?, 'llm', 'm', 'v', "
            "'h', 'clarifies_distinction', 1.0, '{}')", (f"pcj_seed_{span_id}", f"ext_text/{span_id}"))
        store.insert_link(connection, {
            "id": f"plink_seed_{span_id}", "extraction_id": "ext_text", "span_id": span_id,
            "target_kind": "misconception", "target_id": target_id, "relation": "clarifies_distinction",
            "quote": "seeded quote words here", "pick_rank": 1, "roles": roles, "ledger_id": f"pcj_seed_{span_id}",
            "state_key": "old", "model": "m", "prompt_version": "v", "created_at": "2026-10-01T00:00:00Z"})
        connection.commit()


# -- the judge decides (G15) ----------------------------------------------------------------------


def test_with_the_judge_stubbed_to_none_no_discovered_cue_appears(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(none_all=True))
    assert out["calls"] == 1 and out["targets"][0]["status"] == "judged"
    assert _links(repository) == []
    # Every shortlisted passage still has its verdict (none) on the ledger.
    assert {row["verdict"] for row in _ledger(repository)} == {"none"}
    plan = build_guide_plan(vault, repository, extraction_id="ext_text")
    cues = PC.merged_cues(vault, repository, extraction_id="ext_text", plan=plan)
    assert [mark for mark in cues["marks"] if mark.get("found_by") == "model"] == []


def test_every_discovered_link_has_a_ledger_verdict_and_a_verified_quote(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake())
    links = _links(repository)
    assert links and len(links) <= PC.PICK_AT_MOST
    ledger = {row["id"]: row for row in _ledger(repository)}
    with repository.connection() as connection:
        from learnloop.db.stores.source_block_fts import blocks_by_key

        blocks = blocks_by_key(connection, [("ext_text", link["span_id"]) for link in links])
    for link in links:
        row = ledger[link["ledger_id"]]
        assert row["verdict"] == link["relation"] and row["right_id"] == f"ext_text/{link['span_id']}"
        assert json.loads(row["rationale"])["pick_rank"] == link["pick_rank"]
        assert PC.quote_verifies(link["quote"], blocks[("ext_text", link["span_id"])].text)
        assert link["model"] == "fake-cue-judge-model" and link["prompt_version"] == PC.PROMPT_VERSION
    assert out["targets"][0]["links"] == [link["id"] for link in sorted(links, key=lambda l: l["pick_rank"])]


def test_a_pick_whose_quote_is_not_its_passages_words_is_dropped_never_repaired(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(bad_quote=("Swapping two rows",)))
    dropped = out["targets"][0]["dropped"]
    assert dropped and dropped[0]["reason"] == "its quote is not this passage's words"
    assert "t3" not in {link["span_id"] for link in _links(repository)}


# -- state keys and the ledger cache --------------------------------------------------------------


def test_a_second_open_pays_nothing_and_a_new_statement_recomputes_only_its_own_links(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    fake = CueJudgeFake()
    PC.discover(vault, repository, "ext_text", client=fake)
    first = _links(repository)
    again = PC.discover(vault, repository, "ext_text", client=fake)
    assert len(fake.prompts) == 1 and again["calls"] == 0
    assert again["targets"][0]["status"] == "current"
    # A new target (a named misconception on the same LO) is judged; the old one is not.
    repository.insert_misconception(id="mis_two", learning_object_id="lo_matrices", status="active",
                                    statement="Eigenvalues are the diagonal of any square matrix polynomial")
    third = PC.discover(vault, repository, "ext_text", client=fake)
    assert len(fake.prompts) == 2 and third["calls"] == 1
    assert [entry["status"] for entry in third["targets"]] == ["current", "judged"]
    assert all(link in _links(repository) for link in first)


def test_a_lost_link_write_is_recovered_from_the_paid_answer_without_paying_again(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    fake = CueJudgeFake()
    original = store.insert_link
    calls = {"n": 0}

    def failing(connection, row):
        calls["n"] += 1
        raise RuntimeError("the process died after the ledger committed")

    store.insert_link = failing
    try:
        with pytest.raises(RuntimeError):
            PC.discover(vault, repository, "ext_text", client=fake)
    finally:
        store.insert_link = original
    assert _ledger(repository) and _links(repository) == []
    PC.discover(vault, repository, "ext_text", client=fake)
    assert len(fake.prompts) == 1, "the ledger and the checkpoint answered; nothing was paid again"
    assert _links(repository)


# -- caps, spend, dry run --------------------------------------------------------------------------


def test_one_source_open_makes_at_most_max_calls_per_source_open(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    for index in range(3):
        repository.insert_misconception(id=f"mis_extra_{index}", learning_object_id="lo_matrices", status="active",
                                        statement=f"Swapping rows of a matrix determinant variant {index}")
    set_config(paths, "cues", max_calls_per_source_open=2)
    vault = loaded(paths)
    fake = CueJudgeFake()
    out = PC.discover(vault, repository, "ext_text", client=fake)
    assert out["calls"] == 2 and len(fake.prompts) == 2
    assert sorted(entry["status"] for entry in out["targets"]) == ["capped", "capped", "judged", "judged"]


def test_a_metered_judge_without_a_price_is_skipped_and_with_a_cap_is_held_to_it(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(provider_type="openai_chat"))
    assert out["targets"][0]["status"].startswith("skipped: metered cue judge route")
    assert _receipts(repository) == 0
    set_config(paths, "source_retrieval", llm_price_per_million=1000.0)
    set_config(paths, "cues", max_daily_cost_usd=0.0)
    vault = loaded(paths)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(provider_type="openai_chat"))
    assert out["targets"][0]["status"] == "capped" and _links(repository) == []


def test_codex_on_the_subscription_is_never_refused_by_the_metered_cap(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", max_daily_cost_usd=0.0)
    vault = loaded(paths)
    out = PC.discover(vault, repository, "ext_text", client=CueJudgeFake(provider_type="codex_sdk"))
    assert out["targets"][0]["status"] == "judged" and _links(repository)


def test_the_dry_run_lists_targets_and_shortlists_and_calls_and_writes_nothing(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    fake = CueJudgeFake()
    out = PC.discover(vault, repository, "ext_text", client=fake, dry_run=True)
    assert out["dry_run"] and out["targets"][0]["status"] == "dry_run"
    assert out["targets"][0]["manifest"]["candidates"] >= 1
    assert fake.prompts == [] and _ledger(repository) == [] and _links(repository) == []


def test_discovery_switched_off_does_nothing(tmp_path):
    paths, repository, _spans = build_cue_vault(tmp_path / "v")
    set_config(paths, "cues", discovery_enabled=False)
    fake = CueJudgeFake()
    assert PC.discover(loaded(paths), repository, "ext_text", client=fake)["status"] == "disabled"
    assert fake.prompts == []


# -- roles: positive use only (G44) ----------------------------------------------------------------


def test_roles_are_kept_with_confidence_judge_and_ledger_and_never_exclude(tmp_path):
    from learnloop.source_retrieval.corpus import ITEM_BOUND_EXCLUDED_ROLE_HINTS, model_reader_withheld

    paths, repository, spans = build_cue_vault(tmp_path / "v")
    vault = loaded(paths)
    PC.discover(vault, repository, "ext_text",
                client=CueJudgeFake(roles=(("contrast", "high"), ("exercise", "low"))))
    links = _links(repository)
    assert links
    for link in links:
        assert {"role": "contrast", "confidence": "high"} in link["roles"]
        assert link["ledger_id"] and link["model"] and link["prompt_version"]
    # A span the judge called a contrast that ingest marks exercise or solution
    # stays excluded where exercises and solutions are: the role only adds.
    exercise = next(link for link in links if link["span_id"] in spans["exercises"])
    _seed_role_link(repository, span_id=spans["solutions"][1], roles=[{"role": "contrast", "confidence": "high"}])
    assert model_reader_withheld(vault, repository, [("ext_text", spans["solutions"][1])]) == {
        ("ext_text", spans["solutions"][1]): "solution"}
    from learnloop.source_retrieval.corpus import teaching_scope

    item = next(item for item in vault.practice_items.values() if item.learning_object_id == "lo_matrices")
    bound = teaching_scope(vault, repository, [item.learning_object_id], item_bound=True, item=item)
    assert "exercise" in ITEM_BOUND_EXCLUDED_ROLE_HINTS and "ext_text" in bound.extractions
    assert not bound.allows("ext_text", exercise["span_id"])
    assert not bound.allows("ext_text", spans["solutions"][1])


def test_the_judges_role_vocabulary_is_rw4es():
    from learnloop.source_retrieval.library_ask import ROLES

    assert set(PC.RoleProposal.model_json_schema()["properties"]["role"]["enum"]) == set(ROLES)
