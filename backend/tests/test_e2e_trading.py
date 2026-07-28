"""
End-to-end integration tests for trading flow.
Tests complete user journey from registration to trade execution and closure.

Auth note: whether real Firebase Admin credentials are present varies by
environment. When they are, firebase_config.verify_firebase_token requires a
real, verifiable ID token for any request that supplies an Authorization
header — a synthetic bearer token gets rejected with 401 regardless of the
ALLOW_UNAUTHENTICATED_DEV flag. The one identity these tests can reliably
authenticate as, everywhere, is "demo-user": ALLOW_UNAUTHENTICATED_DEV's
missing-header fallback returns that UID without touching Firebase at all.
So every request below is sent with NO Authorization header, and test_user's
user_id is fixed to "demo-user" to match it.
"""

import pytest
import asyncio
import uuid


@pytest.fixture
def test_user():
    """Test user whose id matches the dev-bypass identity (overrides the
    conftest.py version, which uses a random UUID that would fail the
    require_self_or_admin check under the no-Authorization-header bypass)."""
    return {
        "user_id": "demo-user",
        "firebase_uid": "demo-user",
        "email": f"test-{uuid.uuid4()}@example.com",
        "display_name": "Test Trader",
    }


class TestE2ETradingFlow:
    """Complete trading flow E2E tests."""

    @pytest.mark.asyncio
    async def test_user_registration_to_first_trade(self, client, test_user):
        """Test complete flow: register → setup → trade → close."""
        # Step 1: User registration
        register_response = await client.post("/api/users/register", json={
            "email": test_user["email"],
            "display_name": test_user["display_name"],
            "plan": "free",
        })
        assert register_response.status_code == 200
        user_data = register_response.json()
        assert user_data["success"] is True

        # Step 2: Get portfolio summary
        portfolio_response = await client.get(
            f"/api/portfolio/{test_user['user_id']}"
        )
        assert portfolio_response.status_code == 200
        portfolio = portfolio_response.json()
        initial_balance = portfolio.get("starting_balance", 100000)

        # Step 3: Get available signals
        signals_response = await client.get(
            "/api/signals?limit=5"
        )
        assert signals_response.status_code == 200
        signals = signals_response.json()
        if isinstance(signals, dict):
            signals = signals.get("signals", [])

        # Step 4: Execute a paper trade
        signal_id = signals[0]["id"] if signals else "sig-fallback"
        trade_response = await client.post(
            "/api/trades/paper",
            json={
                "user_id": test_user["user_id"],
                "signal_id": signal_id,
                "asset": "BTC",
                "direction": "LONG",
                "quantity": 0.5,
                "entry_price": 50000,
            },
        )
        assert trade_response.status_code == 200
        trade_data = trade_response.json()
        assert trade_data["success"] is True
        trade_id = trade_data.get("trade_id")

        # Step 5: Verify position exists
        positions_response = await client.get(
            f"/api/portfolio/{test_user['user_id']}/positions"
        )
        assert positions_response.status_code == 200

        # Step 6: Get updated portfolio (should reflect unrealized P&L)
        updated_portfolio = await client.get(
            f"/api/portfolio/{test_user['user_id']}"
        )
        assert updated_portfolio.status_code == 200

        # Step 7: Close the trade
        close_response = await client.post(
            f"/api/trades/paper/{trade_id}/close",
            params={"exit_price": 51000}
        )
        assert close_response.status_code == 200
        closed_trade = close_response.json()
        assert closed_trade.get("success") is True
        assert closed_trade["data"]["pnl"] is not None

        # Step 8: Verify trade history
        trades_response = await client.get(
            "/api/trades/paper",
            params={"user_id": test_user["user_id"]}
        )
        assert trades_response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_trades_same_user(self, client, test_user):
        """Test user can execute multiple concurrent trades."""
        assets = ["BTC", "ETH", "SOL"]

        # Execute multiple trades concurrently
        tasks = [
            client.post(
                "/api/trades/paper",
                json={
                    "user_id": test_user["user_id"],
                    "signal_id": f"sig-{asset}",
                    "asset": asset,
                    "direction": "LONG",
                    "quantity": 0.1,
                    "entry_price": 50000,
                }
            )
            for asset in assets
        ]

        responses = await asyncio.gather(*tasks)

        # Verify all trades executed successfully
        for response in responses:
            assert response.status_code == 200
            assert response.json()["success"] is True

        # Verify all trades exist in portfolio
        positions_response = await client.get(
            f"/api/portfolio/{test_user['user_id']}/positions"
        )
        assert positions_response.status_code == 200

    @pytest.mark.asyncio
    async def test_trade_pnl_calculation_accuracy(self, client, test_user):
        """Verify P&L calculations are accurate including slippage."""
        entry_price = 50000.0
        exit_price = 51000.0
        quantity = 1.0
        expected_slippage_pct = 0.001  # 0.1%

        trade_response = await client.post(
            "/api/trades/paper",
            json={
                "user_id": test_user["user_id"],
                "signal_id": "sig-pnl",
                "asset": "BTC",
                "direction": "LONG",
                "quantity": quantity,
                "entry_price": entry_price,
            }
        )
        assert trade_response.status_code == 200
        trade_id = trade_response.json()["trade_id"]

        # Close trade
        close_response = await client.post(
            f"/api/trades/paper/{trade_id}/close",
            params={"exit_price": exit_price}
        )
        assert close_response.status_code == 200
        closed_trade = close_response.json()

        # Verify P&L accounting for slippage
        # Entry slippage: price goes up (worse for buyer) = 50000 * 1.001 = 50050
        # Exit slippage: price goes down (worse for seller) = 51000 * 0.999 = 50949
        actual_pnl = closed_trade["data"]["pnl"]
        expected_pnl = (exit_price * (1 - expected_slippage_pct) -
                       entry_price * (1 + expected_slippage_pct)) * quantity

        assert actual_pnl == pytest.approx(expected_pnl, rel=0.05)


