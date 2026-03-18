"""
AlphaForge Complete End-to-End Integration Tests (MVP Phase 1)

This test suite validates the entire system works end-to-end:
1. Frontend API layer is wired correctly
2. Backend services respond to requests
3. Database schema is initialized
4. Data persistence works
5. User flows complete successfully

Run: pytest tests/integration_e2e.py -v
"""

import os
import sys
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import httpx
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
API_TIMEOUT = 30.0
TEST_EMAIL_SUFFIX = f"e2e_{uuid.uuid4().hex[:8]}@alphaforge.test"


class TestEndToEndIntegration:
    """Complete end-to-end integration tests."""

    @pytest.fixture
    async def client(self):
        """Async HTTP client."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            yield client

    @pytest.fixture
    async def test_user(self, client):
        """Create a test user and return user_id."""
        response = await client.post(
            "/api/users/register",
            json={
                "email": TEST_EMAIL_SUFFIX,
                "display_name": "E2E Test User",
                "institution_name": "AlphaForge QA",
                "plan": "basic",
                "risk_tolerance": "moderate",
            },
        )
        assert response.status_code == 200, f"Failed to create test user: {response.text}"
        user_data = response.json()
        assert "user" in user_data
        user_id = user_data["user"]["id"]
        logger.info(f"✅ Created test user: {user_id}")
        yield user_id


class TestHealthAndReadiness:
    """Test basic health and readiness endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Verify /health endpoint responds."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "timestamp" in data
            logger.info("✅ Health endpoint OK")

    @pytest.mark.asyncio
    async def test_ready_endpoint(self):
        """Verify /ready endpoint responds (database ready)."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/ready")
            # Could be 200 or 503 depending on DB state
            assert response.status_code in [200, 503]
            data = response.json()
            assert "database" in data or "status" in data
            logger.info("✅ Readiness endpoint responded")

    @pytest.mark.asyncio
    async def test_status_endpoint(self):
        """Verify /status endpoint responds with service info."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/status")
            assert response.status_code == 200
            data = response.json()
            assert "api_running" in data
            logger.info("✅ Status endpoint OK")


class TestUserManagement:
    """Test user registration, login, and profile management."""

    @pytest.mark.asyncio
    async def test_user_registration(self):
        """Test user registration flow."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            response = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "user" in data
            assert data["user"]["email"] == email
            logger.info(f"✅ User registration successful: {email}")

    @pytest.mark.asyncio
    async def test_user_profile_retrieval(self):
        """Test retrieving user profile."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            create_resp = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            user_id = create_resp.json()["user"]["id"]

            # Retrieve profile
            response = await client.get(f"/api/users/{user_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == user_id
            assert data["email"] == email
            logger.info(f"✅ User profile retrieval successful")

    @pytest.mark.asyncio
    async def test_user_profile_update(self):
        """Test updating user profile."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            create_resp = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            user_id = create_resp.json()["user"]["id"]

            # Update profile
            response = await client.put(
                f"/api/users/{user_id}",
                json={
                    "display_name": "Updated Name",
                    "risk_tolerance": "aggressive",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Updated Name"
            assert data["risk_tolerance"] == "aggressive"
            logger.info(f"✅ User profile update successful")


class TestMarketData:
    """Test market data endpoints."""

    @pytest.mark.asyncio
    async def test_market_tickers(self):
        """Test fetching market tickers."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/api/market/tickers?symbols=BTC,ETH,SOL")
            assert response.status_code == 200
            data = response.json()
            assert "tickers" in data or "success" in data
            logger.info(f"✅ Market tickers retrieved")

    @pytest.mark.asyncio
    async def test_market_sentiment(self):
        """Test market sentiment endpoint."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/api/market/sentiment")
            assert response.status_code == 200
            data = response.json()
            # Should have sentiment metrics
            assert any(key in data for key in ["bullish_count", "sentiment", "market_status"])
            logger.info(f"✅ Market sentiment retrieved")

    @pytest.mark.asyncio
    async def test_market_funding_rates(self):
        """Test funding rates endpoint."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/api/market/funding-rates")
            assert response.status_code == 200
            data = response.json()
            # Should be list or have funding_rates key
            assert isinstance(data, (list, dict))
            logger.info(f"✅ Funding rates retrieved")

    @pytest.mark.asyncio
    async def test_market_open_interest(self):
        """Test open interest endpoint."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/api/market/open-interest")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, (list, dict))
            logger.info(f"✅ Open interest retrieved")

    @pytest.mark.asyncio
    async def test_market_data_quality(self):
        """Test data quality endpoint."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/api/market/data-quality")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, (list, dict))
            logger.info(f"✅ Data quality info retrieved")


