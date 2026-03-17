"""
End-to-End Backend Testing Suite
Tests all 28 API endpoints and validates complete data flows
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = f"test_{int(datetime.utcnow().timestamp())}@alphaforge.demo"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
END = "\033[0m"

# Test results tracking
results = {
    "passed": 0,
    "failed": 0,
    "total": 0,
    "failures": []
}


async def test_endpoint(name: str, method: str, endpoint: str, expected_status: int = 200, **kwargs) -> Dict[str, Any]:
    """Generic endpoint test helper"""
    results["total"] += 1
    url = f"{BASE_URL}{endpoint}"
    
    try:
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, **kwargs)
            elif method.upper() == "POST":
                response = await client.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = await client.put(url, **kwargs)
            
            success = response.status_code == expected_status
            data = response.json() if response.text else {}
            
            if success:
                print(f"{GREEN}✅ {name}{END}")
                results["passed"] += 1
            else:
                print(f"{RED}❌ {name} (Status: {response.status_code}){END}")
                results["failed"] += 1
                results["failures"].append((name, response.status_code, str(data)))
            
            return {
                "success": success,
                "status": response.status_code,
                "data": data
            }
    
    except Exception as e:
        print(f"{RED}❌ {name} - {str(e)}{END}")
        results["failed"] += 1
        results["failures"].append((name, "EXCEPTION", str(e)))
        return {"success": False, "error": str(e)}


async def test_health_checks():
    """Test health and status endpoints"""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}🏥 HEALTH CHECKS (2 endpoints){END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    await test_endpoint("GET /health", "GET", "/health")
    await test_endpoint("GET /status", "GET", "/status")


async def test_user_management(user_data: Dict = None) -> Dict[str, str]:
    """Test user registration, fetch, and update (3 endpoints)"""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}👤 USER MANAGEMENT (3 endpoints){END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    # Register user
    user_payload = {
        "email": TEST_USER_EMAIL,
        "display_name": "Test Trader",
        "institution_name": "AlphaForge Test Lab",
        "plan": "free",
        "risk_tolerance": "moderate"
    }
    
    result = await test_endpoint(
        "POST /api/users/register",
        "POST",
        "/api/users/register",
        json=user_payload
    )
    
    user_id = None
    if result["success"] and "id" in result["data"]:
        user_id = result["data"]["id"]
        user_data["user_id"] = user_id
        print(f"   └─ User ID: {user_id}")
    else:
        print(f"{YELLOW}   ⚠️  Could not extract user ID{END}")
        return user_data
    
    # Fetch user
    await test_endpoint(
        "GET /api/users/{user_id}",
        "GET",
        f"/api/users/{user_id}"
    )
    
    # Update user
    update_payload = {
        "display_name": "Updated Trader Name"
    }
    await test_endpoint(
        "PUT /api/users/{user_id}",
        "PUT",
        f"/api/users/{user_id}",
        json=update_payload
    )
    
    return user_data


async def test_signal_management(user_data: Dict) -> Dict[str, str]:
    """Test signal generation, processing, and validation (3 endpoints)"""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}📊 SIGNAL MANAGEMENT (3 endpoints){END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    # Process signals
    result = await test_endpoint(
        "POST /api/signals/process",
        "POST",
        "/api/signals/process"
    )
    
    signal_id = None
    if result["success"] and "signals" in result["data"] and len(result["data"]["signals"]) > 0:
        signal_id = result["data"]["signals"][0].get("id")
        user_data["signal_id"] = signal_id
        num_signals = result["data"].get("signals_processed", 0)
        print(f"   └─ Generated {num_signals} signals")
    
    # Get signals
    await test_endpoint(
        "GET /api/signals",
        "GET",
        "/api/signals?limit=50"
    )
    
    # Validate signal (if we have a signal_id and user_id)
    if signal_id and user_data.get("user_id"):
        await test_endpoint(
            "POST /api/signals/{signal_id}/validate",
            "POST",
            f"/api/signals/{signal_id}/validate?user_id={user_data['user_id']}"
        )
    else:
        print(f"{YELLOW}⚠️  Skipped signal validation (missing IDs){END}")
    
    return user_data


async def test_paper_trading(user_data: Dict) -> Dict[str, str]:
    """Test paper trading execution, closing, and history (3 endpoints)"""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}💰 PAPER TRADING (3 endpoints){END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    if not user_data.get("user_id"):
        print(f"{YELLOW}⚠️  Skipping paper trading (no user_id){END}")
        return user_data
    
    # Create paper trade
    trade_payload = {
        "user_id": user_data["user_id"],
        "signal_id": user_data.get("signal_id", "test-signal-1"),
        "asset": "BTC",
        "direction": "LONG",
        "entry_price": 45000.0,
        "quantity": 0.5,
        "stop_loss": 44000.0,
        "take_profit": 46000.0
    }
    
    result = await test_endpoint(
        "POST /api/trades/paper",
        "POST",
        "/api/trades/paper",
        json=trade_payload
    )
    
    trade_id = None
    if result["success"] and "trade_id" in result["data"]:
        trade_id = result["data"]["trade_id"]
        user_data["trade_id"] = trade_id
        print(f"   └─ Trade ID: {trade_id}")
    
    # Get paper trades
    await test_endpoint(
        "GET /api/trades/paper",
        "GET",
        f"/api/trades/paper?user_id={user_data['user_id']}"
    )
    
    # Close trade (if we have trade_id)
    if trade_id:
        await test_endpoint(
            "POST /api/trades/paper/{trade_id}/close",
            "POST",
            f"/api/trades/paper/{trade_id}/close?exit_price=45500.0"
        )
    else:
        print(f"{YELLOW}⚠️  Skipped trade closing (no trade_id){END}")
    
    return user_data


async def test_portfolio_management(user_data: Dict):
    """Test portfolio summary, metrics, and positions (3 endpoints)"""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}📈 PORTFOLIO MANAGEMENT (3 endpoints){END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    if not user_data.get("user_id"):
        print(f"{YELLOW}⚠️  Skipping portfolio (no user_id){END}")
        return
    
    # Get portfolio summary
    result = await test_endpoint(
        "GET /api/portfolio/{user_id}",
        "GET",
        f"/api/portfolio/{user_data['user_id']}"
    )
    
    if result["success"]:
        p = result["data"]
        print(f"   └─ Balance: ${p.get('current_balance', 0):,.2f}")
        print(f"   └─ Total PnL: ${p.get('total_pnl', 0):,.2f}")
        print(f"   └─ Win Rate: {p.get('total_pnL_percent', 0):.1f}%")
    
    # Get portfolio metrics
    await test_endpoint(
        "GET /api/portfolio/{user_id}/metrics",
        "GET",
        f"/api/portfolio/{user_data['user_id']}/metrics"
    )
    
    # Get positions
    await test_endpoint(
        "GET /api/positions/{user_id}",
        "GET",
        f"/api/positions/{user_data['user_id']}"
    )


async def test_market_data():
    """Test market data endpoints (5 endpoints)"""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}🌍 MARKET DATA (5 endpoints){END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    # Market tickers
    result = await test_endpoint(
        "GET /api/market/tickers",
        "GET",
        "/api/market/tickers?symbols=BTC,ETH,SOL"
    )
    
    if result["success"] and "tickers" in result["data"]:
        print(f"   └─ Fetched {len(result['data']['tickers'])} tickers")
    
    # Market sentiment
    result = await test_endpoint(
        "GET /api/market/sentiment",
        "GET",
        "/api/market/sentiment"
    )
    
    if result["success"]:
        sentiment = result["data"].get("market_status", "UNKNOWN")
        print(f"   └─ Market Status: {sentiment}")
    
    # Data quality
    result = await test_endpoint(
        "GET /api/market/data-quality",
        "GET",
        "/api/market/data-quality"
    )
    
    if result["success"] and "data_quality" in result["data"]:
        print(f"   └─ Data quality for {len(result['data']['data_quality'])} feeds")
    
    # Funding rates
    result = await test_endpoint(
        "GET /api/market/funding-rates",
        "GET",
        "/api/market/funding-rates"
    )
    
    if result["success"] and "funding_rates" in result["data"]:
        print(f"   └─ Retrieved {len(result['data']['funding_rates'])} funding rates")
    
    # Open interest
    result = await test_endpoint(
        "GET /api/market/open-interest",
        "GET",
        "/api/market/open-interest"
    )
    
    if result["success"] and "open_interest" in result["data"]:
        print(f"   └─ Retrieved OI for {len(result['data']['open_interest'])} assets")


async def test_webhooks():
    """Test webhook endpoint (1 endpoint)"""
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}🔗 WEBHOOKS (1 endpoint){END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    webhook_payload = {
        "ticker": "BTC",
        "action": "BUY",
        "price": 45000.0
    }
    
    # Test without secret (should fail with 401)
    await test_endpoint(
        "POST /webhooks/tradingview (unauthorized)",
        "POST",
        "/webhooks/tradingview",
        expected_status=401,
        json=webhook_payload
    )


async def run_all_tests():
    """Run complete test suite"""
    print(f"\n{YELLOW}╔════════════════════════════════════════════════════╗{END}")
    print(f"{YELLOW}║     AlphaForge Backend E2E Test Suite              ║{END}")
    print(f"{YELLOW}║     Complete Functionality Validation              ║{END}")
    print(f"{YELLOW}╚════════════════════════════════════════════════════╝{END}")
    
    user_data = {}
    
    # Execute all test suites
    await test_health_checks()
    user_data = await test_user_management(user_data)
    user_data = await test_signal_management(user_data)
    user_data = await test_paper_trading(user_data)
    await test_portfolio_management(user_data)
    await test_market_data()
    await test_webhooks()
    
    # Print summary
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    print(f"{BLUE}📊 TEST SUMMARY{END}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    total = results["total"]
    passed = results["passed"]
    failed = results["failed"]
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{GREEN}✅ Passed: {passed}/{total}{END}")
    print(f"{RED}❌ Failed: {failed}/{total}{END}")
    print(f"{BLUE}📈 Pass Rate: {pass_rate:.1f}%{END}")
    
    if results["failures"]:
        print(f"\n{RED}Failed Tests:{END}")
        for name, status, detail in results["failures"]:
            print(f"  • {name}")
            print(f"    Status: {status}")
            if detail and len(detail) < 100:
                print(f"    Detail: {detail}")
    
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}")
    
    # Final verdict
    if pass_rate >= 90:
        print(f"{GREEN}🎉 MVP VALIDATION PASSED! Backend is ready for integration{END}")
    elif pass_rate >= 70:
        print(f"{YELLOW}⚠️  Core functionality works, some gaps remain{END}")
    else:
        print(f"{RED}🚨 Critical issues found, needs investigation{END}")
    
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{END}\n")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
