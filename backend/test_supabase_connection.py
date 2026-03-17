#!/usr/bin/env python3
"""
Test script to verify Supabase PostgreSQL connection.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_supabase_connection():
    """Test direct PostgreSQL connection to Supabase."""
    
    # Load environment variables
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return False
    
    logger.info("🔌 Testing Supabase PostgreSQL connection...")
    logger.info(f"📍 Database: {database_url.split('@')[1] if '@' in database_url else 'Unknown'}")
    
    try:
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            logger.info("✅ Connection successful!")
            logger.info(f"📦 PostgreSQL version: {version}")
            
            # Get database info
            result = connection.execute(text("""
                SELECT datname, pg_database.datdba, pg_database.encoding
                FROM pg_database
                WHERE datname = current_database()
            """))
            db_info = result.fetchone()
            if db_info:
                logger.info(f"📊 Database name: {db_info[0]}")
                logger.info(f"📊 Encoding: {db_info[2]}")
            
            # Try to list tables
            result = connection.execute(text("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
            """))
            tables = result.fetchall()
            
            if tables:
                logger.info(f"📋 Found {len(tables)} tables:")
                for table in tables:
                    logger.info(f"   - {table[0]}")
            else:
                logger.info("📋 No tables found in public schema (database may be empty)")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {str(e)}")
        logger.error(f"📝 Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
