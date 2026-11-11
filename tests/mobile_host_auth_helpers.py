"""What other test files use from ``tests/test_mobile_host_auth.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

import pytest
from starlette.testclient import TestClient

from learnloop import capture
from learnloop.db.repositories import Repository
from learnloop_mobile.config import MobileConfig
from learnloop_mobile.host import create_app

from tests.helpers import create_basic_vault


@pytest.fixture
def mobile(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    config = MobileConfig(enabled=True, vault=paths.root, hostname="desktop.tail.ts.net",
                          owner_login="owner@example.com")
    app = create_app(config)
    repo = Repository.attach(paths.sqlite_path)
    pending = capture.create_pairing(repo, scope="app")
    device = capture.exchange_pairing(repo, secret=pending["secret"])
    headers = {"Tailscale-User-Login": config.owner_login,
               "Authorization": f"Bearer {device['token']}"}
    with TestClient(app, base_url=f"https://{config.hostname}") as client:
        yield client, app.state.host, repo, device, headers
