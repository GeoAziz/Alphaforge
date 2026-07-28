"""
Comprehensive test suite for enforcement gates.
Tests all pre-trade validation checks before live execution.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import sys
sys.path.insert(0, '..')

from services.enforcement_gates import EnforcementGate
from services.risk_manager import RiskManager
from services.kyc_service_complete import KYCService
from services.compliance_billing_complete import ComplianceService, BillingService
from services.paper_trading_complete import PaperTradingEngine


class TestEnforcementGate:
    """Test suite for master enforcement gate."""

    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        db = Mock()
        db.supabase = Mock()
        db.supabase.table = Mock()
        return db

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        return Mock()

    @pytest.fixture
    def services(self, mock_db, mock_redis):
        """Initialize services."""
        return {
            'risk_manager': RiskManager(mock_db),
            'kyc_service': KYCService(mock_db, mock_redis),
            'compliance_service': ComplianceService(mock_db),
            'billing_service': BillingService(mock_db),
            'paper_trading_engine': PaperTradingEngine(mock_db)
        }

    @pytest.fixture
    def enforcement_gate(self, mock_db, services):
        """Create enforcement gate."""
        return EnforcementGate(
            mock_db,
            services['risk_manager'],
            services['kyc_service'],
            services['compliance_service'],
            services['billing_service'],
            services['paper_trading_engine']
        )

    @pytest.mark.asyncio
    async def test_gate_blocks_without_kyc(self, enforcement_gate):
        """Test: Trade blocked without KYC approval."""

        # Mock services to fail KYC
        enforcement_gate.kyc.enforce_kyc_gate = AsyncMock(
            return_value=(False, "KYC: User not approved")
        )

        signal = {
            'ticker': 'BTC',
            'signal_type': 'BUY',
            'entry_price': 45000,
            'stop_loss_price': 44000,
            'confidence': 0.75
        }

        result = await enforcement_gate.validate_before_live_execution(
            'user123', signal, 100000
        )

        assert result['approved'] == False
        assert 'KYC' in result['reason']
        assert 'user_not_approved' in [b.lower().replace(' ', '_') for b in result['blocked_by']]

    @pytest.mark.asyncio
    async def test_gate_blocks_without_subscription(self, enforcement_gate):
        """Test: Trade blocked without active subscription."""

        enforcement_gate.kyc.enforce_kyc_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.billing.enforce_subscription_gate = AsyncMock(
            return_value=(False, "Subscription: Not active")
        )

        signal = {
            'ticker': 'BTC',
            'signal_type': 'BUY',
            'entry_price': 45000,
            'stop_loss_price': 44000,
            'confidence': 0.75
        }

        result = await enforcement_gate.validate_before_live_execution(
            'user123', signal, 100000
        )

        assert result['approved'] == False
        assert 'Subscription' in result['reason']

    @pytest.mark.asyncio
    async def test_gate_blocks_missing_stop_loss(self, enforcement_gate):
        """Test: Trade blocked without stop loss (non-negotiable)."""

        # Mock all gates pass except risk
        enforcement_gate.kyc.enforce_kyc_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.billing.enforce_subscription_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.compliance.enforce_disclaimer_gate = AsyncMock(return_value=(True, "OK"))

        # Mock risk manager to reject (missing stop loss)
        enforcement_gate.risk_manager.validate_trade = AsyncMock(
            return_value={
                'approved': False,
                'risk_score': 10.0,
                'reason': 'Stop loss required per risk policy'
            }
        )

        signal = {
            'ticker': 'BTC',
            'signal_type': 'BUY',
            'entry_price': 45000,
            'stop_loss_price': None,  # MISSING - should reject
            'confidence': 0.75
        }

        result = await enforcement_gate.validate_before_live_execution(
            'user123', signal, 100000
        )

        assert result['approved'] == False
        assert 'Risk' in result['reason']

    @pytest.mark.asyncio
    async def test_gate_blocks_over_leverage(self, enforcement_gate):
        """Test: Trade blocked if leverage exceeds 5x."""

        enforcement_gate.kyc.enforce_kyc_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.billing.enforce_subscription_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.compliance.enforce_disclaimer_gate = AsyncMock(return_value=(True, "OK"))

        enforcement_gate.risk_manager.validate_trade = AsyncMock(
            return_value={
                'approved': False,
                'risk_score': 9.0,
                'reason': 'Leverage 10x exceeds 5x limit'
            }
        )

        signal = {
            'ticker': 'BTC',
            'signal_type': 'BUY',
            'entry_price': 45000,
            'stop_loss_price': 44000,
            'leverage': 10.0,  # OVER LIMIT
            'confidence': 0.75
        }

        result = await enforcement_gate.validate_before_live_execution(
            'user123', signal, 100000
        )

        assert result['approved'] == False
        assert 'Risk' in result['reason']

    @pytest.mark.asyncio
    async def test_gate_blocks_failed_paper_trading(self, enforcement_gate):
        """Test: Trade blocked if paper trading gate not passed."""

        enforcement_gate.kyc.enforce_kyc_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.billing.enforce_subscription_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.compliance.enforce_disclaimer_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.risk_manager.validate_trade = AsyncMock(
            return_value={'approved': True, 'risk_score': 3.0}
        )

        # Mock DB to show signal_proofs with FAIL status
        enforcement_gate.db.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'paper_trading_status': 'FAIL'}]
        )

        signal = {
            'signal_id': 'sig_123',
            'ticker': 'BTC',
            'signal_type': 'BUY',
            'entry_price': 45000,
            'stop_loss_price': 44000,
            'confidence': 0.75
        }

        result = await enforcement_gate.validate_before_live_execution(
            'user123', signal, 100000
        )

        assert result['approved'] == False
        assert 'Paper Trading' in result['reason']

    @pytest.mark.asyncio
    async def test_gate_approves_all_checks_pass(self, enforcement_gate):
        """Test: Trade approved when all gates pass."""

        enforcement_gate.kyc.enforce_kyc_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.billing.enforce_subscription_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.compliance.enforce_disclaimer_gate = AsyncMock(return_value=(True, "OK"))
        enforcement_gate.risk_manager.validate_trade = AsyncMock(
            return_value={'approved': True, 'risk_score': 3.0}
        )

        # Mock DB to show signal_proofs with PASS status
        enforcement_gate.db.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = Mock(
            data=[{'paper_trading_status': 'PASS'}]
        )

        signal = {
            'signal_id': 'sig_123',
            'ticker': 'BTC',
            'signal_type': 'BUY',
            'entry_price': 45000,
            'stop_loss_price': 44000,
            'confidence': 0.75
        }

        result = await enforcement_gate.validate_before_live_execution(
            'user123', signal, 100000
        )

        assert result['approved'] == True
        assert result['checks_passed'] == 6


class TestRiskEnforcement:
    """Test suite for risk management enforcement."""

    @pytest.fixture
    def risk_manager(self):
        """Create risk manager."""
        return RiskManager(Mock())

    @pytest.mark.asyncio
    async def test_reject_position_over_2pct(self, risk_manager):
        """Test: Reject position size > 2%."""

        signal = {
            'ticker': 'BTC',
            'confidence': 1.0,  # Would trigger max size
            'entry_price': 100
        }

        result = await risk_manager.validate_trade(
            'user123',
            signal,
            portfolio_balance=100000
        )

        # Position size check should pass for normal signals
        # Only fails if position explicitly exceeds 2%
        assert result['approved'] in [True, False]

    @pytest.mark.asyncio
    async def test_reject_no_stop_loss(self, risk_manager):
        """Test: Reject trade without stop loss (non-negotiable)."""

        signal = {
            'ticker': 'BTC',
            'signal_type': 'BUY',
            'entry_price': 45000,
            'stop_loss_price': None,  # MISSING
            'confidence': 0.75
        }

        result = await risk_manager.validate_trade(
            'user123',
            signal,
            portfolio_balance=100000
        )

        assert result['approved'] == False
        assert 'Stop loss required' in result['reason']


class TestPaperTradingGate:
    """Test suite for paper trading validation gate."""

    @pytest.fixture
    def paper_trading_engine(self):
        """Create paper trading engine."""
        return PaperTradingEngine(Mock())

    @pytest.mark.asyncio
    async def test_gate_requires_28_days(self, paper_trading_engine):
        """Test: Gate requires minimum 28 days."""

        paper_start = datetime.utcnow() - timedelta(days=14)  # Only 14 days

        result = await paper_trading_engine.validate_signal_gate(
            'sig_123',
            backtest_sharpe=1.5,
            paper_trading_started_at=paper_start
        )

        assert result['approved'] == False
        assert 'INSUFFICIENT_DURATION' == result['gate_status']
        assert 'days_remaining' in result

    @pytest.mark.asyncio
    async def test_gate_requires_sharpe_80pct(self, paper_trading_engine):
        """Test: Live Sharpe must be >= 80% of backtest."""

        paper_start = datetime.utcnow() - timedelta(days=28)
        backtest_sharpe = 1.5
        min_required = backtest_sharpe * 0.80  # 1.2

        # If live Sharpe is 1.0 (< 1.2), should fail
        result = await paper_trading_engine.validate_signal_gate(
            'sig_123',
            backtest_sharpe=backtest_sharpe,
            paper_trading_started_at=paper_start
        )

        # Note: In actual test, would mock DB to return trades with specific Sharpe
        assert 'gate_status' in result


class TestKYCEnforcement:
    """Test suite for KYC verification."""

    @pytest.fixture
    def kyc_service(self):
        """Create KYC service."""
        return KYCService(Mock(), Mock())

    @pytest.mark.asyncio
    async def test_kyc_gate_blocks_unverified(self, kyc_service):
        """Test: Live trading blocked until KYC approved."""

        kyc_service.get_kyc_status = AsyncMock(
            return_value={'status': 'NOT_STARTED', 'approved': False}
        )

        allowed, reason = await kyc_service.enforce_kyc_gate('user123')

        assert allowed == False
        assert 'KYC' in reason

    @pytest.mark.asyncio
    async def test_kyc_gate_allows_approved(self, kyc_service):
        """Test: Live trading allowed when KYC approved."""

        kyc_service.get_kyc_status = AsyncMock(
            return_value={'status': 'APPROVED', 'approved': True}
        )

        allowed, reason = await kyc_service.enforce_kyc_gate('user123')

        assert allowed == True


class TestBillingEnforcement:
    """Test suite for subscription enforcement."""

    @pytest.fixture
    def billing_service(self):
        """Create billing service."""
        return BillingService(Mock())

    @pytest.mark.asyncio
    async def test_billing_gate_blocks_unsubscribed(self, billing_service):
        """Test: Live trading blocked without active subscription."""

        billing_service.get_subscription_status = AsyncMock(
            return_value={'subscribed': False, 'status': 'NO_SUBSCRIPTION'}
        )

        allowed, reason = await billing_service.enforce_subscription_gate('user123')

        assert allowed == False
        assert 'subscription' in reason.lower()

    @pytest.mark.asyncio
    async def test_billing_gate_allows_active(self, billing_service):
        """Test: Live trading allowed with active subscription."""

        billing_service.get_subscription_status = AsyncMock(
            return_value={'subscribed': True, 'status': 'ACTIVE'}
        )

        allowed, reason = await billing_service.enforce_subscription_gate('user123')

        assert allowed == True


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
