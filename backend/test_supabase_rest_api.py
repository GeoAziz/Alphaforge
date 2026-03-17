#!/usr/bin/env python3
"""
Test Supabase connection using REST API instead of direct PostgreSQL.
"""

import os
import sys
import requests
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_supabase_rest_api():
    """Test Supabase using REST API."""
    
    load_dotenv()
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_anon_key:
        logger.error("❌ SUPABASE_URL or SUPABASE_ANON_KEY not found in .env")
        return False
    
    logger.info("🔌 Testing Supabase REST API connection...")
    logger.info(f"📍 URL: {supabase_url}")
    
    try:
        # Test health/auth endpoint
        headers = {
            "Authorization": f"Bearer {supabase_anon_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{supabase_url}/rest/v1/", headers=headers, timeout=5)
        logger.info(f"📊 Response Status: {response.status_code}")
        
        if response.status_code in [200, 401, 403]:  # Any response means connection works
            logger.info("✅ REST API connection successful!")
            logger.info(f"📦 Response: {response.text[:200]}")
            return True
        else:
            logger.error(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_supabase_rest_api()
    sys.exit(0 if success else 1)
