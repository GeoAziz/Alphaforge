-- ============================================================================
-- ALPHAACADEMY EDUCATION LAYER
-- ============================================================================

-- ============================================================================
-- EDUCATION CONTENT
-- ============================================================================

CREATE TABLE IF NOT EXISTS education_content (
  content_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('patterns', 'strategies', 'risk_mgmt', 'quant_basics')),
  difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
  content TEXT NOT NULL,
  tags JSONB DEFAULT '[]'::jsonb,
  estimated_minutes INTEGER DEFAULT 5,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_education_content_category ON education_content(category);
CREATE INDEX IF NOT EXISTS idx_education_content_difficulty ON education_content(difficulty);

-- ============================================================================
-- SIGNAL BREAKDOWNS
-- ============================================================================

CREATE TABLE IF NOT EXISTS signal_breakdowns (
  signal_id UUID PRIMARY KEY,
  breakdown_summary TEXT NOT NULL,
  pattern_name TEXT,
  key_metrics JSONB DEFAULT '{}'::jsonb,
  generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- USER EDUCATION PROGRESS
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_education_progress (
  user_id UUID NOT NULL,
  content_id UUID NOT NULL,
  completed BOOLEAN DEFAULT FALSE,
  quiz_score NUMERIC(5,2),
  completed_at TIMESTAMP WITH TIME ZONE,
  PRIMARY KEY (user_id, content_id),
  FOREIGN KEY (content_id) REFERENCES education_content(content_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_edu_progress_user ON user_education_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_edu_progress_content ON user_education_progress(content_id);

-- ============================================================================
-- SEED DATA: 10+ Starter Content Pieces
-- ============================================================================

INSERT INTO education_content (title, category, difficulty, content, tags, estimated_minutes) VALUES

-- PATTERNS (3 guides)
('Momentum Divergence Detection', 'patterns', 'beginner',
'## Momentum Divergence

Momentum divergence occurs when the price of an asset moves in the opposite direction of a momentum indicator (like RSI or MACD).

### Bullish Divergence
- Price makes a **lower low** while the indicator makes a **higher low**
- Suggests weakening selling pressure
- Often precedes a price reversal upward

### Bearish Divergence
- Price makes a **higher high** while the indicator makes a **lower high**
- Suggests weakening buying pressure
- Often precedes a price reversal downward

### How to Identify
1. Look for price making new extremes (highs or lows)
2. Check RSI or MACD histogram for opposing movement
3. Confirm with volume (divergence on declining volume is stronger)
4. Wait for a candle close to confirm the reversal

### Common Mistakes
- Acting on divergence without waiting for confirmation
- Ignoring the broader trend (divergence in a strong trend may fail)
- Using divergence on very short timeframes (noise dominates)

### AlphaForge Integration
AlphaForge signals tagged with **momentum_divergence** are generated when RSI divergence is detected on multiple timeframes with volume confirmation.',
'["momentum", "divergence", "RSI", "MACD", "reversal", "technical analysis"]', 8),

('Breakout Pattern Recognition', 'patterns', 'beginner',
'## Breakout Patterns

A breakout occurs when price moves above a resistance level or below a support level with increased volume.

### Types of Breakouts
- **Horizontal Breakout**: Price breaks above/below a horizontal support/resistance level
- **Channel Breakout**: Price escapes a consolidation channel (ascending/descending)
- **Volatility Breakout**: Price breaks out of a Bollinger Band squeeze

### Key Characteristics
- Volume should spike 1.5-2x average on the breakout candle
- The breakout candle should close beyond the level (not just wick)
- Look for retest of the broken level as new support/resistance

### False Breakout Prevention
1. Wait for a candle close beyond the level
2. Check volume confirmation
3. Look for alignment across timeframes
4. Set alerts at key levels rather than chasing

### AlphaForge Integration
Signals tagged **breakout** trigger when price breaks key levels with volume confirmation across 1H and 4H charts.',
'["breakout", "support", "resistance", "volume", "consolidation", "technical analysis"]', 7),

('Mean Reversion Strategy', 'patterns', 'intermediate',
'## Mean Reversion

Mean reversion assumes that prices tend to return to their historical average over time. Assets that deviate significantly from their mean are expected to revert.

### Statistical Foundation
- **Z-Score**: Measures how many standard deviations a price is from the mean
  - Z > 2: Overbought, expect reversion downward
  - Z < -2: Oversold, expect reversion upward
- **Bollinger Bands**: Dynamic mean reversion bands (20-period SMA ± 2 standard deviations)

### Entry Criteria
1. Price reaches 2+ standard deviations from the moving average
2. RSI confirms extreme reading (< 30 or > 70)
3. Volume shows exhaustion (declining on the extreme move)
4. Price begins to turn back toward the mean

### Risk Management
- Mean reversion works best in ranging markets
- In strong trends, mean reversion signals can fail badly
- Always use stop losses (price can stay extreme longer than expected)
- Position size smaller on mean reversion trades (higher failure rate)

### AlphaForge Integration
Signals tagged **mean_reversion** use Bollinger Band deviation and RSI extremes. Best applied when market regime is detected as "ranging".',
'["mean reversion", "z-score", "Bollinger Bands", "RSI", "statistical", "technical analysis"]', 10),

-- STRATEGIES (4 guides)
('Copy Trading Best Practices', 'strategies', 'beginner',
'## Copy Trading on AlphaForge

Copy trading lets you automatically mirror the trades of experienced signal creators. Here''s how to do it effectively.

### Choosing Signal Creators
1. **Track Record**: Look for creators with 3+ months of verified history
2. **Risk-Adjusted Returns**: Sharpe ratio > 1.0 is good, > 1.5 is excellent
3. **Max Drawdown**: Should be < 20% for conservative, < 35% for aggressive
4. **Win Rate**: 45-60% is typical for profitable traders (higher often means small wins)

### Risk Management
- **Never copy 100% of a position**. Start with 10-25% allocation per creator
- **Diversify across 3-5 creators** to avoid single-point-of-failure
- **Set your own stop losses** regardless of the creator''s settings
- **Monitor regularly** - even good creators have bad streaks

### Paper Trade First
1. Follow a creator on paper trading for 2+ weeks
2. Compare their paper results to live results
3. Only go live after confirming consistency

### Red Flags
- Creator has no verified track record
- Returns are suspiciously consistent (no drawdowns)
- Strategy uses excessive leverage (> 5x)
- Creator doesn''t explain their approach',
'["copy trading", "social trading", "signal following", "portfolio allocation", "risk management"]', 10),

('Position Sizing Methods', 'strategies', 'intermediate',
'## Position Sizing

Position sizing determines how much capital to allocate to each trade. It''s the single most important factor in long-term trading success.

### Fixed Fractional
- Risk a fixed percentage of your account per trade (typically 1-2%)
- **Formula**: Position Size = (Account × Risk%) / (Entry - Stop Loss)
- Pros: Simple, scales with account growth
- Cons: Doesn''t account for conviction level

### Kelly Criterion
- Optimal position size based on win rate and win/loss ratio
- **Formula**: f* = (bp - q) / b
  - b = average win / average loss
  - p = win probability
  - q = 1 - p (loss probability)
- **Always use half-Kelly or quarter-Kelly** in practice
- Pros: Mathematically optimal
- Cons: Requires accurate historical data

### Volatility-Based (ATR)
- Scale position inversely to volatility
- **Formula**: Position Size = (Account × Risk%) / (ATR × multiplier)
- High volatility = smaller positions
- Low volatility = larger positions
- Pros: Adapts to market conditions
- Cons: Requires ATR calculation

### Which to Use?
- **Beginners**: Fixed fractional (1-2% risk)
- **Intermediate**: Volatility-based
- **Advanced**: Kelly criterion with conservative fraction',
'["position sizing", "Kelly criterion", "risk management", "portfolio management", "ATR"]', 12),

('Risk Management Framework', 'strategies', 'beginner',
'## Risk Management Essentials

Every profitable trader''s edge comes from managing risk, not from picking winners.

### The 1% Rule
- Never risk more than 1% of your account on a single trade
- On a $10,000 account, maximum loss per trade = $100
- This ensures you can survive 20 consecutive losses and still trade

### Stop Loss Strategy
- **Always use stop losses** - no exceptions
- Set stop loss BEFORE entering a trade
- Base stops on technical levels, not arbitrary percentages
- Never move stop loss further from entry (only closer)

### Risk-Reward Ratio
- Minimum 1:2 risk-reward for every trade
- If risking $100, expect to make at least $200
- This means you only need to win 34% of trades to be profitable

### Portfolio-Level Risk
- Maximum 5-6 concurrent positions
- Maximum 20% total portfolio risk at any time
- Maximum 2 correlated positions (e.g., don''t go long BTC and ETH simultaneously)
- Rebalance when any position exceeds 25% of portfolio

### Psychological Rules
- Never revenge trade after a loss
- Take breaks after 2 consecutive losses
- Review every trade (win or lose) in a trading journal',
'["risk management", "stop loss", "position sizing", "portfolio risk", "trading psychology"]', 8),

('Backtesting Your Strategy', 'strategies', 'intermediate',
'## Backtesting Guide

Backtesting evaluates a trading strategy against historical data to estimate its viability before risking real capital.

### Key Metrics to Track
| Metric | Good | Excellent |
|--------|------|-----------|
| Sharpe Ratio | > 1.0 | > 1.5 |
| Win Rate | > 45% | > 55% |
| Profit Factor | > 1.5 | > 2.0 |
| Max Drawdown | < 20% | < 15% |
| Total Trades | > 100 | > 300 |

### Common Backtesting Pitfalls
1. **Overfitting**: Optimizing parameters to fit historical data perfectly
   - Fix: Use out-of-sample testing (test on data not used for optimization)
2. **Survivorship Bias**: Only testing assets that exist today
   - Fix: Include delisted assets in your dataset
3. **Look-Ahead Bias**: Using data that wouldn''t have been available in real-time
   - Fix: Strictly use only past data for each bar
4. **Transaction Costs**: Ignoring fees, slippage, and spread
   - Fix: Include realistic costs in every backtest

### AlphaForge Backtesting
Use the built-in backtester to test any strategy against historical signals. Set realistic slippage (0.1%) and commission (0.1%) parameters.',
'["backtesting", "strategy evaluation", "Sharpe ratio", "overfitting", "trading strategy"]', 10),

('Understanding Leverage', 'strategies', 'advanced',
'## Leverage in Crypto Trading

Leverage amplifies both gains and losses. Understanding it is essential before using margin.

### How Leverage Works
- **1x leverage**: $1,000 controls $1,000 worth of assets
- **5x leverage**: $1,000 controls $5,000 worth of assets
- **10x leverage**: $1,000 controls $10,000 worth of assets

### The Math of Leverage
With 5x leverage on a $1,000 position:
- **+5% price move**: +25% return ($250 gain)
- **-5% price move**: -25% return ($250 loss)
- **-20% price move**: -100% (total liquidation)

### Liquidation Price
- With 5x leverage, liquidation occurs at approximately -18% from entry
- With 10x leverage, liquidation occurs at approximately -9% from entry
- Crypto can move 10%+ in hours - leveraged positions are high risk

### When to Use Leverage
- Only when you have a proven, backtested strategy
- Only with strict stop losses
- Only risk 1-2% of account per trade (leverage affects this calculation)
- Start with 2-3x maximum until experienced

### AlphaForge Leverage Settings
The platform enforces maximum leverage limits. Configure your risk tolerance in Settings to prevent over-leveraging.',
'["leverage", "margin", "liquidation", "risk management", "advanced trading"]', 9),

-- QUANT BASICS (3 guides)
('Sharpe Ratio Explained', 'quant_basics', 'beginner',
'## Sharpe Ratio

The Sharpe Ratio measures risk-adjusted return - how much excess return you earn per unit of risk taken.

### Formula
**Sharpe Ratio = (Rp - Rf) / σp**
- Rp = Portfolio return
- Rf = Risk-free rate (e.g., Treasury bill rate)
- σp = Portfolio standard deviation (volatility)

### Interpreting the Numbers
| Sharpe Ratio | Rating |
|-------------|--------|
| < 0.5 | Poor |
| 0.5 - 1.0 | Acceptable |
| 1.0 - 1.5 | Good |
| 1.5 - 2.0 | Very Good |
| > 2.0 | Excellent |

### Example
- Strategy A: 30% annual return, 25% volatility → Sharpe = (30-5)/25 = **1.0**
- Strategy B: 20% annual return, 10% volatility → Sharpe = (20-5)/10 = **1.5**

Strategy B has a better Sharpe ratio despite lower absolute returns because it takes less risk.

### Limitations
- Assumes returns are normally distributed (crypto returns often aren''t)
- Doesn''t distinguish between upside and downside volatility
- Best used alongside other metrics (Sortino, max drawdown)

### In AlphaForge
Every signal creator''s track record displays their Sharpe ratio. Look for creators with Sharpe > 1.0.',
'["Sharpe ratio", "risk-adjusted return", "volatility", "quantitative", "portfolio metrics"]', 7),

('Kelly Criterion for Position Sizing', 'quant_basics', 'intermediate',
'## Kelly Criterion

The Kelly Criterion determines the optimal bet size to maximize long-term growth rate.

### Formula
**f* = (bp - q) / b**
- f* = fraction of bankroll to wager
- b = net odds received (win amount / loss amount)
- p = probability of winning
- q = probability of losing (1 - p)

### Example
- Win rate: 55% (p = 0.55, q = 0.45)
- Average win: $200, Average loss: $100 (b = 2.0)
- f* = (2.0 × 0.55 - 0.45) / 2.0 = **0.325** (32.5% of bankroll)

### Why Half-Kelly or Quarter-Kelly?
Full Kelly is theoretically optimal but:
- It assumes perfect knowledge of your edge (which you don''t have)
- It''s extremely volatile in practice
- A few bad losses can destroy your bankroll

**Practical rule**: Use 25-50% of Kelly recommendation
- Half-Kelly: Reduces volatility by 50%, only costs 25% of growth
- Quarter-Kelly: Further reduces risk, more conservative

### Connecting to Trading
Your trading edge = (Win Rate × Average Win) - (Loss Rate × Average Loss)
Kelly tells you the maximum you should risk given that edge.

### AlphaForge Integration
The Kelly Criterion is calculated for each signal based on historical performance data. Use it as a guideline, not a rule.',
'["Kelly criterion", "position sizing", "optimal bet", "bankroll management", "quantitative"]', 9),

('Understanding Drawdown', 'quant_basics', 'beginner',
'## Drawdown

Drawdown measures the decline from a peak to a trough in your account balance. It''s the most important risk metric for evaluating trading performance.

### Types of Drawdown
- **Maximum Drawdown (MDD)**: Largest peak-to-trough decline
  - If account goes from $100K → $70K → $120K → $90K
  - MDD = 25% (from $120K to $90K)
- **Current Drawdown**: How far you are from your current peak
- **Average Drawdown**: Mean of all drawdown periods

### Why It Matters
- **Recovery requires exponential gains**:
  - -10% drawdown requires +11% to recover
  - -25% drawdown requires +33% to recover
  - -50% drawdown requires +100% to recover
  - -75% drawdown requires +300% to recover

### Acceptable Drawdowns by Style
| Trading Style | Max Acceptable MDD |
|--------------|-------------------|
| Conservative | 5-10% |
| Moderate | 10-20% |
| Aggressive | 20-35% |
| Very Aggressive | 35-50% |

### Managing Drawdowns
1. **Reduce position sizes** as drawdown increases
2. **Take a break** after drawdown exceeds your comfort level
3. **Review your strategy** if drawdown exceeds historical MDD
4. **Never add to a losing position** to "average down"

### AlphaForge Dashboard
Your portfolio dashboard shows current drawdown and historical MDD. Monitor these metrics to stay within your risk tolerance.',
'["drawdown", "maximum drawdown", "risk management", "portfolio metrics", "recovery"]', 7)

ON CONFLICT DO NOTHING;
