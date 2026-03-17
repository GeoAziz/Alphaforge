import asyncio
import os
import uuid
from typing import Any, Dict, Iterable, Optional, Sequence

import httpx
from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.getenv("ALPHAFORGE_API_BASE_URL", "http://localhost:8000")
TIMEOUT = float(os.getenv("ALPHAFORGE_E2E_TIMEOUT", "60"))


def _assert_has_keys(payload: Dict[str, Any], keys: Iterable[str], label: str) -> None:
    missing = [key for key in keys if key not in payload]
    assert not missing, f"{label} missing keys: {missing}"


async def _request(
    client: httpx.AsyncClient,
    method: str,
    path: str,
    *,
    label: str,
    expected: Sequence[int] = (200,),
    **kwargs: Any,
) -> Any:
    response = await client.request(method, path, **kwargs)
    assert response.status_code in expected, (
        f"{label} failed: {method} {path} -> {response.status_code}, body={response.text[:500]}"
    )
    return response.json() if response.text else {}


async def _run_fullsuite() -> None:
    run_suffix = uuid.uuid4().hex[:10]
    user_email = f"e2e_{run_suffix}@alphaforge-qa.com"

    state: Dict[str, Optional[str]] = {
        "user_id": None,
        "signal_id": None,
        "trade_id": None,
        "strategy_id": None,
        "backtest_id": None,
    }

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        health = await _request(client, "GET", "/health", label="health")
        _assert_has_keys(health, ["status", "timestamp", "version"], "health")

        status = await _request(client, "GET", "/status", label="status")
        _assert_has_keys(status, ["api_running", "database", "services", "timestamp"], "status")

        register = await _request(
            client,
            "POST",
            "/api/users/register",
            label="register_user",
            json={
                "email": user_email,
                "display_name": "E2E Test User",
                "institution_name": "AlphaForge QA",
                "plan": "free",
                "risk_tolerance": "moderate",
            },
        )
        _assert_has_keys(register, ["success", "user"], "register_user")
        state["user_id"] = register["user"].get("id")
        assert state["user_id"], "No user id returned from register_user"
        user_id = state["user_id"]

        user = await _request(client, "GET", f"/api/users/{user_id}", label="get_user")
        _assert_has_keys(user, ["id", "email", "display_name", "plan", "risk_tolerance"], "get_user")

        updated_user = await _request(
            client,
            "PUT",
            f"/api/users/{user_id}",
            label="update_user",
            json={"display_name": "E2E Updated User", "risk_tolerance": "aggressive"},
        )
        assert updated_user.get("display_name") == "E2E Updated User"

        tickers = await _request(
            client,
            "GET",
            "/api/market/tickers?symbols=BTC,ETH,SOL",
            label="market_tickers",
        )
        _assert_has_keys(tickers, ["success", "tickers", "timestamp"], "market_tickers")

        sentiment = await _request(client, "GET", "/api/market/sentiment", label="market_sentiment")
        _assert_has_keys(sentiment, ["bullish_count", "neutral_count", "bearish_count", "market_status"], "market_sentiment")

        data_quality = await _request(client, "GET", "/api/market/data-quality", label="market_data_quality")
        _assert_has_keys(data_quality, ["success", "data_quality", "timestamp"], "market_data_quality")

        funding = await _request(client, "GET", "/api/market/funding-rates", label="funding_rates")
        _assert_has_keys(funding, ["success", "funding_rates", "timestamp"], "funding_rates")

        open_interest = await _request(client, "GET", "/api/market/open-interest", label="open_interest")
        _assert_has_keys(open_interest, ["success", "open_interest", "timestamp"], "open_interest")

        processed = await _request(client, "POST", "/api/signals/process", label="process_signals")
        _assert_has_keys(processed, ["success", "signals_processed", "signals"], "process_signals")

        signals = await _request(client, "GET", "/api/signals?limit=25", label="get_signals")
        assert isinstance(signals, list), "get_signals must return list"

        signal_candidates = processed.get("signals") or signals
        if signal_candidates and isinstance(signal_candidates[0], dict):
            state["signal_id"] = signal_candidates[0].get("id")

        signal_id = state["signal_id"]
        assert signal_id, "No signal_id available for signal-dependent flows"

        validation = await _request(
            client,
            "POST",
            f"/api/signals/{signal_id}/validate?user_id={user_id}",
            label="validate_signal",
        )
        _assert_has_keys(validation, ["approved", "risk_score", "warnings"], "validate_signal")

        paper_trade = await _request(
            client,
            "POST",
            "/api/trades/paper",
            label="create_paper_trade",
            json={
                "user_id": user_id,
                "signal_id": signal_id,
                "asset": "BTC",
                "direction": "LONG",
                "entry_price": 45000.0,
                "quantity": 0.25,
                "stop_loss": 44000.0,
                "take_profit": 47000.0,
            },
        )
        _assert_has_keys(paper_trade, ["success", "trade_id", "data"], "create_paper_trade")
        state["trade_id"] = paper_trade.get("trade_id")

        paper_trades = await _request(
            client,
            "GET",
            f"/api/trades/paper?user_id={user_id}",
            label="get_paper_trades",
        )
        _assert_has_keys(paper_trades, ["trades", "count"], "get_paper_trades")

        trade_id = state["trade_id"]
        assert trade_id, "No trade id available to close"

        closed_trade = await _request(
            client,
            "POST",
            f"/api/trades/paper/{trade_id}/close?exit_price=45500.0",
            label="close_paper_trade",
        )
        _assert_has_keys(closed_trade, ["success", "data"], "close_paper_trade")

        portfolio = await _request(client, "GET", f"/api/portfolio/{user_id}", label="portfolio_summary")
        _assert_has_keys(portfolio, ["user_id", "starting_balance", "current_balance", "total_pnl"], "portfolio_summary")

        metrics = await _request(
            client,
            "GET",
            f"/api/portfolio/{user_id}/metrics",
            label="portfolio_metrics",
        )
        _assert_has_keys(metrics, ["total_equity", "pnl_percent", "total_trades", "win_rate"], "portfolio_metrics")

        positions = await _request(client, "GET", f"/api/positions/{user_id}", label="positions")
        _assert_has_keys(positions, ["positions", "count"], "positions")

        chat = await _request(
            client,
            "POST",
            "/api/chat/message",
            label="chat_message",
            params={"user_id": user_id, "message": "Summarize my current risk."},
        )
        _assert_has_keys(chat, ["success", "user_message", "ai_response", "timestamp"], "chat_message")

        chat_history = await _request(
            client,
            "GET",
            "/api/chat/history",
            label="chat_history",
            params={"user_id": user_id, "limit": 20},
        )
        _assert_has_keys(chat_history, ["success", "messages", "count"], "chat_history")

        creator_verification = await _request(
            client,
            "GET",
            f"/api/creator/verification?user_id={user_id}",
            label="creator_verification",
        )
        _assert_has_keys(creator_verification, ["success", "current_stage", "pipeline"], "creator_verification")

        strategy_submit = await _request(
            client,
            "POST",
            f"/api/creator/strategy-submit?user_id={user_id}",
            label="creator_strategy_submit",
        )
        _assert_has_keys(strategy_submit, ["success", "strategy_id"], "creator_strategy_submit")
        state["strategy_id"] = strategy_submit.get("strategy_id")

        await _request(
            client,
            "GET",
            f"/api/creator/reputation/{user_id}",
            label="creator_reputation",
            expected=(200, 404),
        )

        kyc_status = await _request(client, "GET", f"/api/user/kyc?user_id={user_id}", label="kyc_status")
        _assert_has_keys(kyc_status, ["success"], "kyc_status")

        kyc_submit = await _request(client, "POST", f"/api/user/kyc?user_id={user_id}", label="kyc_submit")
        _assert_has_keys(kyc_submit, ["success"], "kyc_submit")

        audit_log = await _request(client, "POST", f"/api/audit/log?user_id={user_id}", label="audit_log_create")
        _assert_has_keys(audit_log, ["success"], "audit_log_create")

        audit_trail = await _request(
            client,
            "GET",
            f"/api/audit/trail/{user_id}?limit=50",
            label="audit_trail",
        )
        _assert_has_keys(audit_trail, ["success", "audit_logs", "count"], "audit_trail")

        risk_get = await _request(client, "GET", f"/api/settings/risk?user_id={user_id}", label="risk_settings_get")
        _assert_has_keys(risk_get, ["success", "settings"], "risk_settings_get")

        risk_update = await _request(client, "PUT", f"/api/settings/risk?user_id={user_id}", label="risk_settings_update")
        _assert_has_keys(risk_update, ["success", "message"], "risk_settings_update")

        exchange_connect = await _request(
            client,
            "POST",
            f"/api/exchange/connect?user_id={user_id}&exchange=binance",
            label="exchange_connect",
        )
        _assert_has_keys(exchange_connect, ["success"], "exchange_connect")

        exchange_keys = await _request(client, "GET", f"/api/exchange/keys?user_id={user_id}", label="exchange_keys")
        _assert_has_keys(exchange_keys, ["success", "exchanges", "count"], "exchange_keys")

        exchange_disconnect = await _request(
            client,
            "POST",
            f"/api/exchange/disconnect?user_id={user_id}&exchange=binance",
            label="exchange_disconnect",
        )
        _assert_has_keys(exchange_disconnect, ["success", "message"], "exchange_disconnect")

        ext_signals = await _request(
            client,
            "GET",
            f"/api/external-signals?user_id={user_id}&limit=50",
            label="external_signals_get",
        )
        _assert_has_keys(ext_signals, ["success", "signals", "count"], "external_signals_get")

        ext_rules = await _request(
            client,
            "POST",
            f"/api/external-signals/rules?user_id={user_id}",
            label="external_rules_set",
        )
        _assert_has_keys(ext_rules, ["success", "message"], "external_rules_set")

        ext_history = await _request(
            client,
            "GET",
            f"/api/external-signals/history?user_id={user_id}&days=7",
            label="external_history",
        )
        _assert_has_keys(ext_history, ["success", "webhook_hits", "count"], "external_history")

        user_strategies = await _request(client, "GET", f"/api/strategies?user_id={user_id}", label="user_strategies")
        _assert_has_keys(user_strategies, ["success", "strategies", "count"], "user_strategies")

        marketplace = await _request(
            client,
            "GET",
            "/api/strategies/marketplace?limit=50&offset=0",
            label="marketplace_strategies",
        )
        _assert_has_keys(marketplace, ["success", "strategies", "count"], "marketplace_strategies")

        strategy_id = state["strategy_id"]
        assert strategy_id, "No strategy_id created for strategy endpoints"

        strategy_perf = await _request(
            client,
            "GET",
            f"/api/strategies/{strategy_id}/performance",
            label="strategy_performance",
        )
        _assert_has_keys(strategy_perf, ["success", "strategy_id", "metrics"], "strategy_performance")

        strategy_subscribe = await _request(
            client,
            "POST",
            f"/api/strategy/subscribe?user_id={user_id}&strategy_id={strategy_id}",
            label="strategy_subscribe",
        )
        _assert_has_keys(strategy_subscribe, ["success"], "strategy_subscribe")

        subscriptions = await _request(
            client,
            "GET",
            f"/api/strategy/subscriptions?user_id={user_id}",
            label="strategy_subscriptions",
        )
        _assert_has_keys(subscriptions, ["success", "subscriptions", "count"], "strategy_subscriptions")

        strategy_paper = await _request(
            client,
            "POST",
            f"/api/strategy/{strategy_id}/paper-trade?user_id={user_id}",
            label="strategy_paper_trade",
        )
        _assert_has_keys(strategy_paper, ["success"], "strategy_paper_trade")

        backtest_run = await _request(
            client,
            "POST",
            f"/api/backtest/run?user_id={user_id}",
            label="backtest_run",
        )
        _assert_has_keys(backtest_run, ["success", "backtest_id", "status", "results"], "backtest_run")
        state["backtest_id"] = backtest_run.get("backtest_id")

        backtest_id = state["backtest_id"]
        assert backtest_id, "No backtest_id returned from backtest_run"

        backtest_result = await _request(client, "GET", f"/api/backtest/{backtest_id}", label="backtest_result")
        _assert_has_keys(backtest_result, ["success", "backtest"], "backtest_result")

        equity_curve = await _request(
            client,
            "GET",
            f"/api/backtest/{backtest_id}/equity-curve",
            label="backtest_equity_curve",
        )
        _assert_has_keys(equity_curve, ["success", "backtest_id", "equity_curve"], "backtest_equity_curve")

        user_backtests = await _request(
            client,
            "GET",
            f"/api/backtest/user/{user_id}?limit=20",
            label="user_backtests",
        )
        _assert_has_keys(user_backtests, ["success", "backtests", "count"], "user_backtests")

        execute_signal = await _request(
            client,
            "POST",
            f"/api/signals/{signal_id}/execute?user_id={user_id}",
            label="execute_signal",
        )
        _assert_has_keys(execute_signal, ["success"], "execute_signal")

        signal_proofs = await _request(client, "GET", f"/api/signals/{signal_id}/proofs", label="signal_proofs")
        _assert_has_keys(signal_proofs, ["success", "proof"], "signal_proofs")

        proof_detail = await _request(client, "GET", f"/api/proofs/{signal_id}", label="proof_detail")
        _assert_has_keys(proof_detail, ["success", "proof"], "proof_detail")

        market_insights = await _request(
            client,
            "POST",
            "/api/market/insights?query=What is BTC risk regime now?",
            label="market_insights",
        )
        _assert_has_keys(market_insights, ["success", "insight"], "market_insights")

        webhook_secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "")
        webhook_payload = {"ticker": "BTC", "action": "BUY", "price": 45000.0}

        if webhook_secret.strip():
            unauthorized = await client.post("/webhooks/tradingview", json=webhook_payload)
            assert unauthorized.status_code == 401, (
                f"webhook unauth expected 401, got {unauthorized.status_code}, body={unauthorized.text[:500]}"
            )

            webhook_auth = await _request(
                client,
                "POST",
                "/webhooks/tradingview",
                label="webhook_authorized",
                json=webhook_payload,
                headers={"x-webhook-secret": webhook_secret},
            )
            _assert_has_keys(webhook_auth, ["success", "signal_id"], "webhook_authorized")
        else:
            webhook_no_secret = await _request(
                client,
                "POST",
                "/webhooks/tradingview",
                label="webhook_no_secret",
                json=webhook_payload,
            )
            _assert_has_keys(webhook_no_secret, ["success", "signal_id"], "webhook_no_secret")


def test_backend_fullsuite_e2e() -> None:
    asyncio.run(_run_fullsuite())
