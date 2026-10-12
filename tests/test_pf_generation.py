"""PF-b generate -> verify -> filter -> select -> publish (Slice 2 §5.3-§5.4, §13 PF gates)."""
from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import pytest

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.content.authoring import pf_contracts as C
from learnloop.content.authoring.pf_sandbox import sandbox_available
from learnloop.db.stores import pf as store
from learnloop.ops import pf_generation
from learnloop.ops.pf_generation import GenerationOptions, generate_practice, panel_difficulty, publish_backlog
from learnloop.substrate.activities import resolve_legacy_item
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from tests.pf_fakes import PFFake, clients, enable_pf, proposal, seed_pf_vault

needs_bwrap = pytest.mark.skipif(not sandbox_available(), reason="bubblewrap is not installed")

CAPS = SpendCaps(max_candidates=100, max_pairs=2000, max_calls=2000, max_total_tokens=100_000_000,
                 max_estimated_usd=10_000)
DAY = FrozenClock(datetime(2026, 10, 12, 12, 0, tzinfo=UTC))
NEXT_DAY = FrozenClock(datetime(2026, 10, 13, 12, 0, tzinfo=UTC))


def run(paths, *, path="ensemble", caps=CAPS, price=1.0, fakes=None, clock=DAY, dry_run=False, **options):
    options.setdefault("round", "r1")
    return generate_practice(
        load_vault(paths.root), caps=caps, options=GenerationOptions(path=path, **options),
        dry_run=dry_run, price_per_million=price, clients=fakes if fakes is not None else clients(),
        clock=clock,
    )


def all_calls(fakes) -> int:
    seen, total = set(), 0
    for value in fakes.values():
        for fake in value if isinstance(value, list) else [value]:
            if id(fake) not in seen:
                seen.add(id(fake))
                total += len(fake.calls)
    return total


@pytest.fixture
def pf(tmp_path):
    return seed_pf_vault(tmp_path / "vault")


def rows(repository, where="1=1", params=()):
    with repository.connection() as connection:
        return store.candidates(connection, where=where, params=params)


def ledger(repository, task):
    with repository.connection() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM judgment_ledger WHERE task=?", (task,))]


def test_dry_run_makes_no_calls_migrations_or_writes(pf):
    _, _, paths = pf
    fakes = clients()
    before = hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest()
    report = run(paths, dry_run=True, fakes=fakes)
    assert report["status"] == "dry_run"
    assert report["estimate"]["metered"]["calls"] > 0
    assert report["estimate"]["metered"]["estimated_usd"] > 0
    assert report["plan"][0]["roles"]["proposer"]["calls"] == 2
    assert all_calls(fakes) == 0
    assert hashlib.sha256(paths.sqlite_path.read_bytes()).hexdigest() == before
    assert not (paths.root / ".learnloop" / "pf-generate.lock").exists()


