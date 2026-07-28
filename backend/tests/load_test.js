import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';

// Custom metrics
const requestDuration = new Trend('request_duration');
const authFailure = new Counter('auth_failures');
const tradeErrors = new Counter('trade_errors');
const concurrentUsers = new Gauge('concurrent_users');

// Load test configuration
export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp-up to 100 users over 2 minutes
    { duration: '5m', target: 500 },   // Increase to 500 over 5 minutes
    { duration: '10m', target: 1000 }, // Peak at 1000 concurrent users
    { duration: '5m', target: 500 },   // Ramp-down to 500
    { duration: '2m', target: 0 },     // Ramp-down to 0
  ],
  thresholds: {
    'http_req_duration': ['p(99)<5000', 'p(95)<3000', 'p(90)<2000'],
    'http_req_failed': ['rate<0.1'],
    'auth_failures': ['rate<0.05'],
    'trade_errors': ['rate<0.02'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'test-token-' + Math.random().toString(36).substr(2);

// Test data
const testUsers = [
  { user_id: 'user-001', firebase_uid: 'uid-001' },
  { user_id: 'user-002', firebase_uid: 'uid-002' },
  { user_id: 'user-003', firebase_uid: 'uid-003' },
  { user_id: 'user-004', firebase_uid: 'uid-004' },
  { user_id: 'user-005', firebase_uid: 'uid-005' },
];

const assets = ['BTC', 'ETH', 'SOL', 'DOGE', 'ADA'];
const directions = ['LONG', 'SHORT'];

export default function() {
  const user = testUsers[Math.floor(Math.random() * testUsers.length)];
  const asset = assets[Math.floor(Math.random() * assets.length)];
  const direction = directions[Math.floor(Math.random() * directions.length)];

  concurrentUsers.add(1);

  group('User Authentication & Profile', () => {
    const authRes = http.get(`${BASE_URL}/api/frontend/user/${user.user_id}/profile`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    check(authRes, {
      'auth returns 200': (r) => r.status === 200,
      'auth response has user data': (r) => r.body.includes('user_id'),
    }) || authFailure.add(1);

    requestDuration.add(authRes.timings.duration);
    sleep(1);
  });

  group('Market Data Retrieval', () => {
    const marketsRes = http.get(`${BASE_URL}/api/frontend/market/tickers`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    check(marketsRes, {
      'market data returns 200': (r) => r.status === 200,
      'response time < 2s': (r) => r.timings.duration < 2000,
    });

    requestDuration.add(marketsRes.timings.duration);
    sleep(0.5);
  });

  group('Portfolio Operations', () => {
    const portfolioRes = http.get(`${BASE_URL}/api/frontend/portfolio/${user.user_id}/summary`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    check(portfolioRes, {
      'portfolio summary returns 200': (r) => r.status === 200,
      'portfolio has equity data': (r) => r.body.includes('total_equity'),
    });

    requestDuration.add(portfolioRes.timings.duration);
    sleep(0.5);
  });

  group('Trading Flow', () => {
    // Get signals
    const signalsRes = http.get(`${BASE_URL}/api/frontend/signals?limit=10`, {
      headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
    });

    check(signalsRes, {
      'signals endpoint returns 200': (r) => r.status === 200,
    });

    // Execute paper trade
    const tradePayload = JSON.stringify({
      user_id: user.user_id,
      signal_id: 'sig-' + Math.random().toString(36).substr(2, 9),
      asset: asset,
      direction: direction,
      entry_price: 50000 + Math.random() * 10000,
      quantity: Math.random() * 10,
      stop_loss: 45000,
      take_profit: 55000,
    });

    const tradeRes = http.post(`${BASE_URL}/api/signals/${asset}/execute`, tradePayload, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${AUTH_TOKEN}`,
      },
      params: { user_id: user.user_id },
    });

    check(tradeRes, {
      'trade execution returns success': (r) => r.status === 200 || r.status === 201,
      'trade has trade_id': (r) => r.body.includes('trade_id') || r.status !== 200,
    }) || tradeErrors.add(1);

    requestDuration.add(tradeRes.timings.duration);
    sleep(1);
  });

  group('Real-time Updates', () => {
    const priceUpdateRes = http.get(
      `${BASE_URL}/api/frontend/market/tickers?assets=${asset}`,
      {
        headers: { Authorization: `Bearer ${AUTH_TOKEN}` },
      }
    );

    check(priceUpdateRes, {
      'price update returns 200': (r) => r.status === 200,
    });

    requestDuration.add(priceUpdateRes.timings.duration);
    sleep(0.5);
  });

  group('Chat Integration', () => {
    const chatPayload = JSON.stringify({
      message: 'What is the current market sentiment for ' + asset + '?',
    });

    const chatRes = http.post(`${BASE_URL}/api/chat/message`, chatPayload, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${AUTH_TOKEN}`,
      },
      params: {
        user_id: user.user_id,
        message: 'market sentiment query',
      },
    });

    check(chatRes, {
      'chat returns 200': (r) => r.status === 200,
    });

    requestDuration.add(chatRes.timings.duration);
    sleep(1);
  });

  sleep(Math.random() * 3);
}

export function teardown() {
  console.log('Load test completed');
}
