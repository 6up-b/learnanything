"""Which inventory row synthesis and coverage read for a unit (refactor K3.1).

A unit can hold several inventory rows: one per text (semantic hash), prompt
label, provider and model. Synthesis used to read the oldest, so a re-inventory
after a prompt bump, a model change or a re-read was paid for and ignored.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from learnloop.clock import FrozenClock
from learnloop.content.synthesis.ai_contracts import SOURCE_UNIT_INVENTORY_PROMPT_VERSION
from learnloop.content.synthesis.source_coverage import build_source_coverage
from learnloop.content.synthesis.source_set_synthesis import _collect_inputs, create_study_map
from learnloop.content.synthesis.source_unit_inventory import best_inventory, run_unit_inventory
from learnloop.vault.loader import load_vault

from tests.source_inventory_helpers import FakeInventoryClient
from tests.source_set_synthesis_helpers import _CLOCK, FakeSynthesisClient, _setup


def _row(row_id: str, *, created_at: str, semantic_hash: str = "sha256:now", prompt: str = "p2",
         provider: str = "openai", model: str = "m2", profile: str = "combined") -> dict:
    return {
        "id": row_id,
        "unit_id": "u1",
        "unit_semantic_hash": semantic_hash,
        "inventory_profile": profile,
        "inventory_schema_version": 1,
        "prompt_version": prompt,
        "provider": provider,
        "model": model,
        "created_at": created_at,
        "inventory": {},
    }


def _choose(rows, *, provider="openai", model="m2"):
    chosen = best_inventory(rows, "u1", semantic_hash="sha256:now", prompt_version="p2",
                            provider=provider, model=model, profile="combined")
    return chosen["id"] if chosen else None


def test_current_text_wins_over_a_newer_row_for_old_text():
    rows = [
        _row("old_text_newer", created_at="2026-11-02", semantic_hash="sha256:before"),
        _row("current_text", created_at="2026-11-01"),
    ]
    assert _choose(rows) == "current_text"


def test_current_prompt_wins_then_current_provider_and_model():
    rows = [
        _row("old_prompt_newest", created_at="2026-11-03", prompt="p1"),
        _row("other_model", created_at="2026-11-02", model="m1"),
        _row("current", created_at="2026-11-01"),
    ]
    assert _choose(rows) == "current"
    # Without a current model on record, the newest current-prompt row wins.
    assert _choose(rows, provider=None, model=None) == "other_model"


def test_newest_breaks_ties_and_the_profile_rule_stays():
    rows = [
        _row("older", created_at="2026-11-01", model="m0"),
        _row("newer", created_at="2026-11-02", model="m1"),
        _row("narrow_current", created_at="2026-11-03", profile="semantic"),
    ]
    # A narrower profile never satisfies the combined request while a combined row exists.
    assert _choose(rows) == "newer"
    assert _choose([_row("narrow", created_at="2026-11-01", profile="semantic")]) == "narrow"
    assert _choose([]) is None


class _RevisedInventoryClient(FakeInventoryClient):
    """A later model whose inventory reads differently, so the test can see which row reached the prompt."""

    model = "fake-model-2"

    def run_source_unit_inventory(self, context):
        inventory = super().run_source_unit_inventory(context)
        inventory.outline_summary = "revised summary"
        return inventory


def _source_set(vault):
    return next(source_set for source_set in vault.source_sets if source_set.id == "set_la")


def _first_entry_summary(client: FakeSynthesisClient) -> str:
    entries = [entry for entry in client.calls[0].unit_inventories if entry["unit_id"] == "chapter_symmetry"]
    assert len(entries) == 1
    return entries[0]["inventory"]["outline_summary"]


def test_a_reinventory_by_a_newer_model_reaches_the_synthesis_prompt(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    later = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))
    run_unit_inventory(repo, "ext_text", "chapter_symmetry", role="primary_textbook", profile="combined",
                       client=_RevisedInventoryClient(), input_budget_tokens=20000, clock=later)

    client = FakeSynthesisClient()
    create_study_map(root, "set_la", client=client, brief={"depth": "intro"}, repository=repo, clock=_CLOCK)

    assert _first_entry_summary(client) == "revised summary"


def test_a_row_under_the_current_prompt_label_beats_an_older_label(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    current = repo.unit_inventories_for_revision("rev_text")[0]
    assert current["prompt_version"] == SOURCE_UNIT_INVENTORY_PROMPT_VERSION
    stale = dict(current["inventory"], outline_summary="summary under the old prompt")
    repo.insert_unit_inventory(
        id="inv_old_label", source_revision_id="rev_text", extraction_id="ext_text",
        unit_id="chapter_symmetry", unit_semantic_hash=current["unit_semantic_hash"],
        inventory_profile="combined", inventory_schema_version=current["inventory_schema_version"],
        prompt_version="source_unit_inventory_v0", provider=current["provider"], model=current["model"],
        inventory=stale, clock=FrozenClock(_CLOCK.now() - timedelta(days=30)),
    )

    client = FakeSynthesisClient()
    create_study_map(root, "set_la", client=client, brief={"depth": "intro"}, repository=repo, clock=_CLOCK)

    assert _first_entry_summary(client) != "summary under the old prompt"
    vault = load_vault(root)
    inputs = _collect_inputs(repo, vault, _source_set(vault))
    chosen = inputs.inventory_rows["rev_text:chapter_symmetry"]
    assert chosen["inventory_id"] == current["id"]
    assert chosen["extraction_id"] == "ext_text"
    assert inputs.unit_inventory_versions["rev_text:chapter_symmetry"].endswith(SOURCE_UNIT_INVENTORY_PROMPT_VERSION)


def test_coverage_reads_the_row_synthesis_reads(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    later = FrozenClock(datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC))

    class _ExerciseOnly(FakeInventoryClient):
        model = "fake-model-2"

        def run_source_unit_inventory(self, context):
            inventory = super().run_source_unit_inventory(context)
            inventory.claims = []
            inventory.coverage_claims = []
            return inventory

    run_unit_inventory(repo, "ext_text", "chapter_symmetry", role="primary_textbook", profile="combined",
                       client=_ExerciseOnly(), input_budget_tokens=20000, clock=later)
    vault = load_vault(root)
    coverage = build_source_coverage(repo, vault, _source_set(vault))
    inputs = _collect_inputs(repo, vault, _source_set(vault))

    assert inputs.unit_inventories[0]["inventory"]["claims"] == []
    assert "definition" not in coverage["members"][0]["units"][0]["inventory_evidence"]