def test_kill_switch_refuses_paid_work_but_dry_run_still_estimates(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault", enabled=False)
    fakes = clients()
    report = run(paths, fakes=fakes)
    assert report["status"] == "disabled"
    dry = run(paths, fakes=fakes, dry_run=True)
    assert dry["status"] == "dry_run" and dry["generation_enabled"] is False
    assert all_calls(fakes) == 0


def test_generation_fails_closed_without_bubblewrap_before_any_paid_call(pf, monkeypatch):
    _, repository, paths = pf
    monkeypatch.setattr(pf_generation, "sandbox_available", lambda: False)
    fakes = clients()
    report = run(paths, fakes=fakes)
    assert report["status"] == "sandbox_unavailable"
    assert all_calls(fakes) == 0
    assert not rows(repository)


@pytest.mark.parametrize("dry_run", [True, False])
def test_fewer_than_two_distinct_proposer_models_is_refused(pf, dry_run):
    _, repository, paths = pf
    fakes = clients(proposer_models=("same-model", "same-model"))
    report = run(paths, fakes=fakes, dry_run=dry_run)
    assert report["status"] == "refused"
    assert "two distinct" in report["reason"]
    assert all_calls(fakes) == 0


def test_metered_unknown_price_and_caps_fail_closed_before_any_call(pf):
    _, _, paths = pf
    for kwargs in ({"price": None}, {"caps": SpendCaps(max_calls=5, max_pairs=2000, max_total_tokens=10**9,
                                                       max_estimated_usd=10**4)},
                   {"caps": SpendCaps(max_candidates=2, max_calls=2000, max_pairs=2000,
                                      max_total_tokens=10**9, max_estimated_usd=10**4)},
                   {"caps": SpendCaps(max_pairs=1, max_calls=2000, max_total_tokens=10**9,
                                      max_estimated_usd=10**4)}):
        fakes = clients()
        report = run(paths, fakes=fakes, **kwargs)
        assert report["status"] == "over_budget", kwargs
        assert all_calls(fakes) == 0


@needs_bwrap
def test_ensemble_publishes_verified_survivors_as_ordinary_family_items(pf):
    _, repository, paths = pf
    report = run(paths)
    assert report["status"] == "complete"
    family = report["families"][0]
    assert family["status"] == "complete"
    assert family["proposer_models"] == ["fake-a-resolved", "fake-b-resolved"]
    published = report["published_item_ids"]
    assert len(published) == 2  # pf.select_per_family default
    vault = load_vault(paths.root)
    parent = vault.practice_items["pi_linear_001"]
    parent_card = resolve_legacy_item(vault, repository, parent, purpose="practice").card_id
    cards = set()
    for item_id in published:
        item = vault.practice_items[item_id]
        assert item.family_id == "af_linear" and item.variant_relation == "isomorph"
        assert item.difficulty_source == "solver_panel" and 0.02 <= item.difficulty <= 0.98
        assert item.expected_answer.startswith("Final answer:")
        assert item.grading_rubric == parent.grading_rubric  # verbatim (structure check confirmed)
        assert item.evidence_fingerprint.source_family
        assert "pf_generated" in item.tags
        cards.add(resolve_legacy_item(vault, repository, item, purpose="practice").card_id)
    assert len(cards) == 2 and parent_card not in cards  # each item has its own card
    with repository.connection() as connection:
        members = connection.execute(
            "SELECT practice_item_id, variant_relation FROM activity_family_membership_events "
            "WHERE family_id='af_linear' AND action='add' AND proposal_id LIKE 'pfpub_%'").fetchall()
        receipts = connection.execute(
            "SELECT purpose, resolved_model, budget_json FROM model_call_receipts WHERE owner_kind='pf_generation'"
        ).fetchall()
        mint = connection.execute(
            "SELECT status, generator_version FROM surface_mint_requests WHERE id=?",
            (family["mint_request_id"],)).fetchone()
    assert {row[0] for row in members} == set(published)
    assert tuple(mint) == ("admitted", "pf_ensemble_v1")
    assert {row["purpose"] for row in receipts} >= {"pf_proposer", "pf_panel", "pf_equivalence",
                                                    "pf_structure", "pf_freshness", "pf_selection"}
    assert all(row["resolved_model"] and json.loads(row["budget_json"])["pf"]["prompt_version"]
               for row in receipts if row["budget_json"])
    statuses = {row["status"] for row in rows(repository)}
    assert statuses == {"published", "not_selected"}
    for row in rows(repository):
        cost = json.loads(row["cost_json"])
        assert cost["calls"] > 1 and cost["tokens"] > 0 and cost["metered_usd"] > 0
    assert all(row["verification"] == "verified" for row in rows(repository, "status='published'"))
    assert report["results_by_model"]["fake-a-resolved"]["ensemble"]


@needs_bwrap
def test_every_pf_verdict_is_ledgered_with_model_prompt_and_input(pf):
    _, repository, paths = pf
    run(paths)
    tasks = {"reference_verified", "answer_equivalence", "isomorph", "selection", "pf_publish"}
    with repository.connection() as connection:
        found = [dict(row) for row in connection.execute(
            f"SELECT * FROM judgment_ledger WHERE task IN ({','.join('?' for _ in tasks)})", tuple(tasks))]
    assert {row["task"] for row in found} == tasks
    for row in found:
        assert row["prompt_version"] and row["input_hash"]
        if row["judge"] == "llm":
            assert row["judge_model"]
    # The equivalence verifier's sympy confirmations are verifier rows.
    assert any(row["judge"] == "verifier" and row["task"] == "answer_equivalence" for row in found)


@needs_bwrap
def test_panel_disagreement_is_never_published_even_by_an_eager_judge(pf):
    _, repository, paths = pf
    first = [proposal("AMBIGUOUS 3x + 1 = 10 jars; solve for x."),
             proposal("A crate holds 5x + 2 = 22 kg; solve for x.")]
    second = [proposal("AMBIGUOUS 8x + 1 = 25 cups; solve for x."),
              proposal("A van carries 6x + 4 = 40 boxes; solve for x.")]
    eager = PFFake("eager-judge", select_everything=True)
    fakes = clients(proposer=[PFFake("fake-a", proposals=first), PFFake("fake-b", proposals=second)],
                    selection=eager)
    report = run(paths, fakes=fakes, count=4, select=5)
    assert report["status"] == "complete"
    ambiguous = rows(repository, "payload_json LIKE '%AMBIGUOUS%'")
    assert ambiguous and all(row["verification"] == "unverified" for row in ambiguous)
    assert all(row["rejection_filter"] == "solve_first_agreement" for row in ambiguous)
    assert all(row["status"] == "rejected" for row in ambiguous)
    vault = load_vault(paths.root)
    assert not any("AMBIGUOUS" in item.prompt for item in vault.practice_items.values())
    # The judge would pick anything: it was only ever offered verified survivors.
    for request in eager.calls:
        if request.result_model is C.SelectionVerdict:
            assert "AMBIGUOUS" not in request.prompt
    verified_stems = {json.loads(row["payload_json"])["stem"] for row in rows(repository, "verification='verified'")}
    offered = [json.loads(request.prompt[request.prompt.index("{"):])["context"]["candidates"]
               for request in eager.calls if request.result_model is C.SelectionVerdict]
    assert offered and all(candidate["stem"] in verified_stems for batch in offered for candidate in batch)


@needs_bwrap
def test_declared_isomorph_without_a_passing_structure_check_is_never_published_as_isomorph(pf):
    _, repository, paths = pf
    first = [proposal("NEARVARIANT 4x + 3 = 19 coins; solve for x."),
             proposal("RUBRICMISMATCH 6x + 2 = 20 m; solve for x.")]
    second = [proposal("A ladder has 7x + 1 = 29 rungs; solve for x."),
              proposal("A shelf holds 2x + 9 = 21 books; solve for x.")]
    fakes = clients(proposer=[PFFake("fake-a", proposals=first), PFFake("fake-b", proposals=second)])
    run(paths, fakes=fakes, count=4, select=5)
    near = rows(repository, "payload_json LIKE '%NEARVARIANT%'")
    assert near and all(row["final_relation"] == "near" for row in near)
    mismatch = rows(repository, "payload_json LIKE '%RUBRICMISMATCH%'")
    assert mismatch and all(row["rejection_filter"] == "structure_check" for row in mismatch)
    vault = load_vault(paths.root)
    for item in vault.practice_items.values():
        if "NEARVARIANT" in item.prompt:
            assert item.variant_relation == "near"
            assert item.trace_contract is None
        assert "RUBRICMISMATCH" not in item.prompt


@needs_bwrap
def test_freshness_rejects_exact_and_judged_duplicates(pf):
    _, repository, paths = pf
    proposals = [proposal("Solve 2x + 4 = 10 for x.", "3"),          # the parent, exactly
                 proposal("  solve 2X + 4 = 10   for x.", "3"),      # normalized identical
                 proposal("Solve 2x + 4 = 10, for x", "3"),          # the judge: same surface
                 proposal("A bag holds 9x + 3 = 30 marbles; solve for x.")]
    fakes = clients(proposer=[PFFake("fake-a", proposals=proposals), PFFake("fake-b", proposals=proposals[2:])])
    run(paths, fakes=fakes, count=4, select=5)
    by_stem = {json.loads(row["payload_json"])["stem"]: row for row in rows(repository)}
    assert by_stem["Solve 2x + 4 = 10 for x."]["rejection_filter"] == "exact_duplicate"
    assert by_stem["  solve 2X + 4 = 10   for x."]["rejection_filter"] == "exact_duplicate"
    assert by_stem["Solve 2x + 4 = 10, for x"]["rejection_filter"] == "freshness"
    assert by_stem["A bag holds 9x + 3 = 30 marbles; solve for x."]["status"] == "published"
    exact = [row for row in ledger(repository, "isomorph") if row["judge"] == "exact_key"]
    assert exact and all(row["verdict"] == "same_surface" for row in exact)


@needs_bwrap
def test_generator_path_writes_a_tested_program_and_publishes_cas_verified_draws(pf):
    _, repository, paths = pf
    report = run(paths, path="generator")
    family_report = report["families"][0]
    assert family_report["status"] == "complete", family_report
    vault = load_vault(paths.root)
    family = vault.activity_families["af_linear"]
    assert family.source_kind == "generator"
    assert family.generator["protocol"] == "pf-generator-v1"
    assert family.generator["hash"] == hashlib.sha256(json.dumps(family.generator["program"]).encode()).hexdigest()
    assert family.reference.verification == "verified"
    candidates = rows(repository)
    assert all(row["verification_check"] == "execution_cas" for row in candidates)
    assert len(report["published_item_ids"]) == 2
    for item_id in report["published_item_ids"]:
        item = vault.practice_items[item_id]
        assert item.variant_relation == "isomorph" and item.difficulty_source == "solver_panel"
    assert ledger(repository, "generator_tests")[0]["verdict"] == "pass"
    # A rerun of a new round reuses the stored program: no new program call.
    program_fake = PFFake("fake-judge")
    rerun = run(paths, path="generator", round="r2", fakes=clients(program=program_fake))
    assert rerun["status"] == "complete"
    assert not [call for call in program_fake.calls if call.result_model is C.GeneratorProgramResult]


@needs_bwrap
def test_a_program_that_fails_its_tests_is_retried_then_the_family_publishes_nothing(pf):
    _, repository, paths = pf
    broken = PFFake("fake-judge", program="def generate(seed):\n    return {}\n\ndef check(draw, answer):\n    return True\n")
    report = run(paths, path="generator", fakes=clients(program=broken))
    family = report["families"][0]
    assert family["status"] == "complete"
    assert family["candidates"] == 0 and "program_failure" in family
    programs = [call for call in broken.calls if call.result_model is C.GeneratorProgramResult]
    assert len(programs) == 1 + CAPS.max_retries
    assert all(row["verdict"] == "fail" for row in ledger(repository, "generator_tests"))
    assert not report["published_item_ids"]


@needs_bwrap
def test_single_shot_arm_is_measured_but_never_published(pf):
    _, repository, paths = pf
    report = run(paths, path="single_shot")
    assert report["status"] == "complete"
    candidates = rows(repository)
    assert candidates and {row["status"] for row in candidates} == {"baseline"}
    assert not report["published_item_ids"]
    assert all(json.loads(row["filters_json"]) for row in candidates)


@needs_bwrap
def test_publish_cap_holds_per_utc_day_and_the_backlog_publishes_next_day(tmp_path):
    _, repository, paths = seed_pf_vault(tmp_path / "vault", max_published_per_day=1)
    first = run(paths, select=3)
    assert len(first["published_item_ids"]) == 1
    assert first["families"][0]["capped"] == 2
    second = run(paths, select=3, round="r2")
    assert not second["published_item_ids"]
    assert len(rows(repository, "status='published'")) == 1
    same_day = publish_backlog(load_vault(paths.root), clock=DAY)
    assert same_day["published_item_ids"] == []
    next_day = publish_backlog(load_vault(paths.root), clock=NEXT_DAY)
    assert len(next_day["published_item_ids"]) == 1
    assert len(rows(repository, "status='published'")) == 2


@needs_bwrap
def test_an_unverified_candidate_cannot_be_published(pf):
    from learnloop.ops.pf_publish import PublishRefused, publish_candidate

    _, repository, paths = pf
    run(paths, publish=False, select=1)
    selected = rows(repository, "status='selected'")[0]
    with repository.connection() as connection:
        store.update_candidate(connection, selected["id"], verification="unverified")
    with pytest.raises(PublishRefused, match="unverified"):
        publish_candidate(load_vault(paths.root), repository, selected["id"], clock=DAY)
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        with repository.connection() as connection:
            store.update_candidate(connection, selected["id"], status="published", published_item_id="x")


@needs_bwrap
def test_an_interrupted_run_resumes_without_repaying_finished_work(tmp_path):
    _, _, reference_paths = seed_pf_vault(tmp_path / "reference")
    reference_fakes = clients()
    run(reference_paths, fakes=reference_fakes)
    total = all_calls(reference_fakes)

    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    fakes = clients()
    calls = {"n": 0}

    class Interrupting(PFFake):
        def complete(self, request):
            calls["n"] += 1
            if calls["n"] == 20:
                raise AIInterrupted("stop")
            return super().complete(request)

    fakes["panel"] = [Interrupting("fake-panel-1"), Interrupting("fake-panel-2")]
    first = run(paths, fakes=fakes)
    assert first["status"] == "cancelled"
    with repository.connection() as connection:
        assert connection.execute("SELECT status FROM surface_mint_requests").fetchone()[0] == "pending"
    resumed_fakes = clients()
    second = run(paths, fakes=resumed_fakes)
    assert second["status"] == "complete"
    # Every completed paid call was checkpointed; only the interrupted one
    # (never returned, so never recorded) is sent again.
    assert all_calls(fakes) + all_calls(resumed_fakes) == total
    assert len(second["published_item_ids"]) == 2


@needs_bwrap
def test_codex_routes_run_on_the_subscription_with_estimated_only_cost(pf):
    _, repository, paths = pf
    codex = {role: ([PFFake(f"codex-{role}-{i}", provider_type="codex_sdk") for i in range(2)]
                    if role in {"proposer", "panel"} else PFFake("codex-judge", provider_type="codex_sdk"))
             for role in clients()}
    report = run(paths, fakes=codex, price=None, caps=SpendCaps(max_candidates=100, max_pairs=2000,
                                                                max_calls=2000, max_total_tokens=1,
                                                                max_estimated_usd=0))
    assert report["status"] == "complete"
    with repository.connection() as connection:
        receipts = connection.execute(
            "SELECT budget_json, usage_json FROM model_call_receipts WHERE owner_kind='pf_generation' "
            "AND budget_json IS NOT NULL").fetchall()
    assert receipts
    for budget_json, usage_json in receipts:
        budget = json.loads(budget_json)
        assert budget["billing"] == "subscription" and budget["physical_request_bound"] is False
        assert json.loads(usage_json)["cost_basis"] == "estimated_only"


@needs_bwrap
def test_owner_seed_item_creates_an_authored_family_first(tmp_path):
    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    report = run(paths, seed_items=("pi_svd_define_001",), family_ids=())
    vault = load_vault(paths.root)
    seeded = vault.practice_items["pi_svd_define_001"]
    assert seeded.family_id and seeded.family_id.startswith("af_pf_seed_")
    decision = [row for row in ledger(repository, "family_decision") if row["left_id"].startswith("pfseed_")]
    assert decision and decision[0]["judge"] == "owner"
    assert {family["family_id"] for family in report["families"]} >= {seeded.family_id, "af_linear"}


def test_panel_difficulty_is_a_logit_offset_from_the_parent():
    assert panel_difficulty(0.4, (6, 6), (6, 6), 2.5) == 0.4
    harder = panel_difficulty(0.4, (6, 6), (2, 6), 2.5)
    easier = panel_difficulty(0.4, (3, 6), (6, 6), 2.5)
    assert harder > 0.4 > easier
    assert panel_difficulty(None, (0, 6), (6, 6), 2.5) >= 0.02
    assert panel_difficulty(0.97, (6, 6), (0, 6), 2.5) == 0.98
    # The proposer contract never carries a self-labelled difficulty.
    assert "difficulty" not in C.ProposedCandidate.model_fields


@needs_bwrap
def test_published_items_keep_scheduling_hashes_and_unfamilied_items_unchanged(pf):
    vault, _, paths = pf
    before = {item_id: (practice_item_hash(item), item.model_dump(mode="json"))
              for item_id, item in vault.practice_items.items()}
    report = run(paths)
    after = load_vault(paths.root)
    for item_id, (scheduling_hash, dumped) in before.items():
        assert practice_item_hash(after.practice_items[item_id]) == scheduling_hash
        assert after.practice_items[item_id].model_dump(mode="json") == dumped
    for item_id in report["published_item_ids"]:
        item = after.practice_items[item_id]
        clone = item.model_copy(update={"difficulty_source": "author"})
        assert practice_item_hash(clone) == practice_item_hash(item)
    unfamilied = after.practice_items["pi_svd_define_001"].model_dump(mode="json")
    assert "family_id" not in unfamilied and "variant_relation" not in unfamilied


def test_enable_helper_round_trips_the_template_switch(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault", enabled=False)
    assert not load_vault(paths.root).config.pf.generation_enabled
    enable_pf(paths.root, max_published_per_day=3)
    config = load_vault(paths.root).config.pf
    assert config.generation_enabled and config.max_published_per_day == 3


@needs_bwrap
def test_source_anchored_items_need_a_quote_verified_span_and_must_not_be_closed_book(tmp_path):
    from learnloop.vault.writer import upsert_practice_item

    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    parent = vault.practice_items["pi_linear_001"].model_dump(mode="json")
    parent["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "manual_context", "ref_id": "ctx1",
        "quote": "The focus of a parabola is the fixed point used with the directrix to define it."}]}
    upsert_practice_item(paths.root, parent)
    report = run(paths, path="source_anchored", count=5, select=5)
    assert report["status"] == "complete", report
    by_stem = {json.loads(row["payload_json"])["stem"]: row for row in rows(repository)}
    why = by_stem["Why did the authors choose a directrix?"]
    assert why["rejection_filter"] == "provenance" and why["verification"] == "unverified"
    assert json.loads(why["payload_json"])["provenance_label"] == "inferred"
    assert by_stem["GENERIC: what is a parabola?"]["rejection_filter"] == "closed_book"
    assert by_stem["When does the focus construction fail?"]["rejection_filter"] == "quote_verified_span"
    verified = [row for row in by_stem.values() if row["verification"] == "verified"]
    assert {row["verification_check"] for row in verified} == {"quote_verified_span"}
    published = load_vault(paths.root)
    for item_id in report["published_item_ids"]:
        item = published.practice_items[item_id]
        assert 'Source: "The focus of a parabola' in item.expected_answer
        assert item.difficulty is None and item.difficulty_source is None  # no panel on this path
    assert report["published_item_ids"]
    assert {row["verdict"] for row in ledger(repository, "closed_book")} == {"answerable", "not_answerable"}
    assert [row["verdict"] for row in ledger(repository, "provenance")] == ["inferred"]


