"""UX-1: a unit's inventory output allowance (UX journey audit walks, 2026-11-18).

Two persona walks added the sample chapter as a web page and got "Questions for
this article need another try", with "inventory output exceeded its configured
token budget" in the card's details; Retry failed the same way. The page is one
unit of one window. The model was told 3000 tokens and wrote about 2900 (by the
same four-characters-a-token estimate), but it was charged for the stored copy,
which carries the ids the service writes after the call (about 300 tokens more),
and that copy was over 3000. The window had been saved before the check, so
Retry reused it and failed at the same point.

The rule now: the configured amount is one window's. Each window's request is
held to it and a window is charged for what the model wrote; a unit is allowed
that amount per window; a reused window is not charged again. Every model call
here is a house fake.
"""

from __future__ import annotations

import pytest

from learnloop.ai.execution import output_limit
from learnloop.content.synthesis.ai_contracts import (
    InventoryClaim,
    InventoryConceptMention,
    SourceUnitInventory,
)
from learnloop.content.synthesis.source_unit_inventory import (
    InventoryValidationError,
    build_inventory_windows,
    run_unit_inventory,
)

from tests.source_inventory_helpers import _CLOCK, _block, _ir, _persist, _register_revision, _repo
from tests.structured_ai import StructuredClientFake

BUDGET = 1000  # the smallest per-window amount Settings accepts
CHARS_PER_TOKEN = 4  # the estimate the inventory charges by when a provider reports no usage
ITEMS = 6  # concept mentions, and as many claims, in each reply


def _sized_inventory(context, tokens: int) -> SourceUnitInventory:
    """A valid reply whose own JSON is ``tokens`` by the estimate: ``ITEMS``
    concept mentions and as many claims with the model's short ids, every one
    citing the window's first span, padded in the outline summary."""

    span = context.unit_view["blocks"][0]["span_id"]
    reply = SourceUnitInventory(
        unit_id=context.unit_id,
        semantic_hash=context.semantic_hash,
        concept_mentions=[InventoryConceptMention(mention_id=f"m{i}", name=f"term {i}", span_ids=[span]) for i in range(ITEMS)],
        claims=[
            InventoryClaim(claim_id=f"c{i}", statement=f"claim {i}", concept_mention_ids=[f"m{i}"], span_ids=[span])
            for i in range(ITEMS)
        ],
    )
    room = tokens * CHARS_PER_TOKEN - len(reply.model_dump_json())
    assert room > 0, "the base reply is larger than the size asked for"
    reply.outline_summary = "x" * room
    assert len(reply.model_dump_json()) // CHARS_PER_TOKEN == tokens
    return reply


class SizedInventoryClient(StructuredClientFake):
    """Answers each window with a reply of a chosen size and records the
    generation limit each request was sent under. ``size`` maps the request's
    limit to the reply's size in tokens."""

    model = "fake-model-1"
    provider_type = "codex"

    def __init__(self, size):
        self.size = size
        self.limits: list[int | None] = []
        self.windows: list[int] = []

    def run_source_unit_inventory(self, context):
        limit = output_limit()
        self.limits.append(limit)
        self.windows.append(context.unit_view["window_ordinal"])
        return _sized_inventory(context, self.size(limit))


def _one_unit(tmp_path, blocks):
    repo = _repo(tmp_path)
    _register_revision(repo)
    ir = _ir([("u1", "Document", blocks, "sha256:page", 1)])
    _persist(repo, ir, revision_id="rev1", extraction_id="ext1")
    return repo, ir


def _run(repo, client, *, input_budget_tokens=20000, output_budget_tokens=BUDGET):
    return run_unit_inventory(
        repo, "ext1", "u1", role="reference", client=client, clock=_CLOCK,
        input_budget_tokens=input_budget_tokens, output_budget_tokens=output_budget_tokens,
    )


