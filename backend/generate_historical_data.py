#!/usr/bin/env python3
"""
Historical Data Generator
Generates realistic historical trade data to populate recommendation system
"""

import asyncio
import random
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def generate_historical_trades(
    num_trades: int = 100,
    win_rate: float = 0.65,
    avg_roi: float = 0.02,
    roi_std_dev: float = 0.03
) -> list:
    """Generate realistic historical trade data"""
    
    trades = []
    base_time = datetime.utcnow() - timedelta(days=90)  # 90 days of history
    
    assets = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "MATIC"]
    directions = ["BUY", "SELL"]
    
    for i in range(num_trades):
        # Random time over 90 days
        trade_time = base_time + timedelta(
            hours=random.randint(0, 90 * 24),
            minutes=random.randint(0, 59)
        )
        
        # Generate outcome
        is_winning = random.random() < win_rate
        
        if is_winning:
            roi = random.gauss(avg_roi, roi_std_dev / 2)  # Tighter distribution for winners
            roi = max(roi, 0.001)  # Ensure positive
        else:
            roi = random.gauss(-avg_roi * 0.5, roi_std_dev / 2)  # Smaller losses
            roi = min(roi, -0.001)  # Ensure negative
        
        # Entry and exit prices
        entry_price = random.uniform(100, 90000)  # Realistic price range
        exit_price = entry_price * (1 + roi)
        pnl = exit_price - entry_price
        
        trades.append({
            "signal_id": f"sig_{i:06d}",
            "asset": random.choice(assets),
            "direction": random.choice(directions),
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "roi_pct": roi * 100,
            "outcome": "WINNING_TRADE" if is_winning else "LOSING_TRADE",
            "timestamp": trade_time.isoformat(),
            "size": random.uniform(0.1, 10.0)  # Position size
        })
    
    return trades


def generate_external_signal_sources(num_sources: int = 10) -> list:
    """Generate external signal source performance data"""
    
    sources = []
    source_types = ["tradingview", "telegram", "webhook", "pine_script"]
    
    for i in range(num_sources):
        total_signals = random.randint(10, 200)
        reliability_score = random.uniform(0.3, 0.95)
        win_rate = reliability_score * 0.85  # Slightly lower than reliability
        
        source = {
            "external_source": f"{random.choice(source_types)}_source_{i}",
            "total_signals_received": total_signals,
            "total_signals_executed": int(total_signals * random.uniform(0.6, 0.95)),
            "signals_ignored": int(total_signals * random.uniform(0.05, 0.4)),
            "executed_win_rate": win_rate,
            "total_pnl": random.uniform(-5000, 50000),
            "reliability_score": reliability_score,
            "recommendation": get_recommendation(reliability_score),
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).isoformat()
        }
        
        sources.append(source)
    
    return sources


def get_recommendation(reliability_score: float) -> str:
    """Get recommendation level based on reliability score"""
    if reliability_score > 0.75:
        return "HIGHLY_TRUSTED"
    elif reliability_score > 0.65:
        return "RELIABLE"
    elif reliability_score > 0.55:
        return "MARGINAL"
    else:
        return "UNRELIABLE"


def generate_market_correlations(num_pairs: int = 15) -> list:
    """Generate market correlation data"""
    
    assets = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "MATIC", "AVAX", "LINK"]
    correlations = []
    used_pairs = set()
    
    for _ in range(num_pairs):
        # Ensure unique pairs
        pair = tuple(sorted(random.sample(assets, 2)))
        if pair in used_pairs:
            continue
        used_pairs.add(pair)
        
        asset1, asset2 = pair
        
        # Generate correlated values
        base_corr = random.uniform(0.5, 0.98)
        
        corr_data = {
            "asset1": asset1,
            "asset2": asset2,
            "correlation_1d": base_corr * random.uniform(0.7, 1.0),
            "correlation_7d": base_corr * random.uniform(0.8, 1.0),
            "correlation_30d": base_corr,
            "volatility_1d": random.uniform(0.01, 0.08),
            "volatility_7d": random.uniform(0.01, 0.06),
            "volatility_30d": random.uniform(0.01, 0.05),
            "trend_strength_1d": random.uniform(0.3, 0.9),
            "trend_strength_7d": random.uniform(0.3, 0.8),
            "trend_strength_30d": random.uniform(0.3, 0.7),
            "divergence_detected": random.random() < 0.2,  # 20% chance
            "divergence_strength": random.uniform(0, 0.5),
            "last_computed_at": datetime.utcnow().isoformat()
        }
        
        correlations.append(corr_data)
    
    return correlations


def print_sample_data():
    """Print sample generated data"""
    
    logger.info("\n" + "="*70)
    logger.info("📊 GENERATED SAMPLE DATA")
    logger.info("="*70)
    
    # Sample trades
    logger.info("\n🎯 Sample Trades (first 5):")
    trades = generate_historical_trades(num_trades=5)
    for trade in trades:
        logger.info(f"  {trade['signal_id']}: {trade['asset']} {trade['direction']} → PnL: ${trade['pnl']:+.2f} ({trade['roi_pct']:+.1f}%)")
    
    # Sample sources
    logger.info("\n🌐 Sample External Sources (first 3):")
    sources = generate_external_signal_sources(num_sources=3)
    for source in sources:
        logger.info(f"  {source['external_source']}: {source['recommendation']} (Score: {source['reliability_score']:.2f})")
    
    # Sample correlations
    logger.info("\n📈 Sample Market Correlations (first 3):")
    corrs = generate_market_correlations(num_pairs=3)
    for corr in corrs:
        logger.info(f"  {corr['asset1']}/{corr['asset2']}: 30d Corr={corr['correlation_30d']:.2f}, Volatility={corr['volatility_30d']:.3f}")
    
    logger.info("\n" + "="*70)


def export_to_json(data: list, filename: str):
    """Export data to JSON file"""
    import json
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"✅ Exported {len(data)} records to {filename}")


async def main():
    """Main function"""
    logger.info("🚀 AlphaForge Historical Data Generator\n")
    
    # Generate large dataset
    logger.info("📊 Generating 200 historical trades...")
    trades = generate_historical_trades(num_trades=200, win_rate=0.68)
    
    logger.info("🌐 Generating 15 external signal sources...")
    sources = generate_external_signal_sources(num_sources=15)
    
    logger.info("📈 Generating 20 market correlations...")
    correlations = generate_market_correlations(num_pairs=20)
    
    # Export
    export_to_json(trades, "historical_trades.json")
    export_to_json(sources, "external_sources.json")
    export_to_json(correlations, "market_correlations.json")
    
    # Print samples
    print_sample_data()
    
    # Summary
    logger.info("\n✨ Data generation complete!")
    logger.info(f"   - {len(trades)} trades generated")
    logger.info(f"   - {len(sources)} external sources")
    logger.info(f"   - {len(correlations)} correlation pairs")
    logger.info("\nNext steps:")
    logger.info("  1. Load this data into your database")
    logger.info("  2. Run: python populate_recommendation_system.py")
    logger.info("  3. Test endpoints to see high performers\n")


if __name__ == "__main__":
    asyncio.run(main())