def test_seeding_writes_nothing_until_the_plan_is_admitted(tmp_path):
    _, _, paths = seed_pf_vault(tmp_path / "vault")
    fakes = clients()
    report = run(paths, fakes=fakes, seed_items=("pi_svd_define_001",),
                 caps=SpendCaps(max_calls=1, max_pairs=2000, max_total_tokens=10**9, max_estimated_usd=10**4))
    assert report["status"] == "over_budget"
    assert load_vault(paths.root).practice_items["pi_svd_define_001"].family_id is None
    assert all_calls(fakes) == 0
    with pytest.raises(ValueError, match="Unknown seed items"):
        run(paths, seed_items=("missing",))


@needs_bwrap
def test_an_unparseable_parent_reference_gives_a_neutral_difficulty_basis(tmp_path):
    from learnloop.vault.writer import upsert_practice_item

    _, repository, paths = seed_pf_vault(tmp_path / "vault")
    parent = load_vault(paths.root).practice_items["pi_linear_001"].model_dump(mode="json")
    parent["expected_answer"] = "Subtract four and halve: x equals three."
    upsert_practice_item(paths.root, parent)
    run(paths)
    published = rows(repository, "status='published'")
    assert published
    for row in published:
        panel = json.loads(row["panel_json"])
        assert panel["difficulty_basis"] == "batch_mean" and panel["parent_rate"][0] == 0
        # Every sibling solved equally often: no offset from the parent's difficulty.
        assert row["difficulty"] == 0.4


