"""
Pytest configuration: sets fake env vars and patches Supabase BEFORE any app
module is imported, so create_client never fires against an empty URL.
"""
import os
from unittest.mock import MagicMock, patch

# ── 1. Fake credentials so supabase_client.py doesn't raise on import ──────────
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "sb_publishable_fake_key_for_tests")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "sb_secret_fake_key_for_tests")
os.environ.setdefault("NEWS_API_KEY", "fake-news-api-key")

# ── 2. Patch supabase.create_client before any router imports it ────────────────
_mock_sb = MagicMock()
patch("supabase.create_client", return_value=_mock_sb).start()

# Expose the shared mock so individual tests can configure return values.
import pytest

@pytest.fixture(autouse=False)
def mock_supabase():
    """Return the shared Supabase mock so tests can set .return_value etc."""
    _mock_sb.reset_mock(return_value=True, side_effect=True)
    return _mock_sb


# ── 3. Build the TestClient once per session ────────────────────────────────────
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from services.auth_utils import get_current_user

FAKE_USER = {"sub": "test-user-uuid-1234", "email": "test@example.com"}

def _fake_auth():
    return FAKE_USER

@pytest.fixture(scope="session")
def client():
    app.dependency_overrides[get_current_user] = _fake_auth
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def authed_headers():
    return {"Authorization": "Bearer fake-token"}
