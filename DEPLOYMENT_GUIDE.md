# AlphaForge MVP Phase 1 - Deployment Guide

This guide walks through **your responsibility**: deploying the backend and frontend to production.

**Timeline: 1-2 hours for experienced ops engineers**

---

## Overview

You'll deploy three components:

| Component | Platform | Status | Your Action |
|-----------|----------|--------|-------------|
| **Backend** | Render.com or Railway.app | ✅ Ready | Deploy FastAPI app |
| **Frontend** | Vercel | ✅ Ready | Deploy Next.js app |
| **Database** | Supabase | ⏳ Schema Ready | Just verify connectivity |

All infrastructure code is ready. You just need to push to GitHub and connect services.

---

## Prerequisites

- GitHub account with push access
- Render.com or Railway.app account
- Vercel account (or let me handle frontend after you deploy backend)
- Already run: `python scripts/init_supabase_db.py` (database initialized locally)

---

## Part 1: Backend Deployment (Render.com - Recommended)

### Step 1.1: Create GitHub Repository for Backend

```bash
# Create new private repo on GitHub
# Name: alphaforge-backend
# Clone locally
cd /tmp
git clone https://github.com/YOUR_ORG/alphaforge-backend.git
cd alphaforge-backend

# Copy backend files
cp -r /home/devmahnx/Dev/alphaforge/backend/* .

# Commit
git add .
git commit -m "Initial commit: AlphaForge backend Phase 1 MVP"
git push origin main
```

### Step 1.2: Set Up Render.com

1. Go to https://render.com
2. Sign in/Sign up
3. Click "New +" → "Web Service"
4. Connect GitHub
5. Select `alphaforge-backend` repository
6. Configure:

**Settings:**
- **Environment:** Python 3.10
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Environment Variables** (Copy from your local `.env`):
```
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=sb_secret_...
SUPABASE_ANON_KEY=eyJ...
ALPHA_VANTAGE_API_KEY=...
POLYGON_IO_API_KEY=...
TRADINGVIEW_WEBHOOK_SECRET=...
API_ENV=production
CORS_ALLOW_ORIGINS=https://your-frontend-domain.vercel.app
```

7. Click "Create Web Service"
8. **Wait for build** (~3-5 minutes)

**Expected Result:**
```
✅ Build succeeded
✅ Deployed at: https://alphaforge-backend-XXXXXX.onrender.com
```

### Step 1.3: Verify Backend is Running

```bash
# Test health endpoint
curl https://alphaforge-backend-XXXXXX.onrender.com/health

# Expected response:
# {"status":"ok","timestamp":"...","version":"1.0.0"}
```

### Step 1.4: Monitor Live Backend

```bash
# Test user registration (the integration test)
curl -X POST https://alphaforge-backend-XXXXXX.onrender.com/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "prod_test_'$(date +%s)'@alphaforge.local",
    "display_name": "Production Test",
    "plan": "basic",
    "risk_tolerance": "moderate"
  }'

# Should return 200 with user created
```

**Note:** First request may be slow (Render spins up from sleep). Subsequent requests will be fast.

### Step 1.5: Enable Auto-Deploy (Optional)

In Render Dashboard → Service Settings:
- Enable "Auto-Deploy on Push"
- Now any git push to `main` will auto-deploy

---

## Part 2: Frontend Deployment (Vercel)

### Step 2.1: Prepare Frontend Repository

```bash
# Create new GitHub repo for frontend
# Name: alphaforge-frontend

cd /tmp
git clone https://github.com/YOUR_ORG/alphaforge-frontend.git
cd alphaforge-frontend

# Copy frontend files
cp -r /home/devmahnx/Dev/alphaforge/src .
cp -r /home/devmahnx/Dev/alphaforge/public .
cp /home/devmahnx/Dev/alphaforge/package.json .
cp /home/devmahnx/Dev/alphaforge/tsconfig.json .
cp /home/devmahnx/Dev/alphaforge/next.config.ts .
cp /home/devmahnx/Dev/alphaforge/tailwind.config.ts .
cp /home/devmahnx/Dev/alphaforge/postcss.config.mjs .

# Commit
git add .
git commit -m "Initial commit: AlphaForge frontend Phase 1 MVP"
git push origin main
```

### Step 2.2: Set Up Vercel

