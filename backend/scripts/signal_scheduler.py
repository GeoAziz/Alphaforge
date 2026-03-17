"""
Signal processing scheduler.
Runs signal aggregation and processing at regular intervals.
"""

import asyncio
import logging
import os
from datetime import datetime
from schedule import every, run_pending
import time

from config import Config, SignalConfig
from database.db import get_db
from services.signal_aggregator import SignalAggregator
from services.signal_processor import SignalProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalScheduler:
    """Manages scheduled signal generation and processing."""
    
    def __init__(self):
        self.db = get_db()
        self.aggregator = SignalAggregator()
        self.processor = SignalProcessor()
        self.symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "MATIC", "AVAX", "LINK"]
    
    async def process_signals_job(self):
        """Main signal processing job."""
        logger.info("🔄 Starting signal processing job...")
        
        try:
            # Aggregate signals
            logger.info(f"📊 Aggregating signals for {len(self.symbols)} symbols...")
            raw_signals = await self.aggregator.fetch_all_signals(self.symbols)
            
            if not raw_signals:
                logger.info("ℹ️ No signals generated this cycle")
                return
            
            # Process and rank
            logger.info(f"⚙️ Processing {len(raw_signals)} raw signals...")
            processed_signals = self.processor.process_signals(raw_signals)
            
            # Store in database
            logger.info(f"💾 Storing {len(processed_signals)} processed signals...")
            for signal in processed_signals:
                signal["created_at"] = datetime.utcnow().isoformat()
                
                try:
                    self.db.supabase.table("signals").insert(signal).execute()
                except Exception as e:
                    logger.warning(f"Could not store signal {signal.get('ticker')}: {e}")
            
            logger.info(f"✅ Signal processing job complete: {len(processed_signals)} signals stored")
            
        except Exception as e:
            logger.error(f"❌ Signal processing job failed: {e}")
    
    def schedule_jobs(self):
        """Set up recurring jobs."""
        interval_seconds = Config.SIGNAL_PROCESSOR_INTERVAL
        interval_minutes = max(1, interval_seconds // 60)
        
        logger.info(f"📅 Scheduling signal processing every {interval_minutes} minutes")
        
        # Run signal processing job at regular intervals
        every(interval_minutes).minutes.do(self.run_async_job, self.process_signals_job)
        
        logger.info("✅ Jobs scheduled")
    
    @staticmethod
    def run_async_job(coro):
        """Helper to run async functions in scheduler."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)
    
    async def run(self):
        """Start the scheduler."""
        logger.info("🚀 Signal Scheduler starting...")
        
        self.schedule_jobs()
        
        # Run scheduler loop
        try:
            while True:
                run_pending()
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("🛑 Scheduler stopped")
            await self.aggregator.close()


async def main():
    """Entry point."""
    scheduler = SignalScheduler()
    await scheduler.run()


if __name__ == "__main__":
    asyncio.run(main())
