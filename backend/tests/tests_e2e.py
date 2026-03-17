"""
End-to-End Backend Testing Suite
Validates all services and API endpoints
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test_user_001"
TEST_EMAIL = "test@alphaforge.io"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class BackendTestSuite:
    """Comprehensive backend testing suite."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = []
        self.signal_id = None
        self.trade_id = None
        self.user_id = None
    
    async def run_all_tests(self):
        """Execute all tests in sequence."""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}🧪 AlphaForge Backend E2E Test Suite{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        # Phase 1: Health Checks
        await self.test_health_check()
        
        # Phase 2: User Management
        await self.test_user_registration()
        await self.test_get_user()
        await self.test_update_user()
        
        # Phase 3: Market Data
        await self.test_market_tickers()
        await self.test_market_sentiment()
        await self.test_funding_rates()
        await self.test_open_interest()
        await self.test_data_quality()
        
        # Phase 4: Signal Processing
        await self.test_process_signals()
        await self.test_get_signals()
        
        # Phase 5: Paper Trading
        if self.signal_id:
            await self.test_validate_signal()
            await self.test_create_paper_trade()
            await self.test_get_paper_trades()
            if self.trade_id:
                await self.test_close_paper_trade()
        
        # Phase 6: Portfolio Tracking
        await self.test_get_portfolio()
        await self.test_get_portfolio_metrics()
        await self.test_get_positions()
        
        # Print Summary
        await self.print_summary()
    
    # ========================================================================
    # HEALTH & STATUS TESTS
    # ========================================================================
    
    async def test_health_check(self):
        """Test health endpoint."""
        await self._test_endpoint(
            "GET", "/health",
            expected_status=200,
            description="Health Check"
        )
    
    async def test_status(self):
        """Test status endpoint."""
        response = await self._test_endpoint(
            "GET", "/status",
            expected_status=200,
            description="Service Status"
        )
        if response:
            data = response.json()
            print(f"   Status: {json.dumps(data.get('services', {}), indent=2)}")
    
    # ========================================================================
    # USER MANAGEMENT TESTS
    # ========================================================================
    
    async def test_user_registration(self):
        """Test user registration."""
        payload = {
            "email": TEST_EMAIL,
            "display_name": "Test User",
            "institution_name": "Test Institution",
            "plan": "free",
            "risk_tolerance": "moderate"
        }
        
        response = await self._test_endpoint(
            "POST", "/api/users/register",
            json=payload,
            expected_status=200,
            description="User Registration"
        )
        
        if response:
            data = response.json()
            user_data = data.get("user", {})
            self.user_id = user_data.get("id", TEST_USER_ID)
            print(f"   User ID: {self.user_id}")
            print(f"   Email: {user_data.get('email')}")
    
    async def test_get_user(self):
        """Test get user endpoint."""
        if not self.user_id:
            self.user_id = TEST_USER_ID
        
        response = await self._test_endpoint(
            "GET", f"/api/users/{self.user_id}",
            expected_status=200,
            description="Get User Profile"
        )
        
        if response:
            data = response.json()
            print(f"   Display Name: {data.get('display_name')}")
            print(f"   Plan: {data.get('plan')}")
            print(f"   Risk Tolerance: {data.get('risk_tolerance')}")
    
    async def test_update_user(self):
        """Test update user endpoint."""
        if not self.user_id:
            self.user_id = TEST_USER_ID
        
        payload = {
            "display_name": "Updated Test User",
            "risk_tolerance": "aggressive"
        }
        
        response = await self._test_endpoint(
            "PUT", f"/api/users/{self.user_id}",
            json=payload,
            expected_status=200,
            description="Update User Profile"
        )
        
        if response:
            data = response.json()
            print(f"   Updated Display Name: {data.get('display_name')}")
            print(f"   Updated Risk Tolerance: {data.get('risk_tolerance')}")
    
    # ========================================================================
    # MARKET DATA TESTS
    # ========================================================================
    
    async def test_market_tickers(self):
        """Test market tickers endpoint."""
        response = await self._test_endpoint(
            "GET", "/api/market/tickers?symbols=BTC,ETH,BNB",
            expected_status=200,
            description="Get Market Tickers"
        )
        
        if response:
            data = response.json()
            tickers = data.get('tickers', [])
            print(f"   Fetched {len(tickers)} tickers")
            for ticker in tickers[:2]:
                print(f"   - {ticker.get('symbol')}: ${ticker.get('last_price', 'N/A'):.2f}")
    
    async def test_market_sentiment(self):
        """Test market sentiment endpoint."""
        response = await self._test_endpoint(
            "GET", "/api/market/sentiment",
            expected_status=200,
            description="Get Market Sentiment"
        )
        
        if response:
            data = response.json()
            print(f"   Status: {data.get('market_status')}")
            print(f"   Composite Score: {data.get('composite_score')}")
            print(f"   Bullish: {data.get('bullish_pct')*100:.1f}%")
            print(f"   Neutral: {data.get('neutral_pct')*100:.1f}%")
            print(f"   Bearish: {data.get('bearish_pct')*100:.1f}%")
    
    async def test_funding_rates(self):
        """Test funding rates endpoint."""
        response = await self._test_endpoint(
            "GET", "/api/market/funding-rates",
            expected_status=200,
            description="Get Funding Rates"
        )
        
        if response:
            data = response.json()
            funding_rates = data.get('funding_rates', [])
            print(f"   Fetched {len(funding_rates)} assets")
            for rate in funding_rates[:2]:
                print(f"   - {rate.get('asset')}: {rate.get('funding_rate', 0)*100:.4f}%")
    
    async def test_open_interest(self):
        """Test open interest endpoint."""
        response = await self._test_endpoint(
            "GET", "/api/market/open-interest",
            expected_status=200,
            description="Get Open Interest"
        )
        
        if response:
            data = response.json()
            oi = data.get('open_interest', [])
            print(f"   Fetched {len(oi)} assets")
            for item in oi[:2]:
                print(f"   - {item.get('asset')}: ${item.get('open_interest_usd', 0)/1e9:.2f}B")
    
    async def test_data_quality(self):
        """Test data quality endpoint."""
        response = await self._test_endpoint(
            "GET", "/api/market/data-quality",
            expected_status=200,
            description="Get Data Quality"
        )
        
        if response:
            data = response.json()
            quality = data.get('data_quality', [])
            print(f"   Fetched {len(quality)} feeds")
            for item in quality:
                status = "✅" if item.get('status') == 'HEALTHY' else "⚠️"
                print(f"   {status} {item.get('asset')}: {item.get('uptime_pct', 0):.1f}% uptime")
    
    # ========================================================================
    # SIGNAL PROCESSING TESTS
    # ========================================================================
    
    async def test_process_signals(self):
        """Test signal processing endpoint."""
        response = await self._test_endpoint(
            "POST", "/api/signals/process",
            expected_status=200,
            description="Process Signals"
        )
        
        if response:
            data = response.json()
            processed = data.get('signals_processed', 0)
            print(f"   Processed {processed} signals")
            signals = data.get('signals', [])
            if signals:
                self.signal_id = signals[0].get('id')
                print(f"   Sample Signal ID: {self.signal_id}")
                print(f"   Sample Signal: {signals[0].get('asset')} {signals[0].get('signal_type')}")
    
    async def test_get_signals(self):
        """Test get signals endpoint."""
        response = await self._test_endpoint(
            "GET", "/api/signals?limit=10",
            expected_status=200,
            description="Get Top Signals"
        )
        
        if response:
            signals = response.json()
            print(f"   Fetched {len(signals)} signals")
            if signals:
                for signal in signals[:3]:
                    print(f"   - {signal.get('asset', 'N/A')}: {signal.get('signal_type')} (confidence: {signal.get('confidence', 'N/A')})")
    
    async def test_validate_signal(self):
        """Test signal validation endpoint."""
        if not self.signal_id or not self.user_id:
            print(f"   {YELLOW}⊘ Skipped (no signal or user){RESET}")
            return
        
        response = await self._test_endpoint(
            "POST", f"/api/signals/{self.signal_id}/validate?user_id={self.user_id}",
            expected_status=200,
            description="Validate Signal"
        )
        
        if response:
            data = response.json()
            print(f"   Risk Score: {data.get('risk_score', 'N/A')}")
            print(f"   Approved: {'✅ Yes' if data.get('approved') else '❌ No'}")
    
    # ========================================================================
    # PAPER TRADING TESTS
    # ========================================================================
    
    async def test_create_paper_trade(self):
        """Test paper trade creation."""
        if not self.user_id or not self.signal_id:
            print(f"   {YELLOW}⊘ Skipped (missing user or signal){RESET}")
            return
        
        payload = {
            "user_id": self.user_id,
            "signal_id": self.signal_id,
            "asset": "BTC",
            "direction": "LONG",
            "entry_price": 45000.00,
            "quantity": 1.0,
            "stop_loss": 42000.00,
            "take_profit": 50000.00
        }
        
        response = await self._test_endpoint(
            "POST", "/api/trades/paper",
            json=payload,
            expected_status=200,
            description="Create Paper Trade"
        )
        
        if response:
            data = response.json()
            self.trade_id = data.get('trade_id')
            print(f"   Trade ID: {self.trade_id}")
            print(f"   Asset: {data.get('data', {}).get('asset')}")
            print(f"   Direction: {data.get('data', {}).get('direction')}")
            print(f"   Entry Price: ${data.get('data', {}).get('entry_price', 'N/A')}")
    
    async def test_get_paper_trades(self):
        """Test get paper trades endpoint."""
        if not self.user_id:
            print(f"   {YELLOW}⊘ Skipped (no user){RESET}")
            return
        
        response = await self._test_endpoint(
            "GET", f"/api/trades/paper?user_id={self.user_id}",
            expected_status=200,
            description="Get Paper Trades"
        )
        
        if response:
            data = response.json()
            trades = data.get('trades', [])
            print(f"   Total trades: {len(trades)}")
            if trades:
                for trade in trades[:2]:
                    status = trade.get('status', 'UNKNOWN')
                    print(f"   - {trade.get('asset', 'N/A')}: {status} @ ${trade.get('entry_price', 'N/A')}")
    
    async def test_close_paper_trade(self):
        """Test close paper trade endpoint."""
        if not self.trade_id:
            print(f"   {YELLOW}⊘ Skipped (no trade){RESET}")
            return
        
        response = await self._test_endpoint(
            "POST", f"/api/trades/paper/{self.trade_id}/close?exit_price=46000",
            expected_status=200,
            description="Close Paper Trade"
        )
        
        if response:
            data = response.json()
            trade_data = data.get('data', {})
            pnl = trade_data.get('pnl', 0)
            print(f"   Exit Price: ${trade_data.get('exit_price', 'N/A')}")
            print(f"   PnL: ${pnl:,.2f}")
            print(f"   Status: CLOSED")
    
    # ========================================================================
    # PORTFOLIO TESTS
    # ========================================================================
    
    async def test_get_portfolio(self):
        """Test get portfolio endpoint."""
        if not self.user_id:
            print(f"   {YELLOW}⊘ Skipped (no user){RESET}")
            return
        
        response = await self._test_endpoint(
            "GET", f"/api/portfolio/{self.user_id}",
            expected_status=200,
            description="Get Portfolio Summary"
        )
        
        if response:
            data = response.json()
            print(f"   Starting Balance: ${data.get('starting_balance', 0):,.2f}")
            print(f"   Current Balance: ${data.get('current_balance', 0):,.2f}")
            print(f"   Total PnL: ${data.get('total_pnl', 0):,.2f}")
            print(f"   Win Rate: {data.get('win_rate', 0):.1f}%")
    
    async def test_get_portfolio_metrics(self):
        """Test get portfolio metrics endpoint."""
        if not self.user_id:
            print(f"   {YELLOW}⊘ Skipped (no user){RESET}")
            return
        
        response = await self._test_endpoint(
            "GET", f"/api/portfolio/{self.user_id}/metrics",
            expected_status=200,
            description="Get Portfolio Metrics"
        )
        
        if response:
            data = response.json()
            print(f"   Sharpe Ratio: {data.get('sharpe_ratio', 'N/A')}")
            print(f"   Max Drawdown: {data.get('max_drawdown', 'N/A')}")
            print(f"   Total Return: {data.get('total_return', 'N/A')}")
            print(f"   Win Rate: {data.get('win_rate', 'N/A')}")
    
    async def test_get_positions(self):
        """Test get open positions endpoint."""
        if not self.user_id:
            print(f"   {YELLOW}⊘ Skipped (no user){RESET}")
            return
        
        response = await self._test_endpoint(
            "GET", f"/api/positions/{self.user_id}",
            expected_status=200,
            description="Get Open Positions"
        )
        
        if response:
            data = response.json()
            positions = data.get('positions', [])
            print(f"   Open positions: {len(positions)}")
            if positions:
                for pos in positions[:3]:
                    print(f"   - {pos.get('asset', 'N/A')}: {pos.get('quantity', 0)} @ ${pos.get('entry_price', 0):.2f}")
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    async def _test_endpoint(self, method: str, endpoint: str, **kwargs) -> Any:
        """Execute a test endpoint call."""
        expected_status = kwargs.pop('expected_status', 200)
        description = kwargs.pop('description', endpoint)
        
        try:
            url = f"{BASE_URL}{endpoint}"
            
            if method == "GET":
                response = await self.client.get(url, **kwargs)
            elif method == "POST":
                response = await self.client.post(url, **kwargs)
            elif method == "PUT":
                response = await self.client.put(url, **kwargs)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            if response.status_code == expected_status:
                self.results.append({
                    "test": description,
                    "status": "PASS",
                    "code": response.status_code
                })
                print(f"{GREEN}✅ {description:<40} [{response.status_code}]{RESET}")
                return response
            else:
                self.results.append({
                    "test": description,
                    "status": "FAIL",
                    "code": response.status_code,
                    "expected": expected_status
                })
                print(f"{RED}❌ {description:<40} [Expected: {expected_status}, Got: {response.status_code}]{RESET}")
                print(f"   Response: {response.text[:200]}")
                return None
        
        except Exception as e:
            self.results.append({
                "test": description,
                "status": "ERROR",
                "error": str(e)
            })
            print(f"{RED}❌ {description:<40} [ERROR: {str(e)[:50]}]{RESET}")
            return None
    
    async def print_summary(self):
        """Print test summary."""
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}📊 Test Summary{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        passed = len([r for r in self.results if r.get('status') == 'PASS'])
        failed = len([r for r in self.results if r.get('status') == 'FAIL'])
        errors = len([r for r in self.results if r.get('status') == 'ERROR'])
        total = len(self.results)
        
        print(f"Total Tests:  {total}")
        print(f"{GREEN}Passed:       {passed}{RESET}")
        print(f"{RED}Failed:       {failed}{RESET}")
        print(f"{RED}Errors:       {errors}{RESET}")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0 or errors > 0:
            print(f"{RED}Failed/Error Tests:{RESET}")
            for result in self.results:
                if result.get('status') in ['FAIL', 'ERROR']:
                    print(f"  - {result.get('test')}")
        
        print(f"\n{BLUE}{'='*70}{RESET}\n")


async def main():
    """Run the test suite."""
    suite = BackendTestSuite()
    await suite.run_all_tests()
    await suite.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