# -- Codex review F1: every PF role is an isolated, tool-free turn -------------------------


class _NonIsolating(PFFake):
    """A transport that can run tools (an agent without an isolation boundary)."""

    def supports(self, capability: str) -> bool:
        return capability in {"structured_completion", "bounded_structured_completion"}


@needs_bwrap
def test_every_pf_request_reaches_its_transport_as_an_isolated_turn(tmp_path):
    from learnloop.vault.writer import upsert_practice_item

    _, _, paths = seed_pf_vault(tmp_path / "vault")
    fakes = clients()
    report = run(paths, fakes=fakes)
    assert report["status"] == "complete"
    parent = load_vault(paths.root).practice_items["pi_linear_001"].model_dump(mode="json")
    parent["provenance"] = {"origin": "human", "source_refs": [{
        "ref_type": "manual_context", "ref_id": "ctx1",
        "quote": "The focus of a parabola is the fixed point used with the directrix to define it."}]}
    upsert_practice_item(paths.root, parent)
    source = run(paths, path="source_anchored", fakes=fakes, round="r2", count=5)
    assert source["status"] == "complete"
    requests = [request for value in fakes.values()
                for fake in (value if isinstance(value, list) else [value]) for request in fake.calls]
    roles = {request.purpose for request in requests}
    assert {"pf_panel", "pf_closed_book", "pf_proposer", "pf_equivalence", "pf_structure"} <= roles
    assert requests and all(request.isolated for request in requests)


