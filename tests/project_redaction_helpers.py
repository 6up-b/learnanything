"""What other test files use from ``tests/test_project_redaction.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.project_support import TempRepo


AWS_KEY = "AKIAQWERTYUIOPASDFGH"
OPENAI_KEY = "sk-proj-Zx81kQ0mN3vB7cX2lP9oR4tY6uI1"
GITHUB_TOKEN = "ghp_aB3dE5fG7hJ9kL1mN3pQ5rS7tU9vW1xY3zA5"
ENV_SECRET = "hunter2-the-database-password-123"


def _hunk_header_secret_repo(tmp_path):
    repo = TempRepo(tmp_path / "repo")
    body = "".join(f"    step_{index} = {index}\n" for index in range(12))
    repo.write("conn.py", f'def connect(key="{OPENAI_KEY}"):\n{body}    return step_0\n')
    repo.commit("init", trailer=None)
    tail = "    total = step_0 + step_11\n    total *= 2\n    total -= step_5\n    total += step_7\n    return total\n"
    repo.write("conn.py", f'def connect(key="{OPENAI_KEY}"):\n{body}{tail}')
    repo.commit("Sum the first and last steps")
    return repo
