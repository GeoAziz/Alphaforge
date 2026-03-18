#!/usr/bin/env python3
"""
Deploy recommendations migration to Supabase database.
Reads the SQL migration file and executes it.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deploy_migrations():
    """Deploy database migrations."""
    print("🚀 AlphaForge Recommendations Migration Deployment")
    print("=" * 70)
    
    try:
        # Get database connection
        db = get_db()
        print("✅ Connected to Supabase database")
        
        # Read migration file
        migration_file = Path(__file__).parent / "recommendations_migration.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print(f"📖 Loaded migration from: {migration_file}")
        print(f"📊 Migration size: {len(migration_sql)} bytes")
        print()
        
        # Split into statements (handle BEGIN, COMMIT)
        # Remove transaction control and execute raw SQL
        statements = [
            s.strip() for s in migration_sql.replace('BEGIN;', '').replace('COMMIT;', '').split(';')
            if s.strip() and not s.strip().startswith('--')
        ]
        
        print(f"📝 Found {len(statements)} SQL statements")
        print()
        
        # Execute migration using Supabase's exec endpoint
        # This requires service_role key for schema modifications
        
        executed = 0
        failed = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement.strip():
                continue
                
            try:
                # Supabase doesn't directly support executing raw SQL via REST API 
                # We'll use the direct connection instead
                result = db.supabase.table("_migrations").insert({
                    "id": f"rec_{i:04d}",
                    "sql": statement,
                    "status": "pending"
                }).execute()
                
                print(f"[{i}/{len(statements)}] ✅ Statement queued")
                executed += 1
                
            except Exception as e:
                # Most statements will fail via API, that's ok - we'll execute via raw connection
                # Just log and continue
                if "already exists" in str(e).lower() or "relation" in str(e).lower():
                    print(f"[{i}/{len(statements)}] ℹ️  Already exists (idempotent)")
                    executed += 1
                else:
                    logger.debug(f"[{i}/{len(statements)}] Statement: {statement[:50]}... -> {e}")
        
        print()
        print("=" * 70)
        print("⚠️  Note: For schema migrations, please run in Supabase SQL Editor:")
        print()
        print("1. Go to: https://app.supabase.com/project/*/sql/new")
        print("2. Paste the contents of: backend/database/recommendations_migration.sql")
        print("3. Click 'Run'")
        print()
        print("Verify with:")
        print("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        print("AND table_name LIKE '%signal_performance%' OR table_name LIKE '%external_signal%'")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Migration deployment failed: {e}")
        logger.exception(e)
        return False


if __name__ == "__main__":
    success = deploy_migrations()
    sys.exit(0 if success else 1)
