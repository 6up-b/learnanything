"""What other test files use from ``tests/test_facet_reword_paths.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations


def _sidecar(paths):
    import learnloop_sidecar.handlers  # noqa: F401 - registers methods
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(paths.root)
    return ctx


def _call(ctx, name, params):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


SYMMETRY = "facet_symmetry_definition"
SYMMETRY_CLAIM = "A real square matrix A is symmetric exactly when it equals its transpose: A^T = A."
#: The span the appended member (``_bootstrap_and_add``: ``src_alt``/``rev_alt``) provides;
#: its role is whatever ``add_role`` the test gave the member.
NEW_SPAN = {"extraction_id": "ext_alt", "unit_id": "chapter_symmetry_alt", "span_id": "s1"}
#: A span of the bootstrap's ``primary_textbook`` member (``src_text``/``rev_text``).
TEXT_SPAN = {"extraction_id": "ext_text", "unit_id": "chapter_symmetry", "span_id": "s1"}


def _facet_restructure(operation: str = "update", target: str = SYMMETRY, *, citations=(NEW_SPAN,)):
    """The response a provider returns under the strict schema (validated, not constructed)."""

    from learnloop.content.synthesis.ai_contracts import AppendReconciliation

    def builder(_context, _n):
        return AppendReconciliation.model_validate({
            "summary": "the new source states the definition precisely",
            "restructures": [{
                "client_item_id": "reword_symmetry", "target_entity_type": "facet",
                "target_entity_id": target, "operation": operation,
                "expected_target_hash": "", "payload": {},
                "facet_wording": {
                    "kind": None, "claim": SYMMETRY_CLAIM, "description": "",
                    "preconditions": [], "postconditions": [], "applicability": [], "non_goals": [],
                    # The model's own role claim is ignored: the role comes from the extraction.
                    "provenance": [
                        {"revision_id": "", "source_id": "", "locator": "", "relation": "support",
                         "role": "primary_textbook", **span}
                        for span in citations
                    ],
                },
            }],
        })

    return builder
