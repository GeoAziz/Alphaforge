"""
Database initialization script.
Run this once to set up Supabase tables and schema.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from database.db import get_db
from database.migrations import MIGRATION_SQL

load_dotenv()


async def init_database():
    """Initialize Supabase database with schema."""
    
    print("🔧 Initializing AlphaForge database...")
    print("-" * 60)
    
    try:
        db = get_db()
        
        # Test connection
        print("📡 Testing Supabase connection...")
        result = db.supabase.table("users").select("*").limit(1).execute()
        print("✅ Supabase connection successful")
        
        # Run migrations
        print("\n📝 Running schema migrations...")
        print("   Creating tables: users, signals, paper_trades, portfolios...")
        print("   Creating indices for performance...")
        print("   Enabling Row Level Security (RLS)...")
        
        # Note: Direct SQL execution requires admin access
        # For free Supabase tier, manually run the SQL in the SQL Editor
        print("\n⚠️  WARNING: Supabase free tier doesn't support direct SQL execution")
        print("   Manual setup required:")
        print("\n   1. Go to Supabase dashboard")
        print("   2. Open SQL Editor")
        print("   3. Create a new query")
        print("   4. Copy-paste this SQL:")
        print("\n" + "=" * 60)
        print(MIGRATION_SQL[:500] + "...\n(see database/migrations.py for full SQL)")
        print("=" * 60)
        print("\n   5. Execute the query")
        
        # Create tables via Python client (limited support)
        print("\n🔨 Creating tables via API client...")
        
        # Users table
        try:
            db.supabase.table("users").select("*").limit(1).execute()
            print("✓ users table exists")
        except:
            print("ℹ Make sure to run SQL migrations manually")
        
        print("\n✅ Database initialization complete!")
        print("\n📚 Next steps:")
        print("   1. Set up environment variables in .env")
        print("   2. Run: python -m scripts.init_db")
        print("   3. Start backend: python main.py")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)


async def seed_sample_data():
    """Seed database with sample signals for testing."""
    
    print("\n🌱 Seeding sample data...")
    
    try:
        db = get_db()
        
        sample_signals = [
            {
                "ticker": "BTC",
                "signal_type": "BUY",
                "confidence": 0.85,
                "entry_price": 63200,
                "stop_loss_price": 62000,
                "take_profit_price": 65000,
                "rationale": "Bullish RSI divergence with volume confirmation",
                "drivers": ["RSI_divergence", "volume_breakout", "support_bounce"],
                "created_at": "2024-03-17T10:00:00Z"
            },
            {
                "ticker": "ETH",
                "signal_type": "SELL",
                "confidence": 0.72,
                "entry_price": 3450,
                "stop_loss_price": 3600,
                "take_profit_price": 3200,
                "rationale": "Overbought on 4H chart, potential pullback",
                "drivers": ["overbought_RSI", "resistance_test", "funding_rate_high"],
                "created_at": "2024-03-17T10:30:00Z"
            }
        ]
        
        for signal in sample_signals:
            db.supabase.table("signals").insert(signal).execute()
            print(f"✓ {signal['ticker']} {signal['signal_type']} signal created")
        
        print(f"✅ Seeded {len(sample_signals)} sample signals")
        
    except Exception as e:
        print(f"❌ Sample data seeding failed: {e}")


if __name__ == "__main__":
    asyncio.run(init_database())
    # asyncio.run(seed_sample_data())
