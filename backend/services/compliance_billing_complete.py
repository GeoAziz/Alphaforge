"""
Compliance & Billing Services
- Disclaimer acknowledgment tracking (§7 Architecture)
- Age gate enforcement (18+)
- Stripe subscription management ($39/month Basic tier)
"""

import logging
import stripe
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class ComplianceService:
    """
    Compliance tracking including disclaimers and age verification.
    Per §7 Architecture: 7-point contextual disclaimer system.
    """

    DISCLAIMER_KEYS = [
        'FINANCIAL_PROMOTION',
        'PAST_PERFORMANCE',
        'LEVERAGE_RISK',
        'EXECUTION_RISK',
        'MODEL_RISK',
        'TECH_RISK',
        'AGE_VERIFICATION'
    ]

    def __init__(self, db):
        self.db = db

    async def track_disclaimer_acknowledgment(
        self,
        user_id: str,
        disclaimer_key: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        method: str = 'modal_popup'
    ) -> Dict[str, Any]:
        """
        Track user acknowledgment of disclaimers for compliance evidence.
        Per §7: Required before first trade.
        """

        try:
            ack_record = {
                'user_id': user_id,
                'disclaimer_key': disclaimer_key,
                'disclaimer_version': '1.0',
                'acknowledged_at': datetime.utcnow().isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent,
                'method': method,
                'created_at': datetime.utcnow().isoformat()
            }

            self.db.supabase.table('disclaimer_acknowledgments').insert(ack_record).execute()

            logger.info(f"✅ Disclaimer {disclaimer_key} acknowledged by {user_id}")

            return {'success': True, 'acknowledged': True}

        except Exception as e:
            logger.error(f"Disclaimer tracking failed: {e}")
            return {'success': False, 'error': str(e)}

    async def get_pending_disclaimers(self, user_id: str) -> List[str]:
        """Get disclaimers still needing acknowledgment."""

        try:
            # Fetch acknowledged disclaimers
            response = self.db.supabase.table('disclaimer_acknowledgments').select('disclaimer_key').eq(
                'user_id', user_id
            ).execute()

            acknowledged = [d['disclaimer_key'] for d in (response.data or [])]
            pending = [key for key in self.DISCLAIMER_KEYS if key not in acknowledged]

            return pending

        except Exception as e:
            logger.error(f"Pending disclaimers fetch failed: {e}")
            return self.DISCLAIMER_KEYS

    async def enforce_age_gate(self, user_id: str, date_of_birth: str) -> Tuple[bool, str]:
        """
        Enforce 18+ age requirement per §7 Architecture.
        Returns (allowed: bool, reason: str)
        """

        try:
            from datetime import datetime

            # Parse DOB
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
            age = (datetime.utcnow() - dob).days // 365

            if age < 18:
                return False, f"You must be 18+ to trade. Your age: {age} years"

            return True, "Age verification passed"

        except Exception as e:
            logger.error(f"Age verification failed: {e}")
            return False, "Age verification error"

    async def enforce_disclaimer_gate(self, user_id: str) -> Tuple[bool, str]:
        """Block trading if critical disclaimers not acknowledged."""

        try:
            pending = await self.get_pending_disclaimers(user_id)

            critical_disclaimers = [
                'FINANCIAL_PROMOTION',
                'LEVERAGE_RISK',
                'PAST_PERFORMANCE'
            ]

            pending_critical = [d for d in pending if d in critical_disclaimers]

            if pending_critical:
                return False, f"Must acknowledge: {', '.join(pending_critical)}"

            return True, "All required disclaimers acknowledged"

        except Exception as e:
            logger.error(f"Disclaimer gate check failed: {e}")
            return False, "Compliance verification error"


