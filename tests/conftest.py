"""Shared test setup."""

import pytest

from backend import config

TEST_CLIENT_ID = "test-client-id.apps.googleusercontent.com"


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Every test gets its own empty user database and a known client ID."""
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "test_users.db"))
    monkeypatch.setattr(config, "GOOGLE_CLIENT_ID", TEST_CLIENT_ID)
