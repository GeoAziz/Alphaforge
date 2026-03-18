#!/usr/bin/env python3
"""
Simple migration deployment script.
Reads SQL migration and executes it against the database.
"""

import os
import sys
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    # If dotenv not available, try manual loading
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()

def run_migration():
    """Run the migration using raw PostgreSQL connection."""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Installing...")
        os.system("pip install psycopg2-binary")
        import psycopg2
    
    # Database credentials from environment
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("❌ DATABASE_URL not set in .env")
        return False
    
    print("🚀 Starting Recommendations Migration")
    print("=" * 60)
    
    migration_file = Path(__file__).parent.parent / "database" / "recommendations_migration.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print(f"📖 Loaded migration ({len(migration_sql)} bytes)")
        
        # Connect to database
        print("🔗 Connecting to Supabase...")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Execute migration
        print("⚙️  Executing migration...")
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration executed successfully")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('signal_performance', 'external_signal_performance', 'market_correlations', 'user_cache_preferences', 'websocket_connections')
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Created {len(tables)} new tables:")
        for table in sorted(tables):
            print(f"   - {table}")
        
        cursor.close()
        conn.close()
        
        return len(tables) >= 5
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
