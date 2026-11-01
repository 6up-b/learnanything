"""Reader CA6b (Codex review F7): the second pane's router offers only what that pane runs.

Side by side's second pane leaves the open book's own views out of its palette
(*work through this*: the working posture closes side by side; *what matters
here?*: the Guide's reading path is the open book's). ``reader.route_intent``
with ``sidePane`` true offers the Decider the same actions, so a routed answer
never names an action the pane cannot run. The main pane's routing is
unchanged.

The Decider is a fake (``tests.router_model_fakes.FakeDecider``): no network.
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.reader import reader_intent as RI
from tests.helpers import append_config_toml
from tests.recap_fixtures import call, context
from tests.router_model_fakes import FakeDecider as _FakeDecider
from tests.test_reader_guidance import _setup


class FakeDecider(_FakeDecider):
    settings = SimpleNamespace(price_per_million_input=0.02)


BOOK_BOUND = {"work_through", "what_matters_here"}


def _ctx(root, decider):
    ctx = context(root)
    ctx.reader_intent_inline = True
    ctx.reader_intent_client_factory = lambda: decider
    return ctx


def _prefer(option: str):
    return lambda refs: {ref: (0.9 if ref == option else 0.1 / max(1, len(refs) - 1)) for ref in refs}


def _offered(decider) -> set[str]:
    (call_,) = decider.calls
    return set(call_["questions"][RI.QUESTION_NAME].options)


def test_the_second_pane_is_never_offered_the_open_books_own_views(tmp_path):
    vault, _repo = _setup(tmp_path)
    append_config_toml(vault.root, "\n[workbench]\nenabled = true\n\n[reading_paths]\nenabled = true\n")
    params = {"extractionId": "ext1", "spanIds": ["s1"], "text": "work through it", "quote": "q"}

    # The main pane: both are on offer (the switches are on).
    main = FakeDecider(choice=_prefer("work_through"))
    routed = call(_ctx(vault.root, main), "reader.route_intent", params)
    assert BOOK_BOUND <= _offered(main)
    assert routed["action"] == "work_through"

    # The second pane: neither is offered, so the Decider cannot name either.
    side = FakeDecider(choice=_prefer("work_through"))
    routed = call(_ctx(vault.root, side), "reader.route_intent", {**params, "sidePane": True})
    offered = _offered(side)
    assert offered and not (BOOK_BOUND & offered)
    assert offered == _offered(main) - BOOK_BOUND
    assert routed["action"] not in BOOK_BOUND
