# AlphaForge Beta Launch Plan

**Phase:** Closed Beta  
**Target Launch:** 2 weeks after legal sign-off  
**Duration:** 4 weeks  
**Users:** 100 selected traders  

---

## Goals

1. **Validate enforcement gates work end-to-end**
2. **Confirm paper trading gate delays are acceptable**
3. **Test Stripe billing integration**
4. **Monitor system stability under load (100 users)**
5. **Collect user feedback on UX/signal quality**
6. **Prepare legal/compliance team for GA**

---

## User Selection Criteria

### Tier 1: Internal (10 users)
- AlphaForge team members
- Advisors and investors
- Purpose: Deep testing, feedback on edge cases
- Access: Unlimited, all features

### Tier 2: Professional Traders (40 users)
- Invitation-only from community
- Criteria: >2 years trading experience, >$50k account
- Purpose: Signal quality feedback, risk edge cases
- Screening: Manual review by compliance

### Tier 3: Retail Testers (50 users)
- Waitlist signup → random lottery
- Criteria: 18+, KYC approval
- Purpose: UX feedback, onboarding flow
- Screening: Automated KYC check

---

## Week 1: Onboarding & Kickoff

### Day 1-2: Compliance Review
```
✅ All beta users complete KYC/AML
✅ Stripe sandbox subscriptions activated
✅ Paper trading gate start date recorded
✅ Audit trail initialization verified
```

### Day 3-5: Technical Kickoff
```
✅ Beta users download trading signals
✅ Demo paper trading account creation
✅ Onfido KYC webhook testing
✅ Stripe subscription lifecycle testing (trial → active → cancel)
```

### Day 6-7: Monitoring Setup
```
✅ Dashboard: Real-time user metrics
   - Active users
   - Paper trading submissions
   - Live trade attempts (should be 0 in week 1)
   - Error rates by gate
   - KYC approval latency

✅ Alerts configured:
   - System latency > 5s
   - Trade execution failures
   - KYC webhook timeouts
   - Audit trail corruption
```

---

## Week 2: Paper Trading Validation

### Objectives
1. Confirm 4-week paper trading gate working
2. Collect signal quality metrics
3. Monitor paper trading engine performance

### Key Metrics to Track

```
PAPER TRADING GATE:
- Submissions: # of signals submitted
- Gate blocks: # rejected (too early)
- Accepted: # passed gate checks
- Duration compliance: All ≥28 days enforced?
- Sharpe calc: Comparing backtest vs live

SIGNAL QUALITY:
- Win rate: % profitable signals
- Avg profit per signal: $ or %
- Avg loss per signal: $ or %
- Largest DD: Max drawdown on paper
- Sortino ratio: Risk-adjusted return

SYSTEM PERFORMANCE:
- Gate check latency: P95, P99
- Signal generation latency: Time to generate
- Database query times: Paper trade lookups
- Memory usage: Peak and average
```

### Daily Standup
- Review overnight metrics
- Identify paper trading anomalies
- Check audit trail integrity
- Validate no hard rejections from bugs

### Gate Monitoring
```
GATE 1 - KYC:
□ All 100 users approve KYC within 24h?
□ Any OFAC/PEP matches? (expect 0)
□ Onfido webhook latency < 5s?

GATE 2 - Subscription:
□ Stripe webhooks firing correctly?
□ Trial period (7 days) working?
□ Cancellation flow working?

GATE 3 - Compliance:
□ All users acknowledge 7 disclaimers?
□ Age gate enforced?
□ Disclaimer tracking in audit trail?

GATE 4 - Risk:
□ Paper trades validate position size?
□ No trades >2% of portfolio?
□ Leverage limits respected?
□ Stop loss required working?

GATE 5 - Paper Trading:
□ 4-week gate blocking premature signals?
□ Sharpe ratio calculation correct?
□ 28+ days enforced?

GATE 6 - Execution:
□ Idempotency keys preventing dupes?
□ Order confirmation within 5s?
□ Retry logic working on failures?
```

---

## Week 3: Live Trading (Controlled)

### Unlock Conditions
```
✅ All gates passing 100% of the time
✅ Paper trading engine stable (0 bugs)
✅ Audit trail verified hash-chain
✅ Legal approval received
✅ Insurance policy bound
```

### Phased Live Rollout

**Phase A: Tier 1 (Internal, 10 users)**
- Day 1: Enable live trading for internal team
- Monitor: Every trade, every gate, every audit log entry
- No restrictions on position size (for testing)
- On-call team standing by

**Phase B: Tier 2 (Professional, 40 users)**
- Day 2: Enable for professional traders
- Monitor: Trade success rate, gate rejections
- Full position size limits (2%, 5x leverage)
- Daily compliance review

**Phase C: Tier 3 (Retail, 50 users)**
- Day 3: Enable for retail testers
- Monitor: Signal quality, user experience
- Position size caps at 1% (extra safety)
- Support team standing by