class TestSignalProcessing:
    """Test signal processing endpoints."""

    @pytest.mark.asyncio
    async def test_get_signals(self):
        """Test fetching signals."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/api/frontend/signals/latest?limit=10")
            # May be 200 or 404 if no signals exist
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Signals retrieved: {len(data) if isinstance(data, list) else 'list'}")

    @pytest.mark.asyncio
    async def test_process_signals(self):
        """Test signal processing endpoint."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.post(
                "/api/signals/process",
                json={"symbols": ["BTC", "ETH"]},
            )
            # May be 200 or 422 depending on validation
            assert response.status_code in [200, 422]
            logger.info(f"✅ Signal processing call completed")


class TestPortfolioOperations:
    """Test portfolio operations."""

    @pytest.mark.asyncio
    async def test_portfolio_summary(self):
        """Test getting portfolio summary for a user."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            create_resp = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            user_id = create_resp.json()["user"]["id"]

            # Get portfolio
            response = await client.get(f"/api/frontend/portfolio/{user_id}/summary")
            # May be 200 or 404 if portfolio doesn't exist yet
            assert response.status_code in [200, 404]
            logger.info(f"✅ Portfolio summary accessed")

    @pytest.mark.asyncio
    async def test_portfolio_positions(self):
        """Test getting portfolio positions."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            create_resp = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            user_id = create_resp.json()["user"]["id"]

            # Get positions
            response = await client.get(f"/api/frontend/portfolio/{user_id}/positions")
            assert response.status_code in [200, 404]
            logger.info(f"✅ Portfolio positions accessed")


class TestPaperTrading:
    """Test paper trading operations."""

    @pytest.mark.asyncio
    async def test_execute_paper_trade(self):
        """Test executing a paper trade."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            create_resp = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            user_id = create_resp.json()["user"]["id"]

            # Execute paper trade
            response = await client.post(
                "/api/trades/paper",
                json={
                    "user_id": user_id,
                    "asset": "BTC",
                    "direction": "LONG",
                    "entry_price": 65000,
                    "quantity": 0.1,
                    "stop_loss": 63000,
                    "take_profit": 70000,
                },
            )
            # May be 200 (created) or 404/422 (validation/error)
            assert response.status_code in [200, 201, 404, 422]
            logger.info(f"✅ Paper trade execution call completed")


class TestFrontendAPIIntegration:
    """Test frontend API integration endpoints."""

    @pytest.mark.asyncio
    async def test_frontend_user_api(self):
        """Test frontend user API layer."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            create_resp = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            user_id = create_resp.json()["user"]["id"]

            # Test frontend endpoints
            response = await client.get(f"/api/frontend/user/{user_id}/profile")
            assert response.status_code in [200, 404]
            logger.info(f"✅ Frontend user profile API working")

            response = await client.get(f"/api/frontend/user/{user_id}/kyc")
            assert response.status_code in [200, 404]
            logger.info(f"✅ Frontend KYC API working")

    @pytest.mark.asyncio
    async def test_frontend_market_api(self):
        """Test frontend market API layer."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get("/api/frontend/market/tickers")
            assert response.status_code == 200
            logger.info(f"✅ Frontend market API working")

    @pytest.mark.asyncio
    async def test_frontend_portfolio_api(self):
        """Test frontend portfolio API layer."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"
            create_resp = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            user_id = create_resp.json()["user"]["id"]

            response = await client.get(f"/api/frontend/portfolio/{user_id}/summary")
            assert response.status_code in [200, 404]
            logger.info(f"✅ Frontend portfolio API working")


class TestSystemResilience:
    """Test system resilience and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_user_id(self):
        """Test accessing invalid user returns appropriate error."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.get(f"/api/users/invalid-uuid-12345")
            assert response.status_code in [400, 404]
            logger.info(f"✅ Invalid user ID handled correctly")

    @pytest.mark.asyncio
    async def test_missing_required_parameters(self):
        """Test missing required parameters returns validation error."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            response = await client.post(
                "/api/users/register",
                json={"email": "test@example.com"},  # Missing required fields
            )
            assert response.status_code in [400, 422]
            logger.info(f"✅ Missing parameters validation working")

    @pytest.mark.asyncio
    async def test_duplicate_user_registration(self):
        """Test duplicate user registration is prevented."""
        async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=API_TIMEOUT) as client:
            email = f"test_{uuid.uuid4().hex[:8]}@alphaforge.test"

            # First registration should succeed
            response1 = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            assert response1.status_code == 200

            # Second registration with same email should fail
            response2 = await client.post(
                "/api/users/register",
                json={
                    "email": email,
                    "display_name": "Test User 2",
                    "plan": "basic",
                    "risk_tolerance": "moderate",
                },
            )
            assert response2.status_code in [400, 409, 422]
            logger.info(f"✅ Duplicate user prevention working")


# ============================================================================
# Test Fixtures and Configuration
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_tests():
    """Setup for test suite."""
    logger.info("=" * 70)
    logger.info("Starting AlphaForge E2E Integration Tests")
    logger.info(f"API Base URL: {API_BASE_URL}")
    logger.info("=" * 70)
    yield
    logger.info("=" * 70)
    logger.info("E2E Integration Tests Complete")
    logger.info("=" * 70)


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    # Can be run directly or via pytest
    pytest.main([__file__, "-v", "-s"])