def test_a_window_that_keeps_to_its_limit_is_not_charged_for_the_ids_the_service_adds(tmp_path):
    # The walks' case: one unit, one window, the model writes just under the
    # limit it was given. The stored copy (with the service's ids) is over it.
    repo, ir = _one_unit(tmp_path, [_block("s1", "A symmetric matrix is orthogonally diagonalizable.")])
    assert len(build_inventory_windows(ir, "u1", input_budget_tokens=20000)) == 1
    client = SizedInventoryClient(lambda limit: limit - 10)

    result = _run(repo, client)

    assert client.limits == [BUDGET]
    assert len(result.inventory.claims) == ITEMS
    assert all(claim.claim_id.startswith("u1|w0|") for claim in result.inventory.claims)
    # The stored copy is larger than what the model wrote: the ids are ours.
    assert len(result.inventory.model_dump_json()) // CHARS_PER_TOKEN > BUDGET


def test_a_unit_long_enough_for_several_windows_is_allowed_one_windows_amount_for_each(tmp_path):
    # Three sections of about 750 tokens each under a 1000-token input budget:
    # three windows. Each reply is a modest 600 tokens, 1800 in all, more than
    # one window's 1000.
    blocks = [_block(f"s{i}", ("word " * 600).strip(), section=(f"section {i}",)) for i in range(1, 4)]
    repo, ir = _one_unit(tmp_path, blocks)
    assert len(build_inventory_windows(ir, "u1", input_budget_tokens=1000)) == 3
    client = SizedInventoryClient(lambda limit: 600)

    result = _run(repo, client, input_budget_tokens=1000)

    assert client.windows == [0, 1, 2]
    # No window is sent with more than one window's amount.
    assert client.limits == [BUDGET, BUDGET, BUDGET]
    assert len(result.inventory.claims) == 3 * ITEMS
    assert result.usage["calls"] == 3


@pytest.mark.parametrize("windows", [1, 3])
def test_after_a_window_writes_past_its_limit_retry_goes_on_from_where_it_stopped(tmp_path, windows):
    # A window that writes past its limit still fails its unit: the cap on a
    # runaway reply stays. It was paid for and is saved, so Retry reuses it
    # without charging it again, asks only for the windows not yet answered,
    # and finishes, instead of failing at the same point every time.
    blocks = [_block(f"s{i}", ("word " * 600).strip(), section=(f"section {i}",)) for i in range(1, windows + 1)]
    repo, _ir_unused = _one_unit(tmp_path, blocks)
    replies = iter([1300] + [600] * (windows - 1) + [600] * windows)
    client = SizedInventoryClient(lambda limit: next(replies))

    with pytest.raises(InventoryValidationError, match="configured token budget"):
        _run(repo, client, input_budget_tokens=1000)
    assert len(client.limits) == 1

    result = _run(repo, client, input_budget_tokens=1000)

    assert result.cache_hit is False
    assert result.usage["reused_windows"] == 1
    assert len(client.limits) == windows  # the first window was not asked again
    assert len(result.inventory.claims) == ITEMS * windows


def test_a_build_that_stopped_does_not_show_the_internal_reason_on_the_library_card(tmp_path):
    from learnloop.content.pipeline.add_source import AddSourceOptions, add_source, source_status_line
    from learnloop.vault.loader import load_vault

    from tests.ux_phase1_auto_build_helpers import _jobs
    from tests.ux_phase1_support import CLOCK, fake_services, fresh_library, grant_consent, write_book

    internal = "inventory output exceeded its configured token budget"

    class OverBudget(StructuredClientFake):
        model = "fake-model-1"
        provider_type = "codex"

        def run_source_unit_inventory(self, context):
            raise InventoryValidationError(internal)

    root = fresh_library(tmp_path)
    grant_consent(root)
    repo, jobs = _jobs(root, fake_services(inventory_client_factory=lambda ctx: OverBudget()))
    item = add_source(load_vault(root), jobs, str(write_book(tmp_path)), AddSourceOptions(), clock=CLOCK)

    line = source_status_line(repo, load_vault(root), item["source_id"])

    assert line["text"].endswith("need another try") and line["action"] == {"kind": "retry", "label": "Retry"}
    shown = " ".join(str(part) for part in (line["text"], line["details"])).lower()
    for word in ("inventory", "token", "budget"):
        assert word not in shown, (word, line)
    assert line["details"], "the details still say something plain"
    # The reason stays with the job, where Imports & builds shows it on demand.
    failed = [job for job in repo.ingest_jobs_by_types(("inventory",)) if job["status"] == "failed"]
    assert failed and failed[0]["error"]["message"] == internal