### Live Trading Checklist
```
BEFORE EACH PHASE:
[ ] Enforcement gate fully tested
[ ] Execution service tested with real exchange (testnet)
[ ] Audit trail verified for correctness
[ ] Compliance review complete
[ ] On-call team briefing

DURING EACH PHASE:
[ ] Monitor error rates (target: <0.1%)
[ ] Track gate rejections (expected: 5-10%)
[ ] Verify audit trail entries (every trade logged)
[ ] Confirm no duplicate orders (idempotency working)
[ ] Check slippage vs expectation (±0.1%)

AFTER EACH PHASE:
[ ] Post-mortem on any issues
[ ] Collect trader feedback
[ ] Update runbooks based on learnings
[ ] Deploy fixes if needed (before next phase)
```

---

## Week 4: Scale & Final Validation

### Load Testing
```
TARGET: 100 concurrent users
- 50 paper trading
- 30 live trading
- 20 monitoring/idle

TEST DURATION: 8 hours peak
```

### Performance Targets
| Metric | Target | Actual | Status |
|---|---|---|---|
| Enforcement gate latency (P95) | <100ms | ? | ✅/❌ |
| Signal generation latency (P99) | <2s | ? | ✅/❌ |
| Order confirmation (P95) | <5s | ? | ✅/❌ |
| KYC check latency | <100ms | ? | ✅/❌ |
| Database query latency | <50ms | ? | ✅/❌ |
| Audit trail write latency | <10ms | ? | ✅/❌ |
| System uptime | >99.9% | ? | ✅/❌ |

### Monitoring Dashboard (Public for Beta Users)
```
REAL-TIME METRICS (updated every 5s):
- Active users right now
- Live trades this hour
- Paper trades this hour
- Average signal confidence
- System health indicator (🟢/🟡/🔴)
- Current latency (P95)

HISTORICAL (7-day rolling):
- Total users
- Total live trades
- Total paper trades
- Win rate
- Avg profit per signal
- System uptime %
```

### Final Validation Checklist
```
ENFORCEMENT:
[ ] All 6 gates working correctly
[ ] No gate bypasses discovered
[ ] Risk limits never exceeded
[ ] Paper trading gate enforced
[ ] KYC approval required

COMPLIANCE:
[ ] Audit trail immutable (hash verification)
[ ] No unauthorized trades
[ ] All trades logged
[ ] SAR filing triggered correctly (if needed)
[ ] User disclaimers acknowledged

OPERATIONS:
[ ] No data corruption
[ ] No duplicate orders
[ ] No lost trades
[ ] No system crashes
[ ] Error rate <0.1%

PERFORMANCE:
[ ] All latency targets met
[ ] Throughput targets met (500 sig/s)
[ ] No memory leaks
[ ] Database healthy
[ ] Redis stable
```

---

## Feedback Collection

### Daily User Survey
```
Rate your experience (1-5):
1. Signal quality 🟢/🟡/🔴
2. User interface 🟢/🟡/🔴
3. Onboarding process 🟢/🟡/🔴
4. Speed/performance 🟢/🟡/🔴

Would you recommend? Yes/No/Maybe

What's one thing we could improve?
[Text response]
```

### Weekly Deep Dives
- 1-on-1 calls with Tier 1 & 2 users
- Focus: Signal quality, risk rules, compliance understanding
- Collect: Feature requests, bug reports, edge cases

### End of Beta Survey
```
Overall satisfaction: 1-10 scale
- Signal profitability
- UX/interface
- Paper trading experience
- Risk management
- Support quality

Would you continue in GA? Yes/No

Feature requests for GA:
1. [User response]
2. [User response]
3. [User response]
```

---

## Issues Management

### Bug Triage

**Critical (P0):**
- Gate bypass or enforcement failure
- Data corruption in audit trail
- Unauthorized trade execution
- System crash
- **Action:** Immediate rollback, fix, retest

**High (P1):**
- Incorrect gate rejection
- Latency > target
- Stripe billing failure
- KYC webhook timeout
- **Action:** Fix within 24h, notify users

**Medium (P2):**
- UX confusing (lots of user feedback)
- Signal generation accuracy question
- Calculation discrepancy
- **Action:** Fix before GA

**Low (P3):**
- UI polish issues
- Documentation clarification
- Analytics improvements
- **Action:** After beta, before GA

### Issue Log Template
```
ISSUE: [Title]
SEVERITY: P0/P1/P2/P3
REPORTED: [Date, User, Evidence]
IMPACT: # of users, # of trades affected
ROOT CAUSE: [Technical analysis]
FIX: [Code change / Workaround]
TESTING: [How verified before deploy]
DEPLOY: [Date/time rolled out]
POSTMORTEM: [Why did this slip through?]
```

---

## Go/No-Go Decision Criteria

