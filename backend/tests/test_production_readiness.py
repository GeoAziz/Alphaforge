import os
import uuid

import httpx
import pytest


BASE_URL = os.getenv("ALPHAFORGE_API_BASE_URL", "http://localhost:8000")
TIMEOUT = float(os.getenv("ALPHAFORGE_E2E_TIMEOUT", "45"))


@pytest.mark.asyncio
async def test_readiness_requires_real_database():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        response = await client.get("/ready")
        assert response.status_code == 200, response.text
        payload = response.json()

        assert payload.get("status") in {"ready", "degraded"}
        assert payload.get("database") == "ready"

        require_real_db = os.getenv("REQUIRE_REAL_DB", "false").lower() == "true"
        if require_real_db:
            assert payload.get("database_mode") == "supabase", payload
            assert payload.get("required_tables_ok") is True, payload


@pytest.mark.asyncio
async def test_critical_user_signal_trade_flow():
    run_id = uuid.uuid4().hex[:10]
    email = f"prod-readiness-{run_id}@alphaforge.qa"

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        register = await client.post(
            "/api/users/register",
            json={
                "email": email,
                "display_name": "Prod Readiness User",
                "institution_name": "AlphaForge QA",
                "plan": "free",
                "risk_tolerance": "moderate",
            },
        )
        assert register.status_code == 200, register.text
        user_id = register.json().get("user", {}).get("id")
        assert user_id, register.text

        process = await client.post("/api/signals/process")
        assert process.status_code == 200, process.text

        signals = await client.get("/api/signals?limit=1")
        assert signals.status_code == 200, signals.text
        signals_payload = signals.json()
        assert isinstance(signals_payload, list)
        assert len(signals_payload) > 0, signals.text
        signal_id = signals_payload[0].get("id")
        assert signal_id

        trade = await client.post(
            "/api/trades/paper",
            json={
                "user_id": user_id,
                "signal_id": signal_id,
                "asset": "BTC",
                "direction": "LONG",
                "entry_price": 45000.0,
                "quantity": 0.1,
                "stop_loss": 44000.0,
                "take_profit": 47000.0,
            },
        )
        assert trade.status_code == 200, trade.text
        trade_id = trade.json().get("trade_id")
        assert trade_id, trade.text

        close = await client.post(f"/api/trades/paper/{trade_id}/close?exit_price=45500.0")
        assert close.status_code == 200, close.text

        portfolio = await client.get(f"/api/portfolio/{user_id}")
        assert portfolio.status_code == 200, portfolio.text
        portfolio_payload = portfolio.json()
        assert "current_balance" in portfolio_payload
        assert "total_pnl" in portfolio_payload