class BillingService:
    """
    Subscription billing via Stripe.
    Per §16 Architecture: $39/month Basic tier (MVP).
    """

    BASIC_TIER_PRICE_CENTS = 3900  # $39.00

    def __init__(self, db):
        self.db = db

    async def create_subscription(
        self,
        user_id: str,
        email: str,
        plan: str = 'basic',
        trial_days: int = 7
    ) -> Dict[str, Any]:
        """
        Create Stripe subscription for user.
        Includes 7-day free trial for paper trading.
        """

        try:
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=email,
                metadata={'user_id': user_id}
            )

            customer_id = customer.id

            # Create subscription (price ID must be configured in Stripe)
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'AlphaForge Basic',
                            'description': 'AI trading signals and paper trading'
                        },
                        'unit_amount': self.BASIC_TIER_PRICE_CENTS,
                        'recurring': {
                            'interval': 'month'
                        }
                    }
                }],
                trial_period_days=trial_days,
                metadata={'user_id': user_id}
            )

            # Store subscription in database
            sub_record = {
                'user_id': user_id,
                'plan': plan,
                'stripe_subscription_id': subscription.id,
                'stripe_customer_id': customer_id,
                'status': 'ACTIVE' if subscription.status == 'active' else 'TRIAL',
                'billing_cycle_start': datetime.utcfromtimestamp(subscription.current_period_start).isoformat(),
                'billing_cycle_end': datetime.utcfromtimestamp(subscription.current_period_end).isoformat(),
                'trial_end': datetime.utcfromtimestamp(subscription.trial_end).isoformat() if subscription.trial_end else None,
                'price_monthly': 39.00,
                'created_at': datetime.utcnow().isoformat()
            }

            self.db.supabase.table('subscriptions').insert(sub_record).execute()

            logger.info(f"✅ Subscription created for {user_id}: {subscription.id}")

            return {
                'success': True,
                'subscription_id': subscription.id,
                'customer_id': customer_id,
                'status': subscription.status,
                'trial_end': subscription.trial_end
            }

        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            return {'success': False, 'error': str(e)}

    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get subscription status for user."""

        try:
            response = self.db.supabase.table('subscriptions').select('*').eq('user_id', user_id).execute()

            if not response.data:
                return {
                    'subscribed': False,
                    'status': 'NO_SUBSCRIPTION',
                    'plan': 'free'
                }

            sub = response.data[0]
            status = sub.get('status')
            is_active = status in ['ACTIVE', 'TRIAL']

            return {
                'subscribed': is_active,
                'status': status,
                'plan': sub.get('plan'),
                'billing_cycle_end': sub.get('billing_cycle_end'),
                'trial_end': sub.get('trial_end'),
                'stripe_subscription_id': sub.get('stripe_subscription_id')
            }

        except Exception as e:
            logger.error(f"Subscription fetch failed: {e}")
            return {'subscribed': False, 'error': str(e)}

    async def enforce_subscription_gate(self, user_id: str) -> Tuple[bool, str]:
        """Block live trading if subscription not active (outside trial)."""

        try:
            sub_status = await self.get_subscription_status(user_id)

            if not sub_status.get('subscribed'):
                return False, "Active subscription required for live trading (7-day free trial available)"

            status = sub_status.get('status')
            if status == 'PAST_DUE':
                return False, "Subscription payment overdue - please update payment method"

            if status == 'CANCELLED':
                return False, "Subscription cancelled - renew to resume trading"

            return True, "Subscription active"

        except Exception as e:
            logger.error(f"Subscription gate check failed: {e}")
            return False, "Billing verification error"

    async def update_payment_method(
        self,
        user_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Update payment method on file."""

        try:
            sub_response = self.db.supabase.table('subscriptions').select('stripe_customer_id').eq(
                'user_id', user_id
            ).execute()

            if not sub_response.data:
                return {'success': False, 'error': 'No subscription found'}

            customer_id = sub_response.data[0]['stripe_customer_id']

            # Update customer payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={
                    'default_payment_method': payment_method_id
                }
            )

            logger.info(f"✅ Payment method updated for {user_id}")

            return {'success': True, 'message': 'Payment method updated'}

        except Exception as e:
            logger.error(f"Payment method update failed: {e}")
            return {'success': False, 'error': str(e)}


from typing import List
