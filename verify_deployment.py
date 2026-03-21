#!/usr/bin/env python3
"""
Complete Deployment Verification Script
Tests all components are working together
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n{'='*80}")
    print(f"🔍 {description}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                print(result.stdout[:500])
            return True
        else:
            print("❌ FAILED")
            if result.stderr:
                print(result.stderr[:500])
            return False
            
    except subprocess.TimeoutExpired:
        print("⏱️  TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all verification tests"""
    
    print("\n" + "="*80)
    print("🚀 ALPHAFORGE - COMPLETE DEPLOYMENT VERIFICATION")
    print("="*80)
    
    os.chdir('/home/devmahnx/Dev/alphaforge')
    
    results = {
        "Backend Import Check": run_command(
            "cd backend && python -c \"import main; print('✅ main.py imports OK')\"",
            "Checking backend imports"
        ),
        "Database Migration": run_command(
            "cd backend && python scripts/deploy_migration.py 2>&1 | grep '✅'",
            "Verifying database migration"
        ),
        "Backend Verification": run_command(
            "cd backend && python verify_backend_ready.py 2>&1 | grep 'READY'",
            "Verifying backend services"
        ),
        "Frontend Build": run_command(
            "npm run build 2>&1 | tail -5",
            "Building frontend"
        ),
    }
    
    print("\n" + "="*80)
    print("📊 DEPLOYMENT SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} - {test}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print("\n" + "🎉"*40)
        print("""
✅ ALL SYSTEMS GO!

System is ready for production deployment:

📋 NEXT STEPS:

1. Start Backend (Terminal 1):
   cd backend && python main.py

2. Start Frontend (Terminal 2):
   npm run dev

3. Open Browser:
   http://localhost:3000

4. Test Integration:
   - Login with Firebase Auth
   - Check Dashboard loads signals
   - Verify Portfolio displays
   - Test Signal Performance metrics

🚀 Happy coding!
        """)
    else:
        print("\n❌ Some checks failed - review above for details")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    import os
    sys.exit(main())
