"""
Shared pytest fixtures for E2E and chaos tests.

Two client fixtures are provided:
  - `client`: hits a live AlphaForge backend over HTTP (matches the
    BASE_URL convention already used by test_production_readiness.py /
    test_fullsuite_e2e.py). Use for straightforward request/response checks.
  - `app_client`: in-process ASGI client bound directly to the FastAPI `app`
    object, with the real startup/shutdown lifespan run around it. Required
    whenever a test uses unittest.mock.patch() to inject a fault — patching
    only affects objects in the current process, so a test that patches a
    module and then talks to a *separate* live server process would patch
    nothing and silently test nothing.
"""

import os
import sys
import uuid

import httpx
import pytest

BASE_URL = os.getenv("ALPHAFORGE_API_BASE_URL", "http://localhost:8000")
TIMEOUT = float(os.getenv("ALPHAFORGE_E2E_TIMEOUT", "45"))

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
async def client():
    """Async HTTP client against a running AlphaForge backend.

    Rate-limit bucketing is keyed on X-User-Id (falling back to Authorization,
    then "anonymous") — this is set to a value dedicated to this test suite so
    the rest of the suite's request volume doesn't share a bucket with, and
    get throttled by, real anonymous traffic or the DDoS test's own dedicated
    bucket. It only affects rate-limit bucketing, not auth identity (that's
    resolved separately from the Authorization header).
    """
    async with httpx.AsyncClient(
        base_url=BASE_URL, timeout=TIMEOUT, headers={"X-User-Id": "pytest-e2e-client"}
    ) as c:
        yield c


@pytest.fixture(scope="module")
def event_loop():
    """Module-scoped event loop so app_client's expensive lifespan (DB/Redis/
    market-data startup, ~10-15s) runs once per test module, not once per test."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def app_client():
    """In-process ASGI client bound to the real app, lifespan included."""
    from main import app

    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        # host must be in TRUSTED_HOSTS (default localhost/127.0.0.1) or
        # TrustedHostMiddleware rejects every request with 400.
        async with httpx.AsyncClient(
            transport=transport, base_url="http://localhost", timeout=TIMEOUT,
            headers={"X-User-Id": "pytest-app-client"},
        ) as c:
            yield c


@pytest.fixture
def test_user():
    """A fresh, unique test user for each test."""
    return {
        "user_id": str(uuid.uuid4()),
        "firebase_uid": str(uuid.uuid4()),
        "email": f"test-{uuid.uuid4()}@example.com",
        "display_name": "Test Trader",
    }
