#!/usr/bin/env python3
"""
AlphaForge Supabase Database Initialization Script
Initialize PostgreSQL schema in Supabase for Phase 1 MVP

Usage:
    python scripts/init_supabase_db.py         # Uses .env DATABASE_URL
    python scripts/init_supabase_db.py --reset # WARNING: Drops all tables first
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def get_db_connection():
    """Get PostgreSQL connection using SQLAlchemy."""
    from sqlalchemy import create_engine, text
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not set in environment")
        sys.exit(1)
    
    try:
        engine = create_engine(database_url)
        conn = engine.connect()
        logger.info(f"✅ Connected to PostgreSQL")
        return conn, engine
    except Exception as e:
        logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)


def read_migration_sql() -> str:
    """Read migration SQL from supabase_phase1_init.sql."""
    sql_path = Path(__file__).parent.parent / 'database' / 'supabase_phase1_init.sql'
    
    if not sql_path.exists():
        logger.error(f"❌ Migration SQL not found at {sql_path}")
        sys.exit(1)
    
    with open(sql_path, 'r') as f:
        return f.read()


def reset_database(conn):
    """Drop all tables to reset database. WARNING: This deletes all data!"""
    logger.warning("⚠️  RESETTING DATABASE - ALL DATA WILL BE LOST")
    confirm = input("Type 'yes' to confirm: ")
    if confirm != 'yes':
        logger.info("Reset cancelled")
        return
    
    from sqlalchemy import text
    
    tables = [
        'strategy_paper_trades', 'strategy_subscriptions', 'strategies',
        'external_signal_rules', 'external_signals', 'creator_strategies',
        'creator_profiles', 'kyc_verifications', 'audit_logs',
        'user_risk_settings', 'notifications', 'chat_messages',
        'backtests', 'api_keys', 'positions', 'paper_trades',
        'portfolios', 'signals', 'users'
    ]
    
    try:
        for table in tables:
            conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
            logger.info(f"  Dropped table: {table}")
        conn.commit()
        logger.info("✅ All tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        conn.rollback()
        sys.exit(1)


def execute_migration(conn, sql: str) -> bool:
    """Execute migration SQL against database."""
    from sqlalchemy import text
    
    try:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            logger.debug(f"Executing statement {i}/{len(statements)}...")
            conn.execute(text(statement))
        
        conn.commit()
        logger.info(f"✅ Successfully executed {len(statements)} SQL statements")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        return False


def verify_schema(conn) -> bool:
    """Verify schema was created correctly."""
    from sqlalchemy import text
    
    try:
        # Check core tables exist
        expected_tables = [
            'users', 'signals', 'paper_trades', 'positions', 'portfolios',
            'creator_profiles', 'creator_strategies', 'strategy_subscriptions',
            'kyc_verifications', 'audit_logs', 'external_signals',
            'external_signal_rules', 'api_keys', 'backtests',
            'chat_messages', 'notifications', 'user_risk_settings', 'strategies'
        ]
        
        result = conn.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname='public' 
            ORDER BY tablename
        """))
        
        existing_tables = [row[0] for row in result.fetchall()]
        missing_tables = set(expected_tables) - set(existing_tables)
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        logger.info(f"✅ All {len(expected_tables)} core tables created")
        
        # Check RLS policies
        result = conn.execute(text("""
            SELECT COUNT(*) FROM pg_policies 
            WHERE schemaname='public'
        """))
        
        policy_count = result.scalar()
        logger.info(f"✅ RLS policies enabled: {policy_count} policies found")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema verification failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Initialize AlphaForge Supabase schema'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop all tables before initializing (⚠️ WARNING: Deletes all data)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify schema, do not modify'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("AlphaForge Supabase Database Initialization")
    logger.info("=" * 70)
    
    # Get connection
    conn, engine = get_db_connection()
    
    try:
        if args.verify_only:
            logger.info("Verifying existing schema...")
            if verify_schema(conn):
                logger.info("✅ Schema verification passed")
                sys.exit(0)
            else:
                logger.error("❌ Schema verification failed")
                sys.exit(1)
        
        # Reset if requested
        if args.reset:
            reset_database(conn)
        
        # Read migration SQL
        migration_sql = read_migration_sql()
        logger.info(f"Loaded migration SQL ({len(migration_sql)} bytes)")
        
        # Execute migration
        logger.info("Executing migration...")
        if not execute_migration(conn, migration_sql):
            sys.exit(1)
        
        # Verify
        logger.info("Verifying schema...")
        if not verify_schema(conn):
            sys.exit(1)
        
        logger.info("=" * 70)
        logger.info("✅ Database initialization complete!")
        logger.info("=" * 70)
        logger.info("\nNext steps:")
        logger.info("1. Start backend: python main.py")
        logger.info("2. Run tests: pytest -v")
        logger.info("3. Deploy to Render/Railway")
        logger.info("4. Update frontend NEXT_PUBLIC_API_URL")
        
    finally:
        conn.close()
        engine.dispose()


if __name__ == '__main__':
    main()
