"""What other test files use from ``tests/test_probe_surface_mint.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.diagnosis.ai_contracts import ProbeInstanceSurface, ProbeInstanceSurfaces

from tests.structured_ai import StructuredClientFake


class FakeSurfacesClient(StructuredClientFake):
    """AI provider double exposing run_probe_instance_surfaces."""

    model = "fake-model-1"

    def __init__(self, *, surfaces=None):
        self._surfaces = surfaces
        self.calls: list[object] = []

    def run_probe_instance_surfaces(self, context):
        self.calls.append(context)
        if self._surfaces is not None:
            return ProbeInstanceSurfaces(surfaces=self._surfaces)
        return ProbeInstanceSurfaces(
            surfaces=[
                ProbeInstanceSurface(
                    surface_suffix=f"fake_{index}",
                    prompt_md=(
                        f"Surface {index}: considering {context.learning_object_title}, "
                        f"what does {context.target_facets[0]} require here?"
                    ),
                    expected_answer_md=f"A robust learner states the decisive reason {index}.",
                )
                for index in range(context.count)
            ]
        )
