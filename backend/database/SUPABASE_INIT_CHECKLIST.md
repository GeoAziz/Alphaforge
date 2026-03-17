# Supabase DB Init Checklist (Phase 1)

## 1) Run migration SQL
1. Open Supabase project: https://xouqexmepzkxlymihjuw.supabase.co
2. Go to **SQL Editor** → **New Query**.
3. Open and copy all contents of:
   - `backend/database/supabase_phase1_init.sql`
4. Paste and click **Run**.
5. Confirm query completes without errors.

## 2) Verify schema
Run:

```sql
SELECT tablename
FROM pg_tables
WHERE schemaname='public'
ORDER BY tablename;
```

Expected core tables include:
- `users`, `signals`, `paper_trades`, `positions`, `portfolios`
- `creator_profiles`, `creator_strategies`, `strategy_subscriptions`, `strategy_paper_trades`
- `kyc_verifications`, `audit_logs`, `external_signals`, `external_signal_rules`
- `api_keys`, `backtests`, `chat_messages`, `notifications`, `user_risk_settings`, `strategies`

## 3) Verify RLS + policies
Run:

```sql
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE schemaname='public'
ORDER BY tablename, policyname;
```

Expected policies:
- `Users can see own data` (users)
- `Users can see own portfolio` (portfolios)
- `Users can see own trades` (paper_trades)
- `Users can insert own trades` (paper_trades)
- `Users can insert own positions` (positions)

## 4) Backend config check
After schema is live:
1. Ensure backend runtime has `API_ENV=production` only when production secrets are set.
2. Ensure `DATABASE_URL`, `SUPABASE_URL`, and `SUPABASE_SERVICE_KEY` are present in deployment env.
3. Start backend and verify `/ready` and `/health`.

## 5) Smoke test
From `backend/`:

```bash
pytest -q
```

If green, mark RoadMap Task 1.2 complete.