1. Go to https://vercel.com
2. Sign in/Sign up
3. Click "Add New..." → "Project"
4. Import `alphaforge-frontend` from GitHub
5. Configure:

**Framework:** Next.js
**Build Command:** Keep default
**Install Command:** Keep default

**Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://alphaforge-backend-XXXXXX.onrender.com
NEXT_PUBLIC_FIREBASE_CONFIG_JSON={"apiKey":"...","projectId":"...",...}
```

6. Click "Deploy"
7. **Wait for build** (~2-3 minutes)

**Expected Result:**
```
✅ Build succeeded
✅ Deployed at: https://alphaforge-XXXXXX.vercel.app
```

### Step 2.3: Verify Frontend is Running

Open browser:
```
https://alphaforge-XXXXXX.vercel.app
```

**Expected:**
- ✅ Dashboard loads
- ✅ Dark mode enabled
- ✅ No console errors (F12)
- ✅ Responsive on mobile

### Step 2.4: Check API Connectivity

Open browser console (F12) and paste:
```javascript
fetch('https://alphaforge-backend-XXXXXX.onrender.com/health')
  .then(r => r.json())
  .then(d => console.log('✅ Backend connected:', d))
  .catch(e => console.error('❌ Backend error:', e))
```

**Expected:**
```
✅ Backend connected: {status: "ok", ...}
```

If error, check:
- [ ] Backend URL is correct
- [ ] CORS is enabled on backend
- [ ] Backend is actually running

---

## Part 3: Database Production Setup (Already Done Locally)

### Step 3.1: Run Migrations in Production

The database schema needs to be initialized in **production** Supabase:

```bash
# Connect to production Supabase
export DATABASE_URL="postgresql://postgres.YOUR_PROJECT_ID:YOUR_PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

cd /home/devmahnx/Dev/alphaforge/backend
python scripts/init_supabase_db.py
```

**Terminal Output Should Show:**
```
✅ Connected to PostgreSQL (production)
✅ Successfully executed X SQL statements
✅ All 18 core tables created
✅ Database initialization complete!
```

**Verify in Supabase Dashboard:**
1. Go to https://supabase.com
2. Select your project
3. SQL Editor
4. Run: `SELECT COUNT(*) FROM pg_tables WHERE schemaname='public'`
5. Should return: **18** (tables count)

### Step 3.2: Test Database from Production Backend

```bash
# In Render dashboard, check logs
# Should see: ✅ PostgreSQL connection successful

# Or test from terminal
curl https://alphaforge-backend-XXXXXX.onrender.com/ready

# Response:
# {"database":"connected",...}
```

---

## Part 4: Post-Deployment Validation

### Step 4.1: Run Integration Tests Against Production

```bash
cd /home/devmahnx/Dev/alphaforge/backend

# Point tests to production
export API_BASE_URL=https://alphaforge-backend-XXXXXX.onrender.com

# Run E2E tests
pytest tests/integration_e2e.py -v --tb=short

