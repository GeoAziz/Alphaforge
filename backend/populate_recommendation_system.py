#!/usr/bin/env python3
"""
Recommendation System Data Populator
Loads generated historical data into the recommendation system database
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Any, Dict
import logging

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
    
    async def populate_signal_performance(self, trades: list):
        """Insert historical trades into signal_performance table"""
        
        logger.info(f"\n📥 Loading {len(trades)} trades into signal_performance table...")
        
        for i, trade in enumerate(trades):
            try:
                # Calculate derived fields
                win = 1 if trade["roi_pct"] > 0 else 0
                
                data = {
                    "signal_id": trade["signal_id"],
                    "asset": trade["asset"],
                    "direction": trade["direction"],
                    "entry_price": trade["entry_price"],
                    "exit_price": trade["exit_price"],
                    "pnl": trade["pnl"],
                    "roi_pct": trade["roi_pct"],
                    "is_winning": win,
                    "outcome": trade["outcome"],
                    "execution_timestamp": trade["timestamp"],
                    "position_size": trade["size"],
                    "created_at": datetime.utcnow().isoformat()
                }
                
                # Insert using Supabase
                response = await self.db.supabase.table("signal_performance").insert(data).execute()
                self.stats["trades_inserted"] += 1
                
                if (i + 1) % 50 == 0:
                    logger.info(f"  ✓ Inserted {i + 1}/{len(trades)} trades")
                    
            except Exception as e:
                logger.error(f"  ✗ Error inserting trade {trade['signal_id']}: {str(e)}")
                self.stats["errors"].append(str(e))
        
        logger.info(f"✅ Inserted {self.stats['trades_inserted']} trades")
    
    async def populate_external_sources(self, sources: list):
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
                    response = await (self.db.supabase
                        .table("signal_sources")
                        .update(data)
                        .eq("external_source", source["external_source"])
                        .execute())
                    
                    if not response.data:
                        # No rows updated, insert instead
                        await self.db.supabase.table("signal_sources").insert(data).execute()
                except Exception:
                    # Insert on update failure
                    await self.db.supabase.table("signal_sources").insert(data).execute()
                
                self.stats["sources_updated"] += 1
                
                if (i + 1) % 5 == 0:
                    logger.info(f"  ✓ Processed {i + 1}/{len(sources)} sources")
                    
            except Exception as e:
                logger.error(f"  ✗ Error processing source {source['external_source']}: {str(e)}")
                self.stats["errors"].append(str(e))
        
        logger.info(f"✅ Processed {self.stats['sources_updated']} sources")
    
    async def populate_correlations(self, correlations: list):
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
                    "computed_at": datetime.utcnow().isoformat()
                }
                
                response = await self.db.supabase.table("market_correlations").insert(data).execute()
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


async def main():
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
        await populator.populate_signal_performance(trades)
        await populator.populate_external_sources(sources)
        await populator.populate_correlations(correlations)
        
        # Print stats
        populator.print_stats()
        
        # Test queries
        logger.info("\n🧪 TESTING QUERIES")
        logger.info("-" * 70)
        
        # Test 1: High performers
        logger.info("\n1️⃣  High Performers (Win Rate > 60%):")
        hp_response = await db.supabase.table("signal_performance").select(
            "signal_id, asset, roi_pct, is_winning"
        ).gte("roi_pct", 1).limit(5).execute()
        
        if hp_response.data:
            for trade in hp_response.data:
                logger.info(f"   {trade['signal_id']}: {trade['asset']} ROI: {trade['roi_pct']:.1f}%")
        else:
            logger.info("   No high performers found yet")
        
        # Test 2: Reliable sources
        logger.info("\n2️⃣  Reliable External Sources (Score > 0.7):")
        rs_response = await db.supabase.table("signal_sources").select(
            "external_source, reliability_score, recommendation"
        ).gte("reliability_score", 0.7).limit(5).execute()
        
        if rs_response.data:
            for source in rs_response.data:
                logger.info(f"   {source['external_source']}: {source['recommendation']} ({source['reliability_score']:.2f})")
        else:
            logger.info("   No reliable sources found yet")
        
        # Test 3: Correlations
        logger.info("\n3️⃣  Market Correlations (Sample):")
        corr_response = await db.supabase.table("market_correlations").select(
            "asset1, asset2, correlation_30d, divergence_detected"
        ).limit(5).execute()
        
        if corr_response.data:
            for corr in corr_response.data:
                logger.info(f"   {corr['asset1']}/{corr['asset2']}: {corr['correlation_30d']:.2f} (Divergence: {corr['divergence_detected']})")
        else:
            logger.info("   No correlations found yet")
        
        logger.info("\n" + "="*70)
        logger.info("✨ Data population complete!")
        logger.info("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
