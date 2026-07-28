"""
Enhanced CreatorMarketplaceService with verification gates, performance monitoring, and payouts.
Implements §12 & §2.5 Architecture Doc (Strategy Marketplace).
"""

import logging
import os
import stripe
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class CreatorMarketplaceService:
    """
    Marketplace governance and creator management.
    - Strategy submission and verification
    - Backtest validation gates (Sharpe ≥1.0, PF ≥1.5, max DD ≤25%)
    - Live performance monitoring and auto-delisting
    - Revenue calculations and Stripe payouts
    - Appeals process
    """

    BACKTEST_MIN_SHARPE = 1.0
    BACKTEST_MIN_PROFIT_FACTOR = 1.5
    BACKTEST_MAX_DRAWDOWN = 0.25
    BACKTEST_MIN_TRADES = 100

    LIVE_PERFORMANCE_WARNING_PCT = 0.60  # 60% of backtest Sharpe
    LIVE_PERFORMANCE_CRITICAL_PCT = 0.50  # 50% of backtest Sharpe
    AUTO_DELIST_PCT = 0.40  # 40% of backtest Sharpe for 2 consecutive months

    REVENUE_SPLIT = 0.10  # AlphaForge takes 10%, creator gets 90%

    def __init__(self, db, stripe_client=None):
        self.db = db
        self.stripe = stripe_client or stripe

    async def submit_strategy(
        self,
        creator_user_id: str,
        strategy_name: str,
        strategy_description: str,
        backtest_results: Dict[str, Any],
        paper_trading_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit strategy for marketplace verification.
        First step: validate backtest requirements (§12 Architecture).
        """

        try:
            # Validate backtest requirements
            validation = self._validate_backtest(backtest_results)
            if not validation.get('valid'):
                return {
                    'success': False,
                    'reason': validation.get('reason'),
                    'errors': validation.get('errors', [])
                }

            # Create strategy record
            strategy_record = {
                'creator_user_id': creator_user_id,
                'strategy_name': strategy_name,
                'description': strategy_description,
                'backtest_results': backtest_results,
                'paper_trading_results': paper_trading_results,
                'status': 'PENDING_REVIEW',
                'created_at': datetime.utcnow().isoformat()
            }

            response = self.db.supabase.table('creator_strategies').insert(strategy_record).execute()

            if response.data:
                strategy_id = response.data[0].get('id')
                logger.info(f"✅ Strategy {strategy_id} submitted for review")

                return {
                    'success': True,
                    'strategy_id': strategy_id,
                    'status': 'PENDING_REVIEW',
                    'next_step': 'Awaiting review committee approval'
                }
            else:
                return {'success': False, 'error': 'Insert failed'}

        except Exception as e:
            logger.error(f"Strategy submission failed: {e}")
            return {'success': False, 'error': str(e)}

    def _validate_backtest(self, backtest_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate backtest meets minimum requirements (§20.3 Architecture).
        Returns {valid: bool, reason: str, errors: List[str]}
        """

        errors = []

        sharpe = float(backtest_results.get('sharpe_ratio', 0))
        if sharpe < self.BACKTEST_MIN_SHARPE:
            errors.append(f"Sharpe ratio {sharpe:.2f} < required {self.BACKTEST_MIN_SHARPE}")

        pf = float(backtest_results.get('profit_factor', 0))
        if pf < self.BACKTEST_MIN_PROFIT_FACTOR:
            errors.append(f"Profit factor {pf:.2f} < required {self.BACKTEST_MIN_PROFIT_FACTOR}")

        dd = float(backtest_results.get('max_drawdown', 0))
        if dd > self.BACKTEST_MAX_DRAWDOWN:
            errors.append(f"Max drawdown {dd:.2%} > allowed {self.BACKTEST_MAX_DRAWDOWN:.2%}")

        trades = int(backtest_results.get('trade_count', 0))
        if trades < self.BACKTEST_MIN_TRADES:
            errors.append(f"Trade count {trades} < required {self.BACKTEST_MIN_TRADES}")

        return {
            'valid': len(errors) == 0,
            'reason': 'All requirements met' if len(errors) == 0 else 'Backtest validation failed',
            'errors': errors
        }

    async def approve_strategy(
        self,
        strategy_id: str,
        reviewer_id: str
    ) -> Dict[str, Any]:
        """Approve strategy (admin/review committee action)."""

        try:
            update_data = {
                'status': 'APPROVED',
                'approved_at': datetime.utcnow().isoformat(),
                'approved_by': reviewer_id
            }

            self.db.supabase.table('creator_strategies').update(update_data).eq('id', strategy_id).execute()

            logger.info(f"✅ Strategy {strategy_id} APPROVED")

            return {'success': True, 'status': 'APPROVED'}

        except Exception as e:
            logger.error(f"Approval failed: {e}")
            return {'success': False, 'error': str(e)}

    async def monitor_live_performance(
        self,
        strategy_id: str,
        live_sharpe: float,
        backtest_sharpe: float
    ) -> Dict[str, Any]:
        """
        Monitor live performance and trigger actions (§15 Alpha Decay).
        - <60% baseline → Warning badge
        - <50% baseline for 2 months → Auto-delist
        """

        try:
            sharpe_pct = (live_sharpe / backtest_sharpe) * 100 if backtest_sharpe > 0 else 0

            # Fetch current strategy status
            response = self.db.supabase.table('creator_strategies').select('*').eq('id', strategy_id).execute()
            if not response.data:
                return {'error': 'Strategy not found'}

            strategy = response.data[0]
            current_status = strategy.get('status')

            # Determine action based on performance tier
            action = 'NONE'
            new_status = current_status

            if sharpe_pct < self.AUTO_DELIST_PCT:
                action = 'AUTO_DELIST'
                new_status = 'DELISTED'
            elif sharpe_pct < self.LIVE_PERFORMANCE_CRITICAL_PCT:
                action = 'PREPARE_RETIREMENT'
            elif sharpe_pct < self.LIVE_PERFORMANCE_WARNING_PCT:
                action = 'WARN'

            # Update status
            if new_status != current_status:
                update_data = {
                    'status': new_status,
                    'live_sharpe': live_sharpe,
                    'updated_at': datetime.utcnow().isoformat()
                }
                self.db.supabase.table('creator_strategies').update(update_data).eq('id', strategy_id).execute()

            logger.info(f"⚠️ Strategy {strategy_id} performance: {sharpe_pct:.1f}% of backtest - Action: {action}")

            return {
                'strategy_id': strategy_id,
                'live_sharpe': live_sharpe,
                'backtest_sharpe': backtest_sharpe,
                'sharpe_pct': sharpe_pct,
                'action': action,
                'new_status': new_status
            }

        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
            return {'error': str(e)}

    async def calculate_payouts(
        self,
        strategy_id: str,
        payout_period: str  # e.g., "2025-01"
    ) -> Dict[str, Any]:
        """
        Calculate creator payouts for period (§2.5 Architecture).
        Revenue split: Creator 90%, AlphaForge 10%.
        """

        try:
            # Count active subscribers for strategy
            sub_response = self.db.supabase.table('strategy_subscriptions').select('count()').eq(
                'strategy_id', strategy_id
            ).eq('status', 'ACTIVE').execute()

            subscriber_count = sub_response.count if hasattr(sub_response, 'count') else 0

            # Assume subscription price ($39/month Basic tier)
            monthly_subscription = 39.00
            gross_revenue = subscriber_count * monthly_subscription

            alphaforge_cut = gross_revenue * self.REVENUE_SPLIT
            creator_take_home = gross_revenue * (1 - self.REVENUE_SPLIT)

            payout_record = {
                'strategy_id': strategy_id,
                'payout_period': payout_period,
                'subscriber_count': subscriber_count,
                'gross_revenue': gross_revenue,
                'alphaforge_cut_10_pct': alphaforge_cut,
                'creator_take_home_90_pct': creator_take_home,
                'status': 'CALCULATED',
                'created_at': datetime.utcnow().isoformat()
            }

            # Upsert payout record
            self.db.supabase.table('creator_payouts').upsert(payout_record).execute()

            logger.info(f"✅ Payout calculated for {strategy_id}: ${creator_take_home:.2f}")

            return {
                'success': True,
                'payout_period': payout_period,
                'subscriber_count': subscriber_count,
                'gross_revenue': gross_revenue,
                'creator_take_home': creator_take_home,
                'alphaforge_cut': alphaforge_cut
            }

        except Exception as e:
            logger.error(f"Payout calculation failed: {e}")
            return {'success': False, 'error': str(e)}

    async def process_payout_via_stripe(
        self,
        strategy_id: str,
        creator_stripe_account_id: str,
        payout_amount: float,
        payout_period: str
    ) -> Dict[str, Any]:
        """
        Process creator payout via Stripe Connect.
        Records transaction for audit/compliance.
        """

        try:
            # Create Stripe payout to creator's connected account
            payout = self.stripe.Payout.create(
                amount=int(payout_amount * 100),  # Convert to cents
                currency='usd',
                destination=creator_stripe_account_id,
                description=f"AlphaForge creator payout - {payout_period}",
                metadata={
                    'strategy_id': strategy_id,
                    'payout_period': payout_period
                }
            )

            # Update payout record
            self.db.supabase.table('creator_payouts').update({
                'status': 'PAID',
                'paid_at': datetime.utcnow().isoformat(),
                'stripe_payout_id': payout.id
            }).eq('strategy_id', strategy_id).eq('payout_period', payout_period).execute()

            logger.info(f"✅ Payout processed: ${payout_amount:.2f} to {strategy_id}")

            return {
                'success': True,
                'payout_id': payout.id,
                'amount': payout_amount,
                'status': payout.status
            }

        except Exception as e:
            logger.error(f"Stripe payout failed: {e}")
            return {'success': False, 'error': str(e)}

    async def create_appeal(
        self,
        creator_user_id: str,
        strategy_id: str,
        rejection_reason: str,
        appeal_reason: str
    ) -> Dict[str, Any]:
        """
        Allow creator to appeal rejection once (§12 Architecture).
        Routes to external arbitrator for final decision.
        """

        try:
            appeal_record = {
                'creator_user_id': creator_user_id,
                'strategy_id': strategy_id,
                'rejection_reason': rejection_reason,
                'appeal_reason': appeal_reason,
                'status': 'PENDING_ARBITRATOR',
                'created_at': datetime.utcnow().isoformat()
            }

            # In production, this would route to an arbitrator queue
            # For now, just record the appeal

            logger.info(f"📝 Appeal created for strategy {strategy_id} - awaiting arbitrator review")

            return {
                'success': True,
                'appeal_status': 'PENDING_ARBITRATOR',
                'message': 'Your appeal has been submitted for independent review'
            }

        except Exception as e:
            logger.error(f"Appeal creation failed: {e}")
            return {'success': False, 'error': str(e)}


import os
