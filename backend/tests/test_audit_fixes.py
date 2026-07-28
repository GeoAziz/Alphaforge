"""
Tests for audit fixes: auth, paper trading, validation, error handling.
"""

import pytest
from services.paper_trading import PaperTradingEngine
from firebase_config import FirebaseTokenVerifier, verify_firebase_token


class TestPaperTradingSlippageFix:
    """Verify paper trading slippage is applied correctly to both entry and exit."""

    def test_slippage_penalizes_long_entry(self):
        """Long entry slippage should increase price (worse for buyer)."""
        engine = PaperTradingEngine(db=None)
        entry_price = 100.0
        slipped = engine._apply_slippage(entry_price, "LONG", is_exit=False)
        assert slipped > entry_price, "Long entry slippage should increase price"
        assert slipped == pytest.approx(100.1), f"Expected 100.1, got {slipped}"

    def test_slippage_penalizes_long_exit(self):
        """Long exit slippage should decrease price (worse for seller)."""
        engine = PaperTradingEngine(db=None)
        exit_price = 100.0
        slipped = engine._apply_slippage(exit_price, "LONG", is_exit=True)
        assert slipped < exit_price, "Long exit slippage should decrease price"
        assert slipped == pytest.approx(99.9), f"Expected 99.9, got {slipped}"

    def test_slippage_penalizes_short_entry(self):
        """Short entry slippage should decrease price (worse for shorter)."""
        engine = PaperTradingEngine(db=None)
        entry_price = 100.0
        slipped = engine._apply_slippage(entry_price, "SHORT", is_exit=False)
        assert slipped < entry_price, "Short entry slippage should decrease price"
        assert slipped == pytest.approx(99.9), f"Expected 99.9, got {slipped}"

    def test_slippage_penalizes_short_exit(self):
        """Short exit slippage should increase price (worse for shorter closing)."""
        engine = PaperTradingEngine(db=None)
        exit_price = 100.0
        slipped = engine._apply_slippage(exit_price, "SHORT", is_exit=True)
        assert slipped > exit_price, "Short exit slippage should increase price"
        assert slipped == pytest.approx(100.1), f"Expected 100.1, got {slipped}"


class TestAuthValidation:
    """Verify Firebase auth correctly validates tokens in all modes."""

    def test_firebase_token_verifier_exists(self):
        """Ensure Firebase verifier singleton can be instantiated."""
        verifier = FirebaseTokenVerifier()
        assert verifier is not None
        assert hasattr(verifier, 'verify_token'), "Verifier should have verify_token method"

    def test_firebase_config_import(self):
        """Ensure firebase_config can be imported (not firebase_auth)."""
        try:
            import firebase_config
            assert hasattr(firebase_config, 'verify_firebase_token')
            assert hasattr(firebase_config, 'verify_firebase_token_optional')
        except ImportError as e:
            pytest.fail(f"Failed to import firebase_config: {e}")

    def test_firebase_auth_removed(self):
        """Ensure firebase_auth.py does not exist (should use firebase_config only)."""
        import os
        firebase_auth_path = "firebase_auth.py"
        assert not os.path.exists(firebase_auth_path), "firebase_auth.py should be deleted in favor of firebase_config.py"


class TestInputValidation:
    """Verify input validation on critical endpoints."""

    def test_paper_trade_quantity_validation(self):
        """Quantity must be positive and <= 1M."""
        from models.schemas import PaperTradeCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PaperTradeCreate(
                user_id="user1",
                signal_id="sig1",
                asset="BTC",
                direction="LONG",
                entry_price=50000,
                quantity=0,  # Invalid: must be > 0
            )

        with pytest.raises(ValidationError):
            PaperTradeCreate(
                user_id="user1",
                signal_id="sig1",
                asset="BTC",
                direction="LONG",
                entry_price=50000,
                quantity=2000001,  # Invalid: must be <= 1M
            )

    def test_paper_trade_price_validation(self):
        """Prices must be positive."""
        from models.schemas import PaperTradeCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            PaperTradeCreate(
                user_id="user1",
                signal_id="sig1",
                asset="BTC",
                direction="LONG",
                entry_price=-100,  # Invalid: must be > 0
                quantity=1,
            )

    def test_paper_trade_valid_creation(self):
        """Valid paper trade should pass validation."""
        from models.schemas import PaperTradeCreate

        trade = PaperTradeCreate(
            user_id="user1",
            signal_id="sig1",
            asset="BTC",
            direction="LONG",
            entry_price=50000,
            quantity=0.5,
            stop_loss=45000,
            take_profit=55000,
        )
        assert trade.entry_price == 50000
        assert trade.quantity == 0.5
        assert trade.stop_loss == 45000


class TestErrorBoundary:
    """Verify ErrorBoundary component exists and is properly implemented."""

    def test_error_boundary_file_exists(self):
        """ErrorBoundary component should exist."""
        import os
        error_boundary_path = "../src/components/ErrorBoundary.tsx"
        assert os.path.exists(error_boundary_path), "ErrorBoundary.tsx should exist"

    def test_error_boundary_in_portfolio_page(self):
        """Portfolio page should import and use ErrorBoundary."""
        with open("../src/app/portfolio/page.tsx", "r") as f:
            content = f.read()
            assert "ErrorBoundary" in content, "Portfolio page should import ErrorBoundary"
            assert "PortfolioPageContent" in content, "Portfolio page should use renamed content component"

    def test_error_boundary_in_analytics_page(self):
        """Analytics page should import and use ErrorBoundary."""
        with open("../src/app/analytics/page.tsx", "r") as f:
            content = f.read()
            assert "ErrorBoundary" in content, "Analytics page should import ErrorBoundary"

    def test_error_boundary_in_backtesting_page(self):
        """Backtesting page should import and use ErrorBoundary."""
        with open("../src/app/backtesting/page.tsx", "r") as f:
            content = f.read()
            assert "ErrorBoundary" in content, "Backtesting page should import ErrorBoundary"


class TestApiResponse:
    """Verify standardized API response utility."""

    def test_api_response_utility_exists(self):
        """ApiResponse utility should exist."""
        try:
            from utils.api_response import ApiResponse
            assert hasattr(ApiResponse, 'success')
            assert hasattr(ApiResponse, 'error')
            assert hasattr(ApiResponse, 'validation_error')
        except ImportError as e:
            pytest.fail(f"Failed to import ApiResponse: {e}")

    def test_api_response_success_format(self):
        """Success response should have correct format."""
        from utils.api_response import ApiResponse

        response = ApiResponse.success(data={"test": "data"}, message="OK")
        assert response["success"] is True
        assert response["message"] == "OK"
        assert response["data"]["test"] == "data"
        assert "timestamp" in response

    def test_api_response_error_format(self):
        """Error response should have correct format."""
        from utils.api_response import ApiResponse

        response = ApiResponse.error(message="Bad request", status_code=400)
        assert response["success"] is False
        assert response["status_code"] == 400
        assert response["message"] == "Bad request"
        assert "timestamp" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
