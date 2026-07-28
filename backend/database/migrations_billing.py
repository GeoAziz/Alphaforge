"""
Database migration for subscription billing (PRD §16 — Subscription-First model).

Adds Stripe-backed subscription fields to `users` plus a billing_events audit
table. Apply the same way as migrations_gap_features.py:

    python -c "from database.migrations_billing import run_billing_migrations; from database.db import Database; db = Database(); run_billing_migrations(db)"
"""

MIGRATIONS_BILLING = """

-- ============================================================================
-- SUBSCRIPTION BILLING (Stripe)
-- ============================================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier TEXT DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'none';
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_period_end TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);

-- Immutable log of billing webhook events, for support/dispute investigation.
CREATE TABLE IF NOT EXISTS billing_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  stripe_event_id TEXT UNIQUE,
  event_type TEXT NOT NULL,
  payload JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_events_user ON billing_events(user_id);

"""


def run_billing_migrations(db):
    """Execute the subscription billing migration."""
    try:
        db.supabase.rpc('exec_sql', {'sql': MIGRATIONS_BILLING})
        print("✅ Billing migration completed successfully")
        return True
    except Exception as e:
        print(f"❌ Billing migration failed: {e}")
        return False