# Target: 100% pass rate
```

### Step 4.2: Smoke Test Full User Flow

1. Open https://alphaforge-XXXXXX.vercel.app
2. Register as new user (test email)
3. Complete onboarding flow
4. Navigate to Portfolio
5. Navigate to Market Intelligence
6. Check browser console for errors

### Step 4.3: Monitor Production Logs

**Backend (Render):**
- Render Dashboard → Service → Logs
- Should be clean, no ERROR lines

**Frontend (Vercel):**
- Vercel Dashboard → Project → Deployments
- Check for build errors or warnings

**Database:**
- Supabase Dashboard → SQL Editor
- Run: `SELECT COUNT(*) FROM users` (should grow as you register)

---

## Part 5: Scaling Considerations

### For Initial Launch (MVP):

**Backend Scaling:**
- Render free tier handles ~5-10 concurrent users
- Upgrade to "Pay-as-you-go" plan as you grow

**Frontend:**
- Vercel free tier unlimited
- No scaling needed initially

**Database:**
- Supabase free tier: 500MB storage, unlimited queries
- Should easily handle 100+ users initially

**When to Scale (Phase 3+):**
- Backend: Add Redis caching, replicate to multiple regions
- Frontend: Already globally distributed by Vercel
- Database: Add read replicas, implement connection pooling

---

## Part 6: Troubleshooting Deployment

### Frontend Doesn't Load

**Problem:** 404 or build error
```
Solution:
1. Check Vercel logs: Vercel Dashboard → Deployments
2. Verify NEXT_PUBLIC_API_URL is set correctly
3. Redeploy manually
```

### Backend Returns 503

**Problem:** Service unavailable
```
Solution:
1. Check Render logs: Render Dashboard → Logs
2. Verify DATABASE_URL and SUPABASE_* keys
3. Check Supabase is running: supabase.com dashboard
4. Restart service: Render Dashboard → Manual restart
```

### Requests Timeout

**Problem:** Requests exceed 30s
```
Solution:
1. Check database query performance
2. Enable Render slow query logs
3. Add indices to frequently queried columns
4. Consider Redis caching layer
```

### CORS Errors

**Problem:** Frontend gets blocked by CORS
```
Solution:
1. Verify CORS_ALLOW_ORIGINS in backend .env
2. Should be: https://your-frontend-domain.vercel.app
3. Redeploy backend after changing
```

---

## Part 7: Production Monitoring Setup

### Step 7.1: Enable Error Tracking (Optional)

**Sentry (Recommended):**
1. Go to https://sentry.io
2. Sign up
3. Create new projects (one for backend, one for frontend)
4. Get DSN keys
5. Add to environment variables
6. Now errors automatically reported

### Step 7.2: Monitor Uptime

**UptimeRobot (Recommended):**
1. Go to https://uptimerobot.com
2. Create account
3. Add monitor:
   - URL: `https://alphaforge-backend-XXXXXX.onrender.com/health`
   - Check interval: 5 minutes
4. Get email alerts if backend goes down

### Step 7.3: Analytics

**Frontend:**
1. Firebase Analytics (already set up)
2. Tracks user behavior

**Backend:**
1. Render provides basic metrics
2. Can send custom events to Mixpanel/Amplitude later (Phase 3)

---

## Deployment Checklist

- [ ] Backend repository created on GitHub
- [ ] Backend deployed to Render.com
- [ ] Backend health endpoint responds
- [ ] Frontend repository created on GitHub
- [ ] Frontend deployed to Vercel
- [ ] Frontend loads without errors
- [ ] Frontend can reach backend (test in console)
- [ ] Database migrations run
- [ ] Integration tests pass against production
- [ ] Full user flow tested (register → portfolio)
- [ ] Monitoring enabled (UptimeRobot for backend)
- [ ] Team notified of production URLs

---

## Production URLs After Deployment

Save these:

```
🔗 Backend API:    https://alphaforge-backend-XXXXXX.onrender.com
🔗 Frontend App:   https://alphaforge-XXXXXX.vercel.app
🔗 Database:       Supabase (https://supabase.com)
🔗 Logs:           Render Dashboard / Vercel Dashboard
🔗 Status:         UptimeRobot Dashboard
```

---

## Rollback Plan

If something breaks in production:

**Option 1: Quick Rollback (Git)**
```bash
git revert <bad-commit>
git push
# Changes auto-deploy (if enabled)
```

**Option 2: Revert to Previous Deployment**
- Render: Dashboard → Deployments → Select previous → Deploy
- Vercel: Dashboard → Deployments → Select previous → Redeploy

**Option 3: Manual Database Recovery**
```bash
# If database is corrupted
# Restore from Supabase backup (daily auto-backup is on)
# Supabase Dashboard → Backups → Restore from backup
```

---

## Next Steps After Launch

**Day 1-3: Beta Testing**
- Monitor logs for errors
- Collect user feedback
- Fix critical bugs
- Scale if needed

**Week 2: Phase 2 Planning**
- Analyze user behavior
- Plan backtesting engine
- Plan KYC verification flow
- Plan ML signal scoring

**Week 3+: Phase 2 Implementation** (See RoadMap.md for details)

---

## Support

**If Deployment Gets Stuck:**

1. Check Render logs first
2. Check Vercel build logs
3. Verify all environment variables are set
4. Restart services in Render/Vercel dashboard
5. If still stuck, check the integration tests locally

---

**Deployment Status: Ready for Your Action** ✅

Run through this guide step-by-step. You should have a live MVP running in production within 1-2 hours.

Total time from this moment to live MVP: **~2-4 hours**

---

**Last Updated:** March 17, 2026
**Prepared By:** Engineering Team
**Status:** ✅ All Code Ready - Awaiting Your Deployment
