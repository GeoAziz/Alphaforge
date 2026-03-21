#!/usr/bin/env python3
"""
Recommendation System Data Populator
Loads generated historical data into the recommendation system database
"""

import os
import json
from datetime import datetime
from typing import Any, Dict
from collections import defaultdict
import logging
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import database
from database.db import Database
from generate_historical_data import (
    generate_historical_trades,
    generate_external_signal_sources,
    generate_market_correlations
)


class DataPopulator:
    """Populates recommendation system with historical data"""
    
    def __init__(self, db: Database):
        self.db = db
        self.stats = {
            "trades_inserted": 0,
            "sources_updated": 0,
            "correlations_inserted": 0,
            "errors": []
        }
    
    def populate_signal_performance(self, trades: list):
        """Aggregate trades by signal and insert into signal_performance table"""
        
        logger.info(f"\n📥 Aggregating {len(trades)} trades into signal metrics...")
        
        # Aggregate trades by signal_id
        signals = defaultdict(list)
        for trade in trades:
            signals[trade["signal_id"]].append(trade)
        
        logger.info(f"   Aggregating into {len(signals)} unique signals...")
        
        # Process each signal's trades
        for i, (signal_id, signal_trades) in enumerate(signals.items()):
            try:
                # Calculate aggregated metrics
                roi_values = [t["roi_pct"] for t in signal_trades]
                pnl_values = [t["pnl"] for t in signal_trades]
                
                winning_trades = [t for t in signal_trades if t["roi_pct"] > 0]
                losing_trades = [t for t in signal_trades if t["roi_pct"] <= 0]
                
                win_count = len(winning_trades)
                loss_count = len(losing_trades)
                total_trades = len(signal_trades)
                win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
                
                total_pnl = sum(pnl_values)
                avg_pnl_per_execution = total_pnl / total_trades if total_trades > 0 else 0
                total_roi_pct = sum(roi_values)
                avg_roi_per_execution = total_roi_pct / total_trades if total_trades > 0 else 0
                
                best_trade_pnl = max(pnl_values) if pnl_values else 0
                worst_trade_pnl = min(pnl_values) if pnl_values else 0
                
                # Calculate Sharpe ratio (simplified)
                if len(roi_values) > 1:
                    std_dev = statistics.stdev(roi_values) if len(roi_values) > 1 else 0
                    sharpe_ratio = (avg_roi_per_execution / std_dev) if std_dev > 0 else 0
                else:
                    sharpe_ratio = 0
                
                # Calculate max drawdown (simplified)
                max_drawdown_pct = 0
                if pnl_values:
                    cumsum = 0
                    peak = 0
                    for pnl in pnl_values:
                        cumsum += pnl
                        if cumsum > peak:
                            peak = cumsum
                        drawdown = peak - cumsum
                        if drawdown > max_drawdown_pct:
                            max_drawdown_pct = drawdown
                
                # High performer if win_rate > 60%
                is_high_performer = win_rate > 60
                
                # Get first and last execution times
                timestamps = [datetime.fromisoformat(t["timestamp"]) for t in signal_trades]
                first_execution_at = min(timestamps).isoformat() if timestamps else datetime.utcnow().isoformat()
                last_execution_at = max(timestamps).isoformat() if timestamps else datetime.utcnow().isoformat()
                
                # Signal accuracy score based on consistency
                accuracy_score = (win_rate / 100 * 100) + (50 if avg_roi_per_execution > 0 else 0)
                accuracy_score = min(accuracy_score, 100)
                
                data = {
                    "signal_id": signal_id,
                    "asset": signal_trades[0]["asset"],  # Use asset from first trade
                    "num_times_executed": total_trades,
                    "num_times_closed": total_trades,
                    "total_pnl": total_pnl,
                    "avg_pnl_per_execution": avg_pnl_per_execution,
                    "win_count": win_count,
                    "loss_count": loss_count,
                    "win_rate": win_rate,
                    "total_roi_pct": total_roi_pct,
                    "avg_roi_per_execution": avg_roi_per_execution,
                    "best_trade_pnl": best_trade_pnl,
                    "worst_trade_pnl": worst_trade_pnl,
                    "max_drawdown_pct": max_drawdown_pct,
                    "sharpe_ratio": sharpe_ratio,
                    "first_execution_at": first_execution_at,
                    "last_execution_at": last_execution_at,
                    "signal_accuracy_score": accuracy_score,
                    "is_high_performer": is_high_performer,
                    "is_winning": win_rate > 50,
                    "last_updated_at": datetime.utcnow().isoformat()
                }
                
                # Insert using Supabase
                response = self.db.supabase.table("signal_performance").insert(data).execute()
                self.stats["trades_inserted"] += 1
                
                if (i + 1) % 50 == 0:
                    logger.info(f"  ✓ Inserted {i + 1}/{len(signals)} signal aggregates")
                    
            except Exception as e:
                logger.error(f"  ✗ Error inserting signal {signal_id}: {str(e)}")
                self.stats["errors"].append(str(e))
        
        logger.info(f"✅ Inserted {self.stats['trades_inserted']} signal aggregates")
    
    def populate_external_sources(self, sources: list):
        """Update or insert external signal source rankings"""
        
        logger.info(f"\n📥 Loading {len(sources)} external sources into signal_sources table...")
        
        for i, source in enumerate(sources):
            try:
                data = {
                    "external_source": source["external_source"],
                    "total_signals_received": source["total_signals_received"],
                    "total_signals_executed": source["total_signals_executed"],
                    "signals_ignored": source["signals_ignored"],
                    "executed_win_rate": source["executed_win_rate"],
                    "total_pnl": source["total_pnl"],
                    "reliability_score": source["reliability_score"],
                    "recommendation": source["recommendation"],
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                # Try to update, if no rows affected then insert
                try:
                    response = (self.db.supabase
                        .table("signal_sources")
                        .update(data)
                        .eq("external_source", source["external_source"])
                        .execute())
                    
                    if not response.data:
                        # No rows updated, insert instead
                        self.db.supabase.table("signal_sources").insert(data).execute()
                except Exception:
                    # Insert on update failure
                    self.db.supabase.table("signal_sources").insert(data).execute()
                
                self.stats["sources_updated"] += 1
                
                if (i + 1) % 5 == 0:
                    logger.info(f"  ✓ Processed {i + 1}/{len(sources)} sources")
                    
            except Exception as e:
                logger.error(f"  ✗ Error processing source {source['external_source']}: {str(e)}")
                self.stats["errors"].append(str(e))
        
        logger.info(f"✅ Processed {self.stats['sources_updated']} sources")
    
    def populate_correlations(self, correlations: list):
        """Insert market correlation data"""
        
        logger.info(f"\n📥 Loading {len(correlations)} correlations into market_correlations table...")
        
        for i, corr in enumerate(correlations):
            try:
                data = {
                    "asset1": corr["asset1"],
                    "asset2": corr["asset2"],
                    "correlation_1d": corr["correlation_1d"],
                    "correlation_7d": corr["correlation_7d"],
                    "correlation_30d": corr["correlation_30d"],
                    "volatility_1d": corr["volatility_1d"],
                    "volatility_7d": corr["volatility_7d"],
                    "volatility_30d": corr["volatility_30d"],
                    "trend_strength_1d": corr["trend_strength_1d"],
                    "trend_strength_7d": corr["trend_strength_7d"],
                    "trend_strength_30d": corr["trend_strength_30d"],
                    "divergence_detected": corr["divergence_detected"],
                    "divergence_strength": corr["divergence_strength"],
                    "last_computed_at": datetime.utcnow().isoformat()
                }
                
                response = self.db.supabase.table("market_correlations").insert(data).execute()
                self.stats["correlations_inserted"] += 1
                
                if (i + 1) % 5 == 0:
                    logger.info(f"  ✓ Inserted {i + 1}/{len(correlations)} correlations")
                    
            except Exception as e:
                logger.error(f"  ✗ Error inserting correlation {corr['asset1']}/{corr['asset2']}: {str(e)}")
                self.stats["errors"].append(str(e))
        
        logger.info(f"✅ Inserted {self.stats['correlations_inserted']} correlations")
    
    def print_stats(self):
        """Print population statistics"""
        
        logger.info("\n" + "="*70)
        logger.info("📊 POPULATION STATISTICS")
        logger.info("="*70)
        logger.info(f"✅ Trades inserted:       {self.stats['trades_inserted']}")
        logger.info(f"✅ Sources processed:     {self.stats['sources_updated']}")
        logger.info(f"✅ Correlations inserted: {self.stats['correlations_inserted']}")
        
        if self.stats["errors"]:
            logger.info(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats["errors"][:5]:  # Show first 5
                logger.info(f"   - {error}")
        
        total = (self.stats['trades_inserted'] + 
                self.stats['sources_updated'] + 
                self.stats['correlations_inserted'])
        
        logger.info(f"\n🎉 Total records processed: {total}")
        logger.info("="*70)


def main():
    """Main function"""
    
    logger.info("\n" + "="*70)
    logger.info("🚀 AlphaForge Recommendation System - Data Populator")
    logger.info("="*70)
    
    try:
        # Initialize database
        logger.info("\n🔌 Connecting to database...")
        db = Database()
        logger.info("✅ Database connected")
        
        # Generate data
        logger.info("\n📊 Generating historical data...")
        trades = generate_historical_trades(num_trades=200, win_rate=0.68)
        sources = generate_external_signal_sources(num_sources=15)
        correlations = generate_market_correlations(num_pairs=20)
        logger.info(f"✅ Generated {len(trades)} trades, {len(sources)} sources, {len(correlations)} correlations")
        
        # Populate
        populator = DataPopulator(db)
        
        logger.info("\n📥 POPULATING DATABASE")
        populator.populate_signal_performance(trades)
        populator.populate_external_sources(sources)
        populator.populate_correlations(correlations)
        
        # Print stats
        populator.print_stats()
        
        # Test queries
        logger.info("\n🧪 TESTING QUERIES")
        logger.info("-" * 70)
        
        # Test 1: High performers
        logger.info("\n1️⃣  High Performers (Win Rate > 60%):")
        try:
            hp_response = db.supabase.table("signal_performance").select(
                "signal_id, asset, win_rate, is_winning"
            ).gte("win_rate", 60).limit(5).execute()
            
            if hp_response.data:
                for trade in hp_response.data:
                    logger.info(f"   {trade['signal_id']}: {trade['asset']} Win Rate: {trade['win_rate']:.1f}%")
            else:
                logger.info("   No high performers found yet")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        
        # Test 2: Reliable sources
        logger.info("\n2️⃣  Reliable External Sources (Score > 0.7):")
        try:
            rs_response = db.supabase.table("signal_sources").select(
                "external_source, reliability_score, recommendation"
            ).gte("reliability_score", 0.7).limit(5).execute()
            
            if rs_response.data:
                for source in rs_response.data:
                    logger.info(f"   {source['external_source']}: {source['recommendation']} ({source['reliability_score']:.2f})")
            else:
                logger.info("   No reliable sources found yet")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        
        # Test 3: Correlations
        logger.info("\n3️⃣  Market Correlations (Sample):")
        try:
            corr_response = db.supabase.table("market_correlations").select(
                "asset1, asset2, correlation_30d, divergence_detected"
            ).limit(5).execute()
            
            if corr_response.data:
                for corr in corr_response.data:
                    logger.info(f"   {corr['asset1']}/{corr['asset2']}: {corr['correlation_30d']:.2f} (Divergence: {corr['divergence_detected']})")
            else:
                logger.info("   No correlations found yet")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        
        logger.info("\n" + "="*70)
        logger.info("✨ Data population complete!")
        logger.info("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