### Gate 1: Day 7 (End of Week 1)
```
MUST HAVE:
✅ All 100 users KYC approved
✅ Paper trading engine stable
✅ Stripe billing working
✅ Audit trail verified
✅ No critical bugs

DECISION:
❌ PAUSE if audit trail corrupted
❌ PAUSE if >1 critical bug
❌ PAUSE if Stripe integration broken
✅ GO if all above met → proceed to Week 2
```

### Gate 2: Day 14 (End of Week 2)
```
MUST HAVE:
✅ Paper trading gate enforcing 4 weeks
✅ KYC gate blocking appropriately
✅ Compliance disclaimer acknowledged
✅ Risk limits never exceeded
✅ System latency on target

DECISION:
❌ PAUSE if enforcement gates failing
❌ PAUSE if latency > 1s average
❌ PAUSE if >1% error rate
✅ GO if all above met → unlock live trading
```

### Gate 3: Day 21 (End of Week 3)
```
MUST HAVE:
✅ Live trading stable (Tier 1 & 2)
✅ No unauthorized trades
✅ Audit trail correct
✅ KYC/Subscription working
✅ No gate bypasses found

DECISION:
❌ PAUSE if live trading gate broken
❌ PAUSE if audit corruption found
❌ PAUSE if trades executing without KYC
✅ GO if all above met → expand Tier 3
```

### Gate 4: Day 28 (End of Week 4)
```
MUST HAVE:
✅ 100k concurrent load tested
✅ System uptime >99.9%
✅ All performance targets met
✅ User satisfaction >4/5
✅ Legal/compliance sign-off
✅ Insurance policy active

DECISION:
✅ GA READY - Proceed to General Availability launch
❌ GA DELAYED - Fix issues + 1 week re-test
```

---

## Runbooks (On-Call Team)

### Alert: Gate Enforcement Failing
```
1. Page on-call engineer
2. Check which gate is failing (KYC/Risk/etc)
3. Review recent deployments
4. Isolate failing service (check DB, Redis)
5. Rollback if deployed in last 1h
6. Fix and re-deploy
7. Verify gate working with test user
8. Post to #beta-incident channel
```

### Alert: Audit Trail Corruption
```
1. IMMEDIATE: Stop all trading
2. Page compliance officer + engineer
3. Run hash verification script
4. Determine corruption scope
5. If isolated: Repair + verify
6. If widespread: Restore from backup
7. Notify users affected
8. Legal review + SAR filing if needed
```

### Alert: System Latency > 5s
```
1. Check database query times
2. Check Redis memory/connections
3. Check ML signal generation load
4. If DB slow: Analyze slow query log
5. If Redis full: Check eviction policy
6. If ML slow: Reduce batch size
7. Scale up if needed
8. Monitor for 30 min, verify recovered
```

---

## Success Metrics (Definition of Done)

```
FUNCTIONAL:
✅ All 6 enforcement gates working
✅ Paper trading 4-week gate enforced
✅ 0 unauthorized trades
✅ Audit trail immutable

PERFORMANCE:
✅ Latency P95 < 100ms (enforcement)
✅ Throughput 500 signals/sec (sustained)
✅ Uptime > 99.9% (56+ min/month allowed downtime)
✅ Error rate < 0.1% (< 1 error per 1000 ops)

COMPLIANCE:
✅ All users KYC approved
✅ 7 disclaimers acknowledged by all
✅ Subscription enforced for live trades
✅ Age gate validated (18+)

USER SATISFACTION:
✅ Net Promoter Score > 50
✅ Overall rating > 4.0/5.0
✅ Signal quality > 55% win rate
✅ Willingness to upgrade to GA > 80%

LEGAL/OPERATIONS:
✅ FCA notification received
✅ Insurance policy bound
✅ No regulatory complaints
✅ Legal counsel sign-off
```

---

## Post-Beta Tasks (Before GA)

### Week 1 (Post-Beta)
- [ ] Analyze all feedback data
- [ ] Document lessons learned
- [ ] Update enforcement gates based on feedback
- [ ] Scale infrastructure for GA

### Week 2
- [ ] Deploy GA builds
- [ ] Final security audit
- [ ] Compliance final review
- [ ] Marketing launch plan

### Week 3
- [ ] Production deployment preparation
- [ ] Monitoring/alerting final setup
- [ ] Support team training
- [ ] User documentation finalization

### Week 4
- [ ] Launch General Availability
- [ ] Monitor first 24 hours closely
- [ ] Scale as needed
- [ ] Celebrate! 🎉

---

## Communication Plan

### Internal (AlphaForge Team)
- **Daily:** Slack #beta-operations with metrics
- **Weekly:** Team sync on blockers/feedback
- **Post-beta:** Retrospective + lessons learned

### External (Beta Users)
- **Weekly:** Email with highlights/updates
- **Post-beta:** Thank you + feedback summary
- **On issues:** Direct communication within 4h

### Public
- **Day 1:** Beta launch announcement
- **Weekly:** Progress blog posts
- **End of beta:** Results + GA launch date announcement

