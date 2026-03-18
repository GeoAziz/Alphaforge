#!/usr/bin/env python3
"""
Test CORS and PostHog configuration after fixes
"""
import os
import sys
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi.testclient import TestClient
import main

def test_cors_configuration():
    """Test that CORS is properly configured."""
    print("\n" + "="*70)
    print("🧪 CORS CONFIGURATION TEST")
    print("="*70)
    
    client = TestClient(main.app)
    
    # Test 1: Check ALLOWED_ORIGINS
    print(f"\n✅ ALLOWED_ORIGINS: {main.ALLOWED_ORIGINS}")
    assert len(main.ALLOWED_ORIGINS) > 0, "No origins configured"
    assert "https://9205-102-215-79-114.ngrok-free.app" in main.ALLOWED_ORIGINS, "ngrok URL not in origins"
    print("   ✓ ngrok URL present in ALLOWED_ORIGINS")
    
    # Test 2: OPTIONS preflight request from localhost
    print("\n📝 Test: OPTIONS preflight from localhost:9002")
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:9002"}
    )
    print(f"   Status: {response.status_code}")
    cors_header = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
    print(f"   Access-Control-Allow-Origin: {cors_header}")
    assert response.status_code in [200, 405], f"OPTIONS failed: {response.status_code}"
    assert "localhost" in cors_header or cors_header == "*", f"CORS header not set correctly: {cors_header}"
    print("   ✅ Preflight CORS header present")
    
    # Test 3: OPTIONS preflight from ngrok
    print("\n📝 Test: OPTIONS preflight from ngrok")
    response = client.options(
        "/health",
        headers={"Origin": "https://9205-102-215-79-114.ngrok-free.app"}
    )
    print(f"   Status: {response.status_code}")
    cors_header = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
    print(f"   Access-Control-Allow-Origin: {cors_header}")
    assert response.status_code in [200, 405], f"OPTIONS failed: {response.status_code}"
    assert "9205" in cors_header or "*" in cors_header, f"ngrok CORS header not set: {cors_header}"
    print("   ✅ ngrok preflight CORS header present")
    
    # Test 4: Actual GET request with CORS headers (localhost)
    print("\n📝 Test: GET request with CORS headers (localhost)")
    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:9002"}
    )
    print(f"   Status: {response.status_code}")
    cors_header = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
    print(f"   Access-Control-Allow-Origin: {cors_header}")
    assert response.status_code == 200, f"GET failed: {response.status_code}"
    assert "localhost" in cors_header or cors_header == "*", f"CORS header not set on GET: {cors_header}"
    print("   ✅ GET request CORS headers present")
    
    # Test 5: GET request from ngrok
    print("\n📝 Test: GET request with CORS headers (ngrok)")
    response = client.get(
        "/health",
        headers={"Origin": "https://9205-102-215-79-114.ngrok-free.app"}
    )
    print(f"   Status: {response.status_code}")
    cors_header = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
    print(f"   Access-Control-Allow-Origin: {cors_header}")
    assert response.status_code == 200, f"GET failed: {response.status_code}"
    assert "9205" in cors_header or "*" in cors_header, f"ngrok CORS header not set on GET: {cors_header}"
    print("   ✅ ngrok GET request CORS headers present")
    
    print("\n" + "="*70)
    print("✅ ALL CORS TESTS PASSED")
    print("="*70)

def test_posthog_configuration():
    """Test PostHog configuration."""
    print("\n" + "="*70)
    print("🧪 POSTHOG CONFIGURATION TEST")
    print("="*70)
    
    posthog_key = os.getenv("POSTHOG_API_KEY")
    posthog_host = os.getenv("POSTHOG_HOST")
    
    print(f"\n✅ POSTHOG_API_KEY set: {bool(posthog_key)}")
    if posthog_key:
        print(f"   Value: {posthog_key[:20]}...")
        assert posthog_key.startswith(("phc_", "phx_")), "Invalid PostHog key format (should start with phc_ or phx_)"
    
    print(f"✅ POSTHOG_HOST set: {bool(posthog_host)}")
    if posthog_host:
        print(f"   Value: {posthog_host}")
        assert "posthog.com" in posthog_host, f"Invalid PostHog host: {posthog_host}"
    
    print(f"✅ Backend PostHog client: {bool(main.ph)}")
    if main.ph:
        print(f"   ✓ PostHog initialized successfully")
    
    print("\n" + "="*70)
    print("✅ POSTHOG CONFIGURATION VALID")
    print("="*70)

def test_ngrok_configuration():
    """Test ngrok configuration."""
    print("\n" + "="*70)
    print("🧪 NGROK CONFIGURATION TEST")
    print("="*70)
    
    ngrok_url = os.getenv("NGROK_TUNNEL_URL")
    print(f"\n✅ NGROK_TUNNEL_URL env var: {ngrok_url or 'Not set'}")
    print(f"✅ main.ALLOWED_ORIGINS current: {main.ALLOWED_ORIGINS}")
    
    # Check if any origin contains the ngrok domain
    ngrok_found = any("9205-102-215-79-114.ngrok-free.app" in origin for origin in main.ALLOWED_ORIGINS)
    assert ngrok_found, f"ngrok URL not in ALLOWED_ORIGINS. Got: {main.ALLOWED_ORIGINS}"
    print(f"✅ ngrok URL in ALLOWED_ORIGINS")
    
    print("\n" + "="*70)
    print("✅ NGROK CONFIGURATION VALID")
    print("="*70)

if __name__ == "__main__":
    try:
        test_cors_configuration()
        test_posthog_configuration()
        test_ngrok_configuration()
        
        print("\n" + "🎉 "*20)
        print("ALL TESTS PASSED - BACKEND CONFIGURATION FIXED")
        print("🎉 "*20 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
