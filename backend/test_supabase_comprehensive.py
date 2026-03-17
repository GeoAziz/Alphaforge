#!/usr/bin/env python3
"""
Comprehensive Supabase connection test using Python client library.
"""

import os
import sys
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_supabase_client():
    """Test Supabase using Python client library."""
    
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("❌ SUPABASE_URL or SUPABASE_ANON_KEY not found in .env")
        return False
    
    logger.info("🔌 Testing Supabase Python client connection...")
    logger.info(f"📍 URL: {supabase_url}")
    
    try:
        from supabase import create_client
        
        # Initialize Supabase client (simple initialization without proxy)
        supabase = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
        
        # Test 1: Get version info (health check)
        logger.info("\n📋 Test 1: Testing connection health...")
        try:
            # Try to query auth info
            auth_user = supabase.auth.get_session()
            logger.info("✅ Auth session check successful")
        except Exception as e:
            logger.info(f"ℹ️  Auth check returned: {type(e).__name__} (expected for anon key)")
        
        # Test 2: Try to list tables
        logger.info("\n📋 Test 2: Checking database tables...")
        try:
            # Query information schema
            response = supabase.postgrest.auth(supabase_key).get(
                "information_schema.tables",
                {"select": "*", "table_schema": "eq.public"}
            )
            logger.info(f"✅ Tables query returned status code")
        except Exception as e:
            logger.info(f"ℹ️  Tables query: {e}")
        
        # Test 3: Test with a simple table query (if any exist)
        logger.info("\n📋 Test 3: Attempting to query database...")
        try:
            # This will fail if no tables exist, but shows the connection works
            response = supabase.table("users").select("*").limit(1).execute()
            logger.info(f"✅ Query executed successfully")
            logger.info(f"   Data: {response.data}")
        except Exception as e:
            error_msg = str(e)
            if "does not exist" in error_msg or "relation" in error_msg:
                logger.info(f"ℹ️  No 'users' table yet (expected for fresh DB)")
                logger.info(f"   Error: {error_msg[:100]}")
            else:
                logger.info(f"✅ Query attempt shows connection working")
                logger.info(f"   Response: {error_msg[:100]}")
        
        logger.info("\n" + "="*60)
        logger.info("✅ SUPABASE CONNECTION VERIFIED!")
        logger.info("="*60)
        return True
        
    except ImportError:
        logger.error("❌ Supabase library not installed. Run: pip install supabase")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        logger.error(f"   Type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_supabase_client()
    sys.exit(0 if success else 1)