class TestE2EAuthFlow:
    """End-to-end authentication flow tests."""

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_user_data(self, client):
        """Verify a caller can never read another user's portfolio — either
        because their token doesn't verify (401) or, when it does, because
        their UID doesn't match the requested user_id (403). Either is an
        acceptable "access denied" outcome; 200 is not."""
        other_user_id = uuid.uuid4().hex[:16]

        response = await client.get(
            f"/api/portfolio/{other_user_id}",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_expired_token_rejection(self, client):
        """Verify invalid/expired tokens are rejected."""
        response = await client.get(
            "/api/portfolio/user-123",
            headers={"Authorization": "Bearer expired.token.here"}
        )
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_missing_auth_header_rejection(self, client):
        """Verify requests without an auth header can't read arbitrary users'
        data: either auth is enforced outright (401), or the dev bypass's
        demo-user identity gets blocked by the self-or-admin check (403)."""
        response = await client.get("/api/portfolio/user-123")
        assert response.status_code in [401, 403]


class TestE2EDataConsistency:
    """Tests for data consistency across operations."""

    @pytest.mark.asyncio
    async def test_portfolio_balance_consistency(self, client, test_user):
        """Verify portfolio balance is consistent across operations."""
        # Get initial balance
        initial = await client.get(
            f"/api/portfolio/{test_user['user_id']}"
        )
        assert initial.status_code == 200
        initial_balance = initial.json()["starting_balance"]

        # Execute and close multiple trades
        pnls = []
        for i in range(3):
            trade_response = await client.post(
                "/api/trades/paper",
                json={
                    "user_id": test_user["user_id"],
                    "signal_id": f"sig-consistency-{i}",
                    "asset": f"ASSET{i}",
                    "direction": "LONG",
                    "quantity": 1.0,
                    "entry_price": 50000.0,
                }
            )
            assert trade_response.status_code == 200
            trade_id = trade_response.json()["trade_id"]

            close_response = await client.post(
                f"/api/trades/paper/{trade_id}/close",
                params={"exit_price": 51000.0}
            )
            assert close_response.status_code == 200
            pnl = close_response.json()["data"]["pnl"]
            pnls.append(pnl)

        # Get final portfolio
        final = await client.get(
            f"/api/portfolio/{test_user['user_id']}"
        )
        assert final.status_code == 200
        final_balance = final.json().get("current_balance", initial_balance)

        # Verify balance = initial + sum(pnls)
        expected_balance = initial_balance + sum(pnls)
        assert final_balance == pytest.approx(expected_balance, rel=0.05)
