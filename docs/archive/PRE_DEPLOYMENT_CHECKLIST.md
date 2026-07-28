# AlphaForge MVP Phase 1 - Pre-Deployment Checklist

This document provides a step-by-step checklist to validate that all Phase 1 infrastructure is ready before public deployment.

**Target Completion Time: 3-4 hours**

---

## 1. Environment Configuration ✅ Status: Verify

### 1.1 Backend Environment Variables

Location: `backend/.env`

**Required Variables (Already Set):**
- [x] `DATABASE_URL` = PostgreSQL connection string to Supabase
- [x] `SUPABASE_URL` = Supabase project URL
- [x] `SUPABASE_SERVICE_KEY` = Supabase service role key
- [x] `SUPABASE_ANON_KEY` = Supabase anonymous key
- [x] `ALPHA_VANTAGE_API_KEY` = Market data API key
- [x] `POLYGON_IO_API_KEY` = Market data API key

**Verification Command:**
```bash
cd backend
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
required = ['DATABASE_URL', 'SUPABASE_URL', 'SUPABASE_SERVICE_KEY', 'ALPHA_VANTAGE_API_KEY', 'POLYGON_IO_API_KEY']
for key in required:
    val = os.getenv(key, 'MISSING')
    status = '✅' if val != 'MISSING' else '❌'
    print(f'{status} {key}')
"
```

**Expected Output:** All ✅

### 1.2 Frontend Environment Variables

Location: `next.config.ts`

**Required:**
```typescript
// Should point to backend when deployed
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
```

**For Local Development:** Already defaults to `http://localhost:8000`
**For Production:** Will be set in Vercel during deployment

---

## 2. Database Initialization ⏳ Status: Before Deployment

### 2.1 Initialize Supabase Schema

**This MUST be done before deploying backend**

```bash
cd backend
python scripts/init_supabase_db.py
```

**Expected Output:**
```
✅ Connected to PostgreSQL
✅ Successfully executed X SQL statements
✅ All 18 core tables created
✅ RLS policies enabled: 5 policies found
✅ Database initialization complete!
```

**What This Does:**
- Creates 18 PostgreSQL tables (users, signals, portfolios, paper_trades, etc.)
- Sets up indices for performance optimization
- Enables Row-Level Security (RLS) policies for data isolation
- Initializes JSONB columns for flexible data storage

**If Already Done:** Skip to 2.2

### 2.2 Verify Schema

```bash
cd backend
python scripts/init_supabase_db.py --verify-only
```

**Expected Output:**
```
✅ All 18 core tables created
✅ RLS policies enabled: 5 policies found
```

**Do NOT Proceed** if verification fails. Check Supabase dashboard for errors.

---

## 3. Backend Health Checks ✅ Status: Automated

### 3.1 Start Backend Server

```bash
cd backend
python main.py
```

**Expected Output:**
```
✅ All services initialized
🚀 Starting AlphaForge Backend API
```

### 3.2 Verify Health Endpoint (in another terminal)

```bash
curl http://localhost:8000/health

# Expected Response:
# {"status":"ok","timestamp":"2026-03-17T...","version":"1.0.0"}
```

### 3.3 Check Database Connection

```bash
curl http://localhost:8000/ready

# Expected Response:
# {"database":"connected","..." }
```

**If "database": "disconnected":**
- Verify DATABASE_URL is correct
- Check Supabase credentials
- Ensure migrations were run (step 2.1)

---

## 4. Backend API Testing ✅ Status: Comprehensive

### 4.1 Run Unit Tests

```bash
cd backend
pytest -v
```

**Target:** ≥97% code coverage, all green ✅

**If Tests Fail:**
1. Check error messages carefully
2. Verify `.env` is populated correctly
3. Ensure database schema is initialized (step 2.1)
4. Check logs in `backend/logs/` (if enabled)

### 4.2 Run Integration Tests (E2E)

```bash
cd backend
# Make sure backend is running on port 8000 first
pytest tests/integration_e2e.py -v -s
```

**Expected:** All 30+ tests pass ✅

**Key Test Categories:**
- ✅ Health & Readiness (3 tests)
- ✅ User Management (3 tests)
- ✅ Market Data (5 tests)
- ✅ Signal Processing (2 tests)
- ✅ Portfolio Operations (2 tests)
- ✅ Paper Trading (1 test)
- ✅ Frontend API Integration (3 tests)
- ✅ System Resilience (3 tests)