@needs_bwrap
def test_a_route_that_cannot_isolate_is_refused_before_any_request(pf):
    _, repository, paths = pf
    leaky = _NonIsolating("leaky-panel")
    report = run(paths, fakes=clients(panel=[leaky, PFFake("fake-panel-2")]))
    family = report["families"][0]
    assert family["status"] == "failed" and family["error_type"] == "PFUnavailable"
    assert "isolated" in family["reason"]
    assert not leaky.calls
    assert not rows(repository, "status='published'")


def _fake_codex_sdk(monkeypatch, captured, final_response):
    import sys
    from enum import Enum
    from pathlib import Path
    from types import ModuleType, SimpleNamespace

    class FakeCodex:
        def __init__(self, config):
            captured["app_config"] = config.kwargs
            captured["listing"] = sorted(path.name for path in Path(config.kwargs["cwd"]).iterdir())

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        def thread_start(self, **kwargs):
            captured["thread_start"] = kwargs
            return SimpleNamespace(turn=lambda prompt, **kw: captured.setdefault("turns", []).append(kw) or SimpleNamespace(
                run=lambda: SimpleNamespace(final_response=final_response, items=[]), interrupt=lambda: None))

    class SdkAppConfig:
        def __init__(self, *, codex_bin=None, launch_args_override=None, config_overrides=(), cwd=None, env=None,
                     client_name="", client_title=""):
            self.kwargs = {"codex_bin": codex_bin, "launch_args_override": launch_args_override,
                           "config_overrides": tuple(config_overrides), "cwd": cwd}

    class ReasoningEffort(Enum):
        low = "low"

    module = ModuleType("openai_codex")
    module.Codex = FakeCodex
    module.CodexConfig = SdkAppConfig
    types_module = ModuleType("openai_codex.types")
    types_module.Personality = SimpleNamespace(pragmatic="pragmatic")
    types_module.ReasoningEffort = ReasoningEffort
    types_module.ReasoningSummary = SimpleNamespace(model_validate=lambda value: value)
    module.types = types_module
    monkeypatch.setitem(sys.modules, "openai_codex", module)
    monkeypatch.setitem(sys.modules, "openai_codex.types", types_module)


