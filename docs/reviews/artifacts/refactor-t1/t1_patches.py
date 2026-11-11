"""The two hand patches after the move (exact-pattern replacements): donors that patched their own globals."""
from pathlib import Path

def sub(path, old, new):
    p = Path(path); s = p.read_text()
    assert s.count(old) >= 1, (path, old)
    p.write_text(s.replace(old, new))

f = "tests/test_plan_first_transport_offer_grants.py"
sub(f, 'monkeypatch.setattr(sys.modules[__name__], "_DRAIN', 'monkeypatch.setattr(grants_helpers, "_DRAIN')
sub(f, "from tests.plan_first_transport_offer_grants_helpers import Harness\n",
    "from tests import plan_first_transport_offer_grants_helpers as grants_helpers\n"
    "from tests.plan_first_transport_offer_grants_helpers import Harness\n")
sub(f, "\nimport sys\n", "\n")
assert "sys." not in Path(f).read_text()

f = "tests/test_rospeed_ad_link.py"
sub(f, """    def install(self, patch) -> None:
        import sys

        real = M.sigmoid

        def charged(x):
            self.spent += int(np.size(x))
            return real(x)

        for module in (V, M, sys.modules[__name__]):""", """    def install(self, patch) -> None:
        from tests import rospeed_ad_link_helpers

        real = M.sigmoid

        def charged(x):
            self.spent += int(np.size(x))
            return real(x)

        # The landing code's copy (the ``_old_*`` functions) reads ``sigmoid`` from its helper module.
        for module in (V, M, rospeed_ad_link_helpers):""")
print("patched")

sub("tests/conftest.py", '''# Fails a test that leaves a thread running (tests/thread_guard.py).
pytest_plugins = ["tests.thread_guard"]
''', '''# Fails a test that leaves a thread running (tests/thread_guard.py).
pytest_plugins = ["tests.thread_guard"]

# The tests/*_helpers.py modules hold what test files share, assertions included (refactor step T1 moved them out
# of the test files): pytest rewrites their asserts as it does a test file's, so a failure still shows its operands.
pytest.register_assert_rewrite(*sorted(f"tests.{path.stem}" for path in Path(__file__).parent.glob("*_helpers.py")))
''')

# The two RW2b base sequences also run inside `git archive 7d4c5f4ce`'s tree, where StuckFake is still in
# test_stuck_prompt (tests/test_test_layout.py allows exactly this fallback).
for f in ("tests/rw2b_fix10_base_sequence.py", "tests/rw2b_fix11_base_sequence.py"):
    sub(f, "    from tests.stuck_prompt_helpers import StuckFake\n", """    try:
        from tests.stuck_prompt_helpers import StuckFake
    except ModuleNotFoundError:  # the base commit's tree, from before refactor step T1
        from tests.test_stuck_prompt import StuckFake
""")
print("conftest, base sequences")
