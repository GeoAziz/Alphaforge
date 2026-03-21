#!/usr/bin/env python3
"""
AlphaForge Quick Start Guide for Deployment
Run this script to get started with database migrations and service initialization.
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def check_env():
    """Check if Python environment is set up correctly."""
    print_header("1️⃣  Checking Environment")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print_error(f"Python 3.9+ required (you have {sys.version})")
        return False
    print_success(f"Python {sys.version.split()[0]} detected")
    
    # Check if in backend directory
    if not Path("main.py").exists():
        print_error("Please run this from the backend/ directory")
        print_info("cd backend")
        return False
    print_success("Running from correct directory")
    
    # Check .env file
    if not Path(".env").exists():
        print_error(".env file not found")
        print_info("Copy .env.example to .env and fill in your values")
        return False
    print_success(".env file found")
    
    # Check DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print_error("DATABASE_URL not set in .env")
        return False
    if len(db_url) > 50:
        db_display = db_url[:30] + "..." + db_url[-20:]
    else:
        db_display = db_url
    print_success(f"DATABASE_URL configured: {db_display}")
    
    return True

def check_database_connection():
    """Check if database is accessible."""
    print_header("2️⃣  Checking Database Connection")
    
    try:
        import psycopg2
        db_url = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(db_url)
        conn.close()
        print_success("Database connection successful")
        return True
    except ImportError:
        print_error("psycopg2 not installed")
        print_info("Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        print_info("Check your DATABASE_URL in .env")
        return False

def check_migrations():
    """Check migration status."""
    print_header("3️⃣  Checking Migration Status")
    
    try:
        from database.migration_manager import MigrationManager
        
        manager = MigrationManager()
        conn = manager.get_connection()
        
        # Check Phase 1
        phase1_ok, phase1_missing = manager.verify_tables(
            conn, manager.PHASE_1_TABLES, "check"
        )
        
        if phase1_ok:
            print_success(f"Phase 1 complete ({len(manager.PHASE_1_TABLES)} tables)")
        else:
            print_warning(f"Phase 1 incomplete ({len(phase1_missing)} tables missing)")
        
        # Check Phase 2
        phase2_ok, phase2_missing = manager.verify_tables(
            conn, manager.PHASE_2_TABLES, "check"
        )
        
        if phase2_ok:
            print_success(f"Phase 2 complete ({len(manager.PHASE_2_TABLES)} tables)")
        else:
            print_warning(f"Phase 2 incomplete ({len(phase2_missing)} tables missing)")
        
        conn.close()
        
        if phase1_ok and phase2_ok:
            print_success("Migrations complete")
            return True
        else:
            print_warning("Migrations incomplete")
            return False
            
    except Exception as e:
        print_error(f"Failed to check migrations: {e}")
        return None  # None means "unknown"

def run_migrations():
    """Run migrations."""
    print_header("4️⃣  Running Migrations")
    
    print_info("Running: python scripts/run_all_migrations.py")
    print_info("This may take a few seconds...")
    
    result = subprocess.run(
        [sys.executable, "scripts/run_all_migrations.py"],
        capture_output=False
    )
    
    return result.returncode == 0

def check_services():
    """Check if all services can be imported."""
    print_header("5️⃣  Verifying Services")
    
    try:
        print_info("Importing FastAPI application...")
        # Don't actually import main.py as it will try to start
        # Just check imports
        from services.signal_aggregator_v2 import SignalAggregator
        from services.market_data_v2 import MarketDataService
        from services.paper_trading import PaperTradingEngine
        from services.kyc_service import KYCService
        
        print_success("All core services importable")
        return True
    except ImportError as e:
        print_error(f"Service import failed: {e}")
        return False

def main():
    print(f"\n{GREEN}🚀 AlphaForge Backend - Quick Start Guide{RESET}\n")
    
    # Run checks
    ok = True
    
    if not check_env():
        ok = False
    
    if ok and not check_database_connection():
        ok = False
    
    if ok:
        migration_check = check_migrations()
        
        if migration_check is False:
            print_info("Migrations needed - running now...")
            if not run_migrations():
                print_error("Migration failed")
                ok = False
        elif migration_check is not True:
            print_warning("Could not determine migration status")
    
    if ok:
        check_services()
    
    # Final summary
    print_header("Summary")
    
    if ok:
        print_success("All checks passed!")
        print_info("")
        print_info("Next steps:")
        print_info("  1. Start backend: python main.py")
        print_info("  2. Backend will be available at: http://localhost:8000")
        print_info("  3. API documentation: http://localhost:8000/docs")
        print_info("  4. Health check: curl http://localhost:8000/health")
    else:
        print_error("Some checks failed - see above for details")
        sys.exit(1)

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Interrupted by user{RESET}")
        sys.exit(1)
