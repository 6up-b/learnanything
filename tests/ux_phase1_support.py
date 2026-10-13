"""Shared fakes and builders for the UX Phase 1 tests (docs/specs/ux_learnloop_v1.md §6).

Everything here is offline: sources are local Markdown or a blank PDF written
with pypdf, extraction is the real local text path, and every model call goes to
the house fakes (``FakeInventoryClient``, ``FakeSynthesisClient``). The
authoring-route check is a seam on ``RunnerServices`` so a test decides whether
an AI is "connected" without touching Codex or a key.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from learnloop.bootstrap import create_vault
from learnloop.clock import FrozenClock
from learnloop.content.pipeline.add_source import AuthoringRoute
from learnloop.content.pipeline.runner import RunnerServices
from learnloop.db.repositories import Repository
from learnloop.ops.settings_store import apply_config_updates
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.test_source_append import FakeAppendClient
from tests.test_source_inventory import FakeInventoryClient
from tests.test_source_set_synthesis import FakeSynthesisClient

CLOCK = FrozenClock(datetime(2026, 10, 13, 9, 0, 0, tzinfo=UTC))

_PARAGRAPH = (
    "A probability is a number between zero and one that measures how likely an "
    "event is, and the naive definition counts equally likely outcomes."
)

BOOK_MARKDOWN = "\n\n".join(
    [
        "# Contents",
        "1 Probability and counting. 2 Conditional probability. 3 Random variables.",
        "# 1 Probability and counting",
        _PARAGRAPH,
        _PARAGRAPH,
        "# 2 Conditional probability",
        "Conditioning updates a probability in the light of new evidence, " + _PARAGRAPH,
        "# 3 Random variables",
        "A random variable assigns a number to every outcome, " + _PARAGRAPH,
        "# 4 Expectation",
        "The expectation of a random variable is its probability-weighted average, " + _PARAGRAPH,
    ]
) + "\n"


def write_book(tmp_path: Path, name: str = "probability_book.md", text: str = BOOK_MARKDOWN) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def write_pdf(tmp_path: Path, name: str = "blitzstein.pdf", *, title: str | None = "Probability") -> Path:
    """A real (blank, two-page) PDF; the metadata title is what Add shows."""

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    if title is not None:
        writer.add_metadata({"/Title": title})
    buffer = io.BytesIO()
    writer.write(buffer)
    path = tmp_path / name
    path.write_bytes(buffer.getvalue())
    return path


def fresh_library(tmp_path: Path, *, name: str = "LearnLoop", scope_cap: int | None = 150) -> Path:
    """A brand-new library the way first run makes one: no subject, no level.

    ``scope_cap`` shrinks ``quick_add_scope_input_tokens`` so the tiny test book
    is "bigger than one build" and reading-order scoping is exercised."""

    root = create_vault(tmp_path / name).root
    updates: dict[tuple[str, ...], Any] = {}
    if scope_cap is not None:
        updates[("ingest", "budgets", "quick_add_scope_input_tokens")] = scope_cap
    if updates:
        apply_config_updates(root / "learnloop.toml", updates)
    return root


def set_config(root: Path, updates: dict[tuple[str, ...], Any]) -> None:
    apply_config_updates(root / "learnloop.toml", updates)


def grant_consent(root: Path, key: str = "codex") -> None:
    set_config(root, {("ai", "consent", key, "granted_at"): "2026-10-13T09:00:00Z"})


def route(*, ready: bool = True, provider: str = "codex_medium", subscription: bool = True,
          consent_key: str = "codex", message: str | None = None) -> AuthoringRoute:
    return AuthoringRoute(
        provider=provider,
        ready=ready,
        message=message,
        subscription=subscription,
        consent_key=consent_key,
    )


class FakeBookSynthesisClient(FakeSynthesisClient):
    """The house synthesis fake that also answers the append lane, so the
    chapters a progressive build adds really reconcile into the book's map
    (the bootstrap-only fake fails every later chapter)."""

    def __init__(self, *, on_append=None, **kwargs: Any):
        super().__init__(**kwargs)
        self.append = FakeAppendClient()
        self.on_append = on_append

    def run_append_reconciliation(self, context):
        if self.on_append is not None:
            self.on_append(context)
        return self.append.run_append_reconciliation(context)


class Calls:
    """Counts the model clients a test's builds create and call."""

    def __init__(self) -> None:
        self.inventory: list[FakeInventoryClient] = []
        self.synthesis: list[FakeBookSynthesisClient] = []

    @property
    def inventory_calls(self) -> int:
        return sum(len(client.calls) for client in self.inventory)

    @property
    def synthesis_calls(self) -> int:
        return sum(len(client.calls) + len(client.append.calls) for client in self.synthesis)


def fake_services(authoring: AuthoringRoute | None = None, *, calls: Calls | None = None,
                  route_holder: list[AuthoringRoute] | None = None, on_append=None,
                  **overrides: Any) -> RunnerServices:
    chosen = authoring or route()
    seen = calls or Calls()

    def inventory(ctx):
        client = FakeInventoryClient()
        seen.inventory.append(client)
        return client

    def synthesis(ctx):
        client = FakeBookSynthesisClient(on_append=on_append)
        seen.synthesis.append(client)
        return client

    factories: dict[str, Any] = {
        "inventory_client_factory": inventory,
        "synthesis_client_factory": synthesis,
        "authoring_route_factory": (lambda ctx: route_holder[0]) if route_holder else (lambda ctx: chosen),
    }
    factories.update(overrides)
    return RunnerServices(**factories)


def repository(root: Path) -> Repository:
    vault = load_vault(root)
    return Repository(VaultPaths(vault.root, vault.config).sqlite_path)
