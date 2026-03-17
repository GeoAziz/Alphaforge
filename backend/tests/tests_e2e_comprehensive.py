"""
Comprehensive End-to-End Test Suite for AlphaForge Backend
Tests all endpoints and validates complete data flow.
"""

import httpx
import asyncio
import json
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000"
TEST_RESULTS = []


def test_result(test_name, passed, message=""):
    """Record test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    TEST_RESULTS.append((test_name, passed, message))
    print(f"{status} - {test_name}")
    if message:
        print(f"    └─ {message}")


async def run_tests():
    """Run all tests."""
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        print("\n" + "="*70)
        print("🧪 ALPHAFORGE BACKEND - END-TO-END TEST SUITE")
        print("="*70 + "\n")
        
        # ====================================================================
        # HEALTH CHECKS
        # ====================================================================
        print("📌 HEALTH CHECKS")
        print("-" * 70)
        
        try:
            resp = await client.get("/health")
            test_result("Health Check", resp.status_code == 200, f"Status: {resp.status_code}")
        except Exception as e:
            test_result("Health Check", False, str(e))
        
        try:
            resp = await client.get("/status")
            data = resp.json()
            test_result("Status Endpoint", resp.status_code == 200 and data.get("api_running"), 
                       f"Services: {len(data.get('services', {}))}")
        except Exception as e:
            test_result("Status Endpoint", False, str(e))
        
        # ====================================================================
        # USER MANAGEMENT
        # ====================================================================
        print("\n📌 USER MANAGEMENT")
        print("-" * 70)
        
        user_id = None
        try:
            resp = await client.post("/api/users/register", json={
                "email": f"test_{datetime.now().timestamp()}@alphaforge.io",
                "display_name": "Test User",
                "institution_name": "Test Org",
                "plan": "free",
                "risk_tolerance": "moderate"
            })
            data = resp.json()
            user_id = data.get("user", {}).get("id")
            test_result("Register User", resp.status_code in [200, 201] and user_id, f"User ID: {user_id}")
        except Exception as e:
            test_result("Register User", False, str(e))
        
        if user_id:
            try:
                resp = await client.get(f"/api/users/{user_id}")
                data = resp.json()
                test_result("Get User Profile", resp.status_code == 200 and data.get("id") == user_id,
                           f"Email: {data.get('email')}")
            except Exception as e:
                test_result("Get User Profile", False, str(e))
            
            try:
                resp = await client.put(f"/api/users/{user_id}", json={
                    "display_name": "Updated Test User",
                    "risk_tolerance": "aggressive"
                })
                test_result("Update User Profile", resp.status_code in [200, 201],
                           f"Updated display_name")
            except Exception as e:
                test_result("Update User Profile", False, str(e))
        
        # ====================================================================
        # SIGNAL PROCESSING
        # ====================================================================
        print("\n📌 SIGNAL PROCESSING")
        print("-" * 70)
        
        signal_id = None
        try:
            resp = await client.post("/api/signals/process")
            data = resp.json()
            signals_count = data.get("signals_processed", 0)
            test_result("Process Signals", data.get("success") and signals_count >= 0,
                       f"Signals processed: {signals_count}")
            if data.get("signals"):
                signal_id = data["signals"][0].get("id")
        except Exception as e:
            test_result("Process Signals", False, str(e))
        
        try:
            resp = await client.get("/api/signals?limit=10")
            data = resp.json()
            signals_count = len(data) if isinstance(data, list) else 0
            test_result("Get Signals", resp.status_code == 200,
                       f"Signals retrieved: {signals_count}")
        except Exception as e:
            test_result("Get Signals", False, str(e))
        
        if signal_id and user_id:
            try:
                resp = await client.post(f"/api/signals/{signal_id}/validate?user_id={user_id}")
                data = resp.json()
                test_result("Validate Signal", resp.status_code in [200, 201],
                           f"Risk score: {data.get('risk_score')}")
            except Exception as e:
                test_result("Validate Signal", False, str(e))
        
        # ====================================================================
        # PAPER TRADING
        # ====================================================================
        print("\n📌 PAPER TRADING")
        print("-" * 70)
        
        trade_id = None
        if user_id and signal_id:
            try:
                resp = await client.post("/api/trades/paper", json={
                    "user_id": user_id,
                    "signal_id": signal_id,
                    "asset": "BTC",
                    "direction": "LONG",
                    "entry_price": 45000.0,
                    "quantity": 1.0,
                    "stop_loss": 40000.0,
                    "take_profit": 50000.0
                })
                data = resp.json()
                trade_id = data.get("trade_id") or data.get("data", {}).get("trade_id")
                test_result("Create Paper Trade", resp.status_code in [200, 201] and trade_id,
                           f"Trade ID: {trade_id}")
            except Exception as e:
                test_result("Create Paper Trade", False, str(e))
        
        if trade_id:
            try:
                resp = await client.post(f"/api/trades/paper/{trade_id}/close?exit_price=47000.0")
                data = resp.json()
                test_result("Close Paper Trade", resp.status_code in [200, 201],
                           f"Trade closed successfully")
            except Exception as e:
                test_result("Close Paper Trade", False, str(e))
        
        if user_id:
            try:
                resp = await client.get(f"/api/trades/paper?user_id={user_id}")
                data = resp.json()
                trades_count = data.get("count", 0)
                test_result("Get Paper Trades", resp.status_code == 200,
                           f"Trades retrieved: {trades_count}")
            except Exception as e:
                test_result("Get Paper Trades", False, str(e))
        
        # ====================================================================
        # PORTFOLIO MANAGEMENT
        # ====================================================================
        print("\n📌 PORTFOLIO MANAGEMENT")
        print("-" * 70)
        
        if user_id:
            try:
                resp = await client.get(f"/api/portfolio/{user_id}")
                data = resp.json()
                test_result("Get Portfolio Summary", resp.status_code == 200,
                           f"Total PnL: {data.get('total_pnl')}")
            except Exception as e:
                test_result("Get Portfolio Summary", False, str(e))
            
            try:
                resp = await client.get(f"/api/portfolio/{user_id}/metrics")
                data = resp.json()
                test_result("Get Portfolio Metrics", resp.status_code == 200,
                           f"Sharpe: {data.get('sharpe_ratio')}")
            except Exception as e:
                test_result("Get Portfolio Metrics", False, str(e))
            
            try:
                resp = await client.get(f"/api/positions/{user_id}")
                data = resp.json()
                positions_count = data.get("count", 0)
                test_result("Get Open Positions", resp.status_code == 200,
                           f"Positions: {positions_count}")
            except Exception as e:
                test_result("Get Open Positions", False, str(e))
        
        # ====================================================================
        # MARKET DATA
        # ====================================================================
        print("\n📌 MARKET DATA")
        print("-" * 70)
        
        try:
            resp = await client.get("/api/market/tickers?symbols=BTC,ETH")
            data = resp.json()
            tickers_count = len(data.get("tickers", []))
            test_result("Get Market Tickers", resp.status_code == 200,
                       f"Tickers: {tickers_count}")
        except Exception as e:
            test_result("Get Market Tickers", False, str(e))
        
        try:
            resp = await client.get("/api/market/sentiment")
            data = resp.json()
            status = data.get("market_status")
            test_result("Get Market Sentiment", resp.status_code == 200,
                       f"Status: {status}")
        except Exception as e:
            test_result("Get Market Sentiment", False, str(e))
        
        try:
            resp = await client.get("/api/market/data-quality")
            data = resp.json()
            feeds_count = len(data.get("data_quality", []))
            test_result("Get Data Quality", resp.status_code == 200,
                       f"Feeds: {feeds_count}")
        except Exception as e:
            test_result("Get Data Quality", False, str(e))
        
        try:
            resp = await client.get("/api/market/funding-rates")
            data = resp.json()
            rates_count = len(data.get("funding_rates", []))
            test_result("Get Funding Rates", resp.status_code == 200,
                       f"Assets: {rates_count}")
        except Exception as e:
            test_result("Get Funding Rates", False, str(e))
        
        try:
            resp = await client.get("/api/market/open-interest")
            data = resp.json()
            oi_count = len(data.get("open_interest", []))
            test_result("Get Open Interest", resp.status_code == 200,
                       f"Assets: {oi_count}")
        except Exception as e:
            test_result("Get Open Interest", False, str(e))
        
        # ====================================================================
        # WEBHOOKS
        # ====================================================================
        print("\n📌 WEBHOOKS")
        print("-" * 70)
        
        try:
            resp = await client.post("/webhooks/tradingview",
                json={
                    "ticker": "BTC",
                    "action": "BUY",
                    "price": 45000.0
                },
                headers={"x-webhook-secret": "invalid_secret"}
            )
            test_result("Webhook Auth (Invalid Secret)", resp.status_code == 401,
                       "Correctly rejected invalid secret")
        except Exception as e:
            test_result("Webhook Auth (Invalid Secret)", False, str(e))
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, p, _ in TEST_RESULTS if p)
    total = len(TEST_RESULTS)
    
    print(f"\n✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%\n")
    
    # Save results to file
    with open("/tmp/backend_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed/total)*100,
            "results": [
                {"name": name, "passed": p, "message": msg}
                for name, p, msg in TEST_RESULTS
            ]
        }, f, indent=2)
    
    print("Results saved to /tmp/backend_test_results.json\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)
