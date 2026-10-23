"""Reader RW5a fix round 5 (orchestrator): the verify's findings under the scope ruling.

The source-check (spec §8.3 step 3) and admission tests these rounds added were removed
with that machinery by the owner's scope decision of 2026-10-21; their successors
are in tests/test_figures_scope_redesign.py. What stays here still holds.

See docs/reviews/reader-rw5a-codex-review.md, "Fix round 5 (orchestrator)".

"Checked" certifies that the figure's definition equals the source equation
exactly and that the displayed, source-labelled content IS that definition;
not that every float pixel is exact real arithmetic. So the branch case is
closed by construction (a checked definition's piecewise conditions compare
a bare variable or parameter with a binary64-exact literal); the switch and
the routes are reread before every author and verifier call; a stored
"verified" carries its certification version and an older one shows, and is
reused, as an illustration; and a percent readout's scaled value is checked.
"""

from __future__ import annotations

import json
import threading

import pytest

from learnloop.content.authoring import pf_sandbox
from learnloop.db.repositories import Repository
from learnloop.figures import grammar as G
from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.figures import spec as S
from learnloop.figures import verify as V
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import (
    EQUATION_TEXT,
    EXTRACTION,
    AuthorFake,
    VerifierFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
    sandbox_ready,
)
from tests.test_figures_codex_review import _equivalence
from tests.test_figures_switch_off import _switch

needs_sandbox = pytest.mark.skipif(not sandbox_ready(), reason="bubblewrap is not available here")


# ---------------------------------------------------------------------------
# Finding 1 (branch case): exact conditions by construction
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# High 3: the switch and the routes, reread before every call
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# High 4: the certification version
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Medium 5: formatting-derived numbers
# ---------------------------------------------------------------------------

def test_a_percent_readout_that_overflows_when_scaled_fails_structure():
    spec = {"spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": "a big share",
            "panels": [{"kind": "readout", "label": "share", "expr": "10^307", "format": "percent"}]}
    report = V.verify_numerics(S.parse_spec(spec))
    assert report.outcome == V.FAILED and "as a percent" in report.reason
    spec["panels"][0]["format"] = "number"
    assert V.verify_numerics(S.parse_spec(spec)).outcome == V.ILLUSTRATIVE