def test_a_codex_pf_turn_starts_outside_the_vault_with_tools_off_and_never_reuses_unisolated_work(
        pf, monkeypatch, tmp_path):
    from learnloop.ai.execution import content_key
    from learnloop.ai.providers.codex import ISOLATED_PROFILE, SdkCodexClient
    from learnloop.config import CodexConfig
    from learnloop.ops.pf_calls import CHECKPOINT_PREFIX, PFCaller, RoleClient

    vault, repository, paths = pf
    captured: dict = {}
    _fake_codex_sdk(monkeypatch, captured, '{"final_answer": "3", "answer_kind": "numeric", "work_summary": "w"}')
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin="/usr/bin/codex-for-test"),
                            paths.root)
    monkeypatch.setattr(client, "_configured_mcp_server_ids", lambda _cwd: ("filesystem",))
    entry = RoleClient(role="panel", provider="codex_low", model="codex-model", profile_type="codex_sdk",
                       subscription=True, client=client, settings={"provider": "codex_low", "model": "codex-model"})
    caller = PFCaller(vault, repository, caps=CAPS, price_per_million=None, run_id="run-f1")
    prompt = C.panel_solve_prompt(stem="Solve 2x + 4 = 10 for x.", solve_index=0)
    # A checkpoint written under the pre-isolation key (an unisolated turn) is never reused.
    legacy = content_key({"prompt": prompt, "schema": C.PanelSolve.model_json_schema(),
                          "settings": entry.settings, "output_tokens": 1500})
    repository.save_model_checkpoint(CHECKPOINT_PREFIX + legacy, purpose="pf_panel",
                                     result={"final_answer": "LEAKED", "answer_kind": "text", "work_summary": "read"},
                                     usage={"resolved_model": "codex-model"})
    result = caller.call(entry, prompt=prompt, prompt_version=C.PANEL_SOLVE_PROMPT, result_model=C.PanelSolve,
                         output_tokens=1500)
    assert not result.cached and result.result.final_answer == "3"
    assert result.input_hash != legacy
    cwd = Path(captured["app_config"]["cwd"])
    root = paths.root.resolve()
    assert cwd != root and root not in cwd.parents and captured["listing"] == []
    overrides = captured["app_config"]["config_overrides"]
    assert f'default_permissions="{ISOLATED_PROFILE}"' in overrides
    assert {"features.shell_tool=false", "features.unified_exec=false",
            "mcp_servers.filesystem.enabled=false"} <= set(overrides)


