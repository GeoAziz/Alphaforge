# Quick Start: Optional Production Enhancements

Complete setup guide for adding Firebase Auth, WebSocket, Sentry, and PostHog to AlphaForge.

---

## ⚡ Quick Summary

| Feature | Purpose | Effort | Priority |
|---------|---------|--------|----------|
| **Firebase Auth** | Real user authentication | 30 min | High |
| **WebSocket** | Real-time market/signal updates | 45 min | Medium |
| **Sentry** | Error tracking & monitoring | 20 min | High |
| **PostHog** | User analytics | 25 min | Medium |

---

## 1️⃣ Firebase Authentication (30 minutes)

### A. Set Up Firebase

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Create/select project
3. Enable **Authentication** → **Email/Password** + **Google OAuth**
4. Go to **Project Settings** → **Your Apps** → **Web**
5. Copy Firebase config

### B. Update Environment

Add to `.env.local`:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=your_value
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_value
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_value
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_value
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_value
NEXT_PUBLIC_FIREBASE_APP_ID=your_value

# Backend
FIREBASE_CREDENTIALS_JSON='{"type":"service_account",...}'
```

Download service account JSON from Firebase → Project Settings → Service Accounts → Generate new private key

### C. Backend Setup

```bash
pip install firebase-admin
```

Add to `backend/main.py`:

```python
from firebase_admin import verify_firebase_token

@app.get("/api/user/profile")
async def get_user_profile(user_id: str = Depends(verify_firebase_token)):
    # user_id is now verified from Firebase
    return await user_service.get_user_profile(user_id)
```

### D. Frontend Already Ready

Firebase provider is already in `src/firebase/provider.ts` - just activate it in `layout.tsx`:

```typescript
import { FirebaseClientProvider } from '@/firebase/provider';
```

**Status**: ✅ Firebase in layout already, just add credentials

---

## 2️⃣ WebSocket Real-Time Updates (45 minutes)

### A. Install Backend Dependencies

```bash
pip install websockets
```

### B. Add WebSocket Manager

Already created: `backend/websocket_manager.py`

### C. Add WebSocket Endpoints to Backend

In `backend/main.py`, after CORS setup:

```python
from websocket_manager import get_ws_manager
import asyncio

@app.websocket("/ws/market-updates")
async def websocket_market_updates(websocket: WebSocket):
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket, "market-updates")
    
    try:
        while True:
            tickers = await market_data_service.fetch_market_tickers(['BTC', 'ETH'])
            await ws_manager.broadcast_to_group("market-updates", {
                "type": "market_update",
                "data": tickers,
                "timestamp": datetime.utcnow().isoformat()
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "market-updates")

@app.websocket("/ws/signals")
async def websocket_signals(websocket: WebSocket):
    ws_manager = get_ws_manager()
    await ws_manager.connect(websocket, "signals")
    
    try:
        while True:
            signals = await signal_processor.get_live_signals()
            if signals:
                await ws_manager.broadcast_to_group("signals", {
                    "type": "signal_update",
                    "data": signals,
                    "timestamp": datetime.utcnow().isoformat()
                })
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, "signals")
```

### D. Frontend Hook Already Created

Use `src/hooks/use-websocket.ts` in components:

```typescript
import { useWebSocket } from '@/hooks/use-websocket';

export function Dashboard() {
  const { data: market, isConnected } = useWebSocket('/ws/market-updates');
  const { data: signals } = useWebSocket('/ws/signals');

  return (
    <div>
      {isConnected && <div className="bg-green-500">Live</div>}
      {market && <pre>{JSON.stringify(market)}</pre>}
    </div>
  );
}
```

**Status**: ✅ Hook created, just add endpoints to backend

---

## 3️⃣ Sentry Error Tracking (20 minutes)

### A. Create Sentry Project

1. Go to [sentry.io](https://sentry.io)
2. Create → New Project → Next.js
3. Copy **DSN**
4. Go to Settings → Auth Tokens → Generate token
5. Copy **Auth Token**

### B. Set Environment Variables

Add to `.env.local`:

```env
NEXT_PUBLIC_SENTRY_DSN=https://key@org.ingest.sentry.io/id
NEXT_PUBLIC_SENTRY_ENVIRONMENT=development
SENTRY_ORG=your-org
SENTRY_PROJECT=your-project
SENTRY_AUTH_TOKEN=your_token
```

### C. Install Frontend Package

```bash
npm install --save-exact @sentry/nextjs
```

### D. Add Provider to Layout

In `src/app/layout.tsx`:

```typescript
import { SentryProvider, ErrorBoundary } from '@/providers/sentry-provider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <SentryProvider>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </SentryProvider>
      </body>
    </html>
  );
}
```

### E. Backend Sentry

```bash
pip install sentry-sdk
```

In `backend/main.py`:

```python
from sentry_config import init_sentry

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_sentry()
    yield