**If Tests Fail:**
- Check if backend is running
- Verify API_BASE_URL in test config
- Check response status codes (may be different if data missing)

### 4.3 Test Critical User Flows Manually

**Flow 1: User Registration → Profile Setup**
```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@alphaforge.local",
    "display_name": "Test User",
    "plan": "basic",
    "risk_tolerance": "moderate"
  }'
```

**Expected:** Returns 200 with user object including ID

**Flow 2: Get Market Tickers**
```bash
curl http://localhost:8000/api/market/tickers?symbols=BTC,ETH
```

**Expected:** Returns 200 with tickers data

**Flow 3: Get Portfolio Summary**
```bash
curl http://localhost:8000/api/frontend/portfolio/{user_id}/summary
```

**Expected:** Returns 200 or 404 (404 is OK if portfolio not created yet)

---

## 5. Frontend Health Checks ✅ Status: Ready

### 5.1 Start Frontend Dev Server

```bash
cd /home/devmahnx/Dev/alphaforge
npm run dev
```

**Expected Output:**
```
▲ Next.js 14.x.x
- Ready in 1.234s
- Listening on http://localhost:3000
```

### 5.2 Verify Frontend Loads

Open browser: http://localhost:3000

**Expected:**
- ✅ Page loads without errors
- ✅ Dashboard displays
- ✅ No console errors (F12 → Console)
- ✅ Dark mode enabled
- ✅ Responsive on mobile view

### 5.3 Test Frontend API Calls

Open browser console (F12) and check:

```javascript
// This should work once backend is running
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)
```

**Expected:** `{status: "ok", ...}`

### 5.4 Check API Layer Wiring

```bash
# Verify API base URL is set correctly
grep -r "NEXT_PUBLIC_API_URL" src/
grep -r "process.env.NEXT_PUBLIC_API_URL" src/lib/api.ts
```

**Expected:** Should see references to `process.env.NEXT_PUBLIC_API_URL`

---

## 6. Integration Testing (Full Stack) ✅ Status: Ready

### 6.1 Test Complete User Flow Locally

**Setup:**
- Backend running on `http://localhost:8000` ✅
- Frontend running on `http://localhost:3000` ✅
- Database initialized in Supabase ✅

**Test Scenario:**

1. **Register as new user**
   - Go to http://localhost:3000
   - Click "Get Started" or "Sign Up"
   - Register with test email
   - Expected: User created, dashboard loads

2. **View Signals**
   - Dashboard should show signals
   - Backend should call `/api/frontend/signals/*` endpoints
   - Expected: Signals displayed

3. **View Market Data**
   - Navigate to Market Intelligence page
   - Should show funding rates, liquidations, sentiment
   - Expected: Real market data displayed

4. **View Portfolio**
   - Navigate to Portfolio page
   - Should show portfolio summary
   - Expected: Portfolio loaded (empty on new user is OK)

5. **Check Console for Errors**
   - Open browser console (F12)
   - Should be no red errors
   - Some network 404s are OK (for optional data)

### 6.2 Monitor Logs

**Backend Logs:**
```bash
# In backend terminal, watch logs
tail -f backend/logs/alphaforge.log
```

**Expected:** 
- No ERROR lines
- Some INFO lines as requests come in

**Frontend Errors:**
```bash
# In browser console (F12)
# Should see logs of API calls succeeding
```

---

## 7. Performance Validation ✅ Status: Ready

### 7.1 API Response Time Targets

Use your browser Network tab (F12 → Network) or:

```bash
# Test API latency
curl -w "\nTime Total: %{time_total}s\n" http://localhost:8000/health
```

**Target:**
- Health/Status: <100ms
- Market data: <500ms
- User profile: <200ms
- Portfolio: <500ms

**If Slow:**
- Check database query performance
- Add indices to frequently queried columns
- Enable Redis caching (Phase 3)

### 7.2 Frontend Load Time

Open Lighthouse (F12 → Lighthouse):

**Target Scores:**
- Performance: >80
- Accessibility: >90
- Best Practices: >85

**If Low:**
- Image optimization
- Code splitting
- CSS purging
- Remove unused dependencies

---

## 8. Security Validation ⚠️ Status: Critical

### 8.1 Verify No Secrets in Code

```bash
# Check for exposed credentials
cd /home/devmahnx/Dev/alphaforge
grep -r "SUPABASE_SERVICE_KEY" src/
grep -r "DATABASE_URL" src/
grep -r "ALPHA_VANTAGE" src/

# Should return NOTHING (all should be in .env or backend only)
```

