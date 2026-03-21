#!/usr/bin/env python3
"""
AlphaForge Database Migration Runner
Orchestrates the complete database initialization with Phase 1 and Phase 2 migrations.

Usage:
    python scripts/run_all_migrations.py          # Run all migrations
    python scripts/run_all_migrations.py --verify # Only verify existing schema
    python scripts/run_all_migrations.py --help   # Show help
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.migration_manager import MigrationManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.info(f"📖 Loaded environment from: {env_path}")
    else:
        logger.warning(f"⚠️  .env file not found at {env_path}")


def verify_prerequisites():
    """Verify that all prerequisites are met."""
    errors = []
    
    # Check DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        errors.append("DATABASE_URL environment variable not set")
    else:
        if not database_url.startswith("postgresql://"):
            errors.append("DATABASE_URL must be a PostgreSQL connection string")
    
    # Check migration files exist
    migrations_dir = Path(__file__).parent.parent / "database"
    required_files = [
        "supabase_phase1_init.sql",
        "recommendations_migration.sql"
    ]
    
    for filename in required_files:
        filepath = migrations_dir / filename
        if not filepath.exists():
            errors.append(f"Migration file not found: {filename}")
    
    if errors:
        logger.error("❌ Prerequisites check failed:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("✅ All prerequisites met")
    return True


def verify_schema_only():
    """Verify existing schema without running migrations."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("🔍 Verifying Existing Schema")
    logger.info("=" * 70)
    logger.info("")
    
    try:
        manager = MigrationManager()
        conn = manager.get_connection()
        
        # Count tables
        total_tables = manager.get_table_count(conn)
        logger.info(f"📊 Total tables in database: {total_tables}")
        
        # Verify Phase 1 tables
        logger.info("")
        logger.info("Phase 1 Tables (Core Schema):")
        phase1_ok, phase1_missing = manager.verify_tables(conn, manager.PHASE_1_TABLES, "phase_1")
        
        if phase1_ok:
            logger.info(f"✅ All {len(manager.PHASE_1_TABLES)} Phase 1 tables exist")
        else:
            logger.warning(f"⚠️  Missing Phase 1 tables: {phase1_missing}")
        
        # Verify Phase 2 tables
        logger.info("")
        logger.info("Phase 2 Tables (Recommendations):")
        phase2_ok, phase2_missing = manager.verify_tables(conn, manager.PHASE_2_TABLES, "phase_2")
        
        if phase2_ok:
            logger.info(f"✅ All {len(manager.PHASE_2_TABLES)} Phase 2 tables exist")
        else:
            logger.warning(f"⚠️  Missing Phase 2 tables: {phase2_missing}")
        
        conn.close()
        
        logger.info("")
        if phase1_ok and phase2_ok:
            logger.info("✅ Schema is complete and ready for production")
            return True
        elif phase1_ok:
            logger.info("⚠️  Phase 1 is complete, but Phase 2 is missing")
            logger.info("   Run without --verify flag to complete Phase 2 migration")
            return False
        else:
            logger.info("❌ Schema is incomplete, migrations required")
            return False
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AlphaForge Database Migration Runner',
        epilog="""
Examples:
  python scripts/run_all_migrations.py          # Run all migrations
  python scripts/run_all_migrations.py --verify # Only verify existing schema
        """
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Only verify existing schema, do not run migrations'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force run migrations even if tables already exist (USE WITH CAUTION)'
    )
    
    args = parser.parse_args()
    
    # Load environment
    load_environment()
    
    # Verify prerequisites
    if not verify_prerequisites():
        sys.exit(1)
    
    # Run verification only if requested
    if args.verify:
        success = verify_schema_only()
        sys.exit(0 if success else 1)
    
    # Run migrations
    try:
        manager = MigrationManager()
        success = manager.run_all_migrations()
        
        if success:
            logger.info("")
            logger.info("🎉 Database is ready for production!")
            logger.info("")
            logger.info("To start the backend, run:")
            logger.info("  python main.py")
            sys.exit(0)
        else:
            logger.error("")
            logger.error("Please fix the errors above and try again")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