```

Add to `.env`:

```env
SENTRY_DSN=https://key@org.ingest.sentry.io/id
SENTRY_ENVIRONMENT=development
```

**Status**: ✅ Provider created, just install package and add to layout

---

## 4️⃣ PostHog Analytics (25 minutes)

### A. Create PostHog Project

1. Go to [PostHog.com](https://posthog.com)
2. Sign up → Create project
3. Copy **API Key** and **Host**

### B. Set Environment Variables

Add to `.env.local`:

```env
NEXT_PUBLIC_POSTHOG_KEY=your_key
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
POSTHOG_API_KEY=your_key
POSTHOG_HOST=https://us.i.posthog.com
```

### C. Install Frontend Package

```bash
npm install posthog-js
```

### D. Add Provider to Layout

In `src/app/layout.tsx`:

```typescript
import { PostHogProvider } from '@/providers/posthog-provider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <PostHogProvider>
          {children}
        </PostHogProvider>
      </body>
    </html>
  );
}
```

### E. Track Events in Components

```typescript
import { analytics } from '@/providers/posthog-provider';

// Track page views (automatic)
// Track trades
analytics.tradeExecuted({
  asset: 'BTC',
  quantity: 1.5,
  direction: 'buy'
});

// Track strategies
analytics.strategyInteraction('subscribed', 'strategy-123');

// Track signals
analytics.signalInteraction('acted_on', 'signal-456');
```

**Status**: ✅ Provider created, just install package and add to layout

---

## 📋 Complete Setup Checklist

### Backend
- [ ] Install: `pip install sentry-sdk websockets posthog firebase-admin`
- [ ] Update `requirements.txt`: `pip freeze > requirements.txt`
- [ ] Add to `backend/main.py`:
  - [ ] WebSocket endpoints (copy from above)
  - [ ] Sentry init in lifespan
  - [ ] Firebase token verification on protected endpoints
  - [ ] PostHog tracking calls
- [ ] Add `.env` variables for Sentry and PostHog

### Frontend
- [ ] Install: `npm install --save-exact @sentry/nextjs posthog-js`
- [ ] Update `src/app/layout.tsx`:
  - [ ] Add `SentryProvider`
  - [ ] Add `PostHogProvider`
  - [ ] Add Firebase config variables to `.env.local`
- [ ] Create `.env.local` with all API keys:
  - [ ] Firebase config (6 variables)
  - [ ] Sentry DSN + credentials
  - [ ] PostHog key + host
  - [ ] Confirm API_URL points to correct backend

### Services
- [ ] ✅ Firebase: Created service account and got credentials
- [ ] ✅ Sentry: Created project, got DSN, generated auth token
- [ ] ✅ PostHog: Created project, got API key

---

## 🧪 Quick Tests

### Test Firebase Auth
```bash
npm run dev
# Login with email/Google → console should show Firebase user
```

### Test WebSocket
```bash
# Backend: python -m uvicorn main:app --reload
# Browse to http://localhost:3000
# Open DevTools → Network → filter "WS"
# Should see /ws/market-updates and /ws/signals connections
```

### Test Sentry
```typescript
// In browser console
import { errorTracking } from '@/providers/sentry-provider';
errorTracking.captureMessage('Test', 'info');
// Check Sentry dashboard → should see event
```

### Test PostHog
```typescript
// In browser console
import { analytics } from '@/providers/posthog-provider';
analytics.action('test_event');
// Check PostHog dashboard → should see user event
```

---

## 🚀 Next Steps After Setup

1. **Monitor Production**: Watch Sentry dashboard for errors
2. **Track Metrics**: Set up PostHog dashboards for key metrics
3. **Real-Time Experience**: Test WebSocket with actual market data
4. **User Trust**: Show Firebase verification to users
5. **Performance**: Monitor Sentry traces for slow endpoints

---

## ❓ Troubleshooting

### Firebase Auth Not Working
- Check credentials in `FIREBASE_CREDENTIALS_JSON`
- Verify email domain is allowed in Firebase console
- Check backend logs for token verification errors

### WebSocket Connection Fails
- Ensure backend WebSocket endpoint is exposed on ngrok
- Check browser console for connection errors
- Verify API_URL environment variable points to correct backend

### Sentry Not Capturing Errors
- Verify DSN is correct in environment
- Check browser console for Sentry initialization messages
- Ensure errors are being thrown (not just logged)

### PostHog Not Tracking Events
- Verify API key is in `NEXT_PUBLIC_POSTHOG_KEY`
- Check PostHog project is active and accepting events
- Confirm `identify()` is called with user ID

---

All files are already created and ready to use. Just follow the checklist above!

See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for detailed integration instructions.
See [OPTIONAL_SETUP.md](./OPTIONAL_SETUP.md) for full feature documentation.