**Expected:** No matches in `src/` folder

### 8.2 CORS Configuration

Backend should only accept requests from Vercel domain in production:

```python
# backend/main.py should have
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*")
# In production, this should NOT be "*"
```

### 8.3 Environment Variable Secrets

```bash
# Verify .env is in .gitignore
cat .gitignore | grep -i "\.env"

# Should show: .env
```

**Expected:** `.env` is NOT committed to Git ✅

### 8.4 HTTPS Target

- Frontend: Vercel (automatically enforces HTTPS) ✅
- Backend: Render/Railway (can enforce HTTPS) — set during deploy
- Database: Supabase (automatically enforced) ✅

---

## 9. Database Backup & Recovery ⚠️ Pre-Deployment

### 9.1 Enable Supabase Backups

Supabase automatically backs up daily (free tier). For Peace of Mind:

1. Go to Supabase Dashboard
2. Project Settings → Backups
3. Verify backups are enabled

### 9.2 Test Data Export

```bash
# Export current schema (for safety)
pg_dump postgresql://user:password@host/db > backup_schema.sql
```

---

## 10. Deployment Readiness Checklist

### 10.1 Pre-Flight Checks

- [ ] Database initialized (step 2)
- [ ] Backend tests passing (step 4)
- [ ] Backend health endpoint responds ✅
- [ ] Frontend loads without errors ✅
- [ ] Integration tests pass (step 6)
- [ ] No secrets exposed (step 8)
- [ ] CORS configured for production
- [ ] All environment variables set
- [ ] API response times acceptable (step 7)

### 10.2 Deployment Steps (Your Responsibility)

You'll handle these in deployment phase:

1. **Backend Deployment (Render/Railway)**
   ```
   - Push backend/ to GitHub
   - Connect to Render.com or Railway.app
   - Set environment variables
   - Deploy and get public URL
   ```

2. **Frontend Deployment (Vercel)**
   ```
   - Set NEXT_PUBLIC_API_URL = (backend URL)
   - Deploy
   - Verify health endpoint works
   ```

3. **Database (Supabase)**
   ```
   - Migrations already run
   - RLS policies already enabled
   - Just verify accessibility
   ```

---

## 11. Post-Deployment Validation

After you deploy to production:

### 11.1 Smoke Tests

```bash
# Test production endpoints
curl https://your-backend-url/health
curl https://your-frontend-url/health  # if health endpoint exposed
```

### 11.2 Monitor Logs

- Backend logs: Check for errors
- Frontend errors: Browser console monitoring
- Database: Check slow queries

### 11.3 User Acceptance Testing (UAT)

- [ ] Register new user
- [ ] View signals
- [ ] Execute paper trade
- [ ] Check portfolio
- [ ] Mobile responsiveness

---

## 12. Troubleshooting

### API Connection Errors

**Problem:** Frontend can't reach backend
```
TypeError: Failed to fetch
CORS error in console
```

**Solution:**
1. Verify backend is running
2. Check NEXT_PUBLIC_API_URL is set
3. Verify CORS is enabled in backend
4. Check network tab for actual error

### Database Connection Errors

**Problem:** Backend crashes on startup
```
ERROR: could not connect to database
```

**Solution:**
1. Verify DATABASE_URL in `.env`
2. Check Supabase credentials
3. Run migrations: `python scripts/init_supabase_db.py`
4. Verify Supabase project is active

### Tests Failing

**Problem:** E2E tests fail
```
AssertionError: 404 Client Error
```

**Solution:**
1. Ensure backend is running
2. Verify database is initialized
3. Check API endpoints exist
4. Look at response body for error details

---

## 13. Success Criteria

**MVP Phase 1 is deployment-ready when:**

✅ All pre-flight checks pass
✅ Backend integration tests: 100% green
✅ Frontend loads without errors
✅ API response times < 500ms (p95)
✅ No exposed secrets
✅ Database schema fully initialized
✅ All core user flows testable

---

## Next Steps

**Once all checks pass:**

1. ✅ You handle backend & frontend deployment
2. ✅ Verify production endpoints respond
3. ✅ Launch MVP to beta testers
4. ✅ Collect feedback for Phase 2

---

**Last Updated:** March 17, 2026
**Responsibility:** Engineering Team (Backend/Frontend/DevOps)
**Status:** Ready for Deployment Review