# -- Codex review F3: a final isomorph always has a passing structure check ----------------


@needs_bwrap
@pytest.mark.parametrize("relation", ["isomorph", "near"])
def test_freshness_never_restores_isomorph_over_a_failed_structure_check(pf, relation):
    _, repository, paths = pf
    first = [proposal("NEARVARIANT 4x + 3 = 19 coins; solve for x.")]
    second = [proposal("NEARVARIANT 8x + 3 = 35 pens; solve for x.")]
    eager = PFFake("fake-judge", freshness_parent="isomorph")  # the two judges disagree
    fakes = clients(proposer=[PFFake("fake-a", proposals=first), PFFake("fake-b", proposals=second)],
                    freshness=eager)
    report = run(paths, fakes=fakes, count=2, select=5, relation=relation)
    assert report["status"] == "complete"
    candidates = rows(repository)
    assert candidates and all(row["final_relation"] == "near" for row in candidates)
    for row in candidates:
        freshness = json.loads(row["filters_json"])["freshness"]["detail"]
        assert freshness.get("isomorph_relabel_refused") and "relabelled" not in freshness
    vault = load_vault(paths.root)
    published = [vault.practice_items[item_id] for item_id in report["published_item_ids"]]
    assert published and all(item.variant_relation == "near" and item.trace_contract is None for item in published)


@needs_bwrap
def test_an_isomorph_verdict_without_preserved_checkpoints_is_never_a_final_isomorph(pf):
    _, repository, paths = pf
    inconsistent = PFFake("fake-judge", structure={"relation": "isomorph", "checkpoint_sequence_preserved": False})
    report = run(paths, fakes=clients(structure=inconsistent), relation="near")
    assert report["status"] == "complete"
    candidates = rows(repository, "rejection_filter IS NULL")
    assert candidates and all(row["final_relation"] == "near" for row in candidates)
    declared_isomorph = run(paths, fakes=clients(structure=inconsistent), round="r2")
    assert declared_isomorph["status"] == "complete"
    assert all(row["final_relation"] != "isomorph" for row in rows(repository, "round='r2'"))
