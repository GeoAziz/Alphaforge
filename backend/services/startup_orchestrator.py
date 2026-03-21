"""
Startup Orchestrator for AlphaForge Backend
Handles database initialization, service startup, and health verification.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio

from database.migration_manager import MigrationManager

logger = logging.getLogger(__name__)


class StartupOrchestrator:
    """Orchestrates the complete startup sequence."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.status: Dict[str, Any] = {
            "database": {"status": "pending"},
            "migrations": {"status": "pending"},
            "services": {"status": "pending", "services": []}
        }
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    async def verify_database_connection(self) -> bool:
        """Verify database connection is working.
        
        Returns:
            True if database is accessible, False otherwise
        """
        logger.info("🔗 Verifying database connection...")
        try:
            manager = MigrationManager()
            conn = manager.get_connection()
            
            # Simple query to verify connection
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            logger.info("✅ Database connection verified")
            self.status["database"]["status"] = "connected"
            return True
            
        except Exception as e:
            error_msg = f"Failed to connect to database: {e}"
            logger.error(f"❌ {error_msg}")
            self.errors.append(error_msg)
            self.status["database"]["status"] = "failed"
            self.status["database"]["error"] = str(e)
            return False
    
    async def check_migration_status(self) -> bool:
        """Check if migrations have been run.
        
        Returns:
            True if all migrations are complete, False otherwise
        """
        logger.info("🔍 Checking migration status...")
        try:
            manager = MigrationManager()
            conn = manager.get_connection()
            
            # Check Phase 1 tables
            phase1_ok, phase1_missing = manager.verify_tables(
                conn, manager.PHASE_1_TABLES, "phase_1_check"
            )
            
            # Check Phase 2 tables
            phase2_ok, phase2_missing = manager.verify_tables(
                conn, manager.PHASE_2_TABLES, "phase_2_check"
            )
            
            conn.close()
            
            if not phase1_ok:
                self.status["migrations"]["status"] = "incomplete"
                self.status["migrations"]["phase_1"] = {
                    "ok": False,
                    "missing": list(phase1_missing)
                }
                logger.warning(f"⚠️  Phase 1 migration incomplete (missing: {phase1_missing})")
                self.warnings.append(f"Phase 1 tables missing: {phase1_missing}")
            else:
                logger.info("✅ Phase 1 migration verified")
                self.status["migrations"]["phase_1"] = {"ok": True}
            
            if not phase2_ok:
                self.status["migrations"]["status"] = "incomplete"
                self.status["migrations"]["phase_2"] = {
                    "ok": False,
                    "missing": list(phase2_missing)
                }
                logger.warning(f"⚠️  Phase 2 migration incomplete (missing: {phase2_missing})")
                self.warnings.append(f"Phase 2 tables missing: {phase2_missing}")
            else:
                logger.info("✅ Phase 2 migration verified")
                self.status["migrations"]["phase_2"] = {"ok": True}
            
            all_ok = phase1_ok and phase2_ok
            self.status["migrations"]["status"] = "complete" if all_ok else "incomplete"
            return all_ok
            
        except Exception as e:
            error_msg = f"Failed to check migrations: {e}"
            logger.error(f"❌ {error_msg}")
            self.errors.append(error_msg)
            self.status["migrations"]["status"] = "error"
            self.status["migrations"]["error"] = str(e)
            return False
    
    async def run_migrations_if_needed(self) -> bool:
        """Run migrations if they haven't been done yet.
        
        Returns:
            True if migrations completed successfully, False otherwise
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("🔄 Running Database Migrations")
        logger.info("=" * 70)
        
        try:
            manager = MigrationManager()
            success = manager.run_all_migrations()
            
            if success:
                self.status["migrations"]["status"] = "complete"
                logger.info("✅ All migrations completed successfully")
                return True
            else:
                self.errors.append("Migrations failed")
                self.status["migrations"]["status"] = "failed"
                return False
                
        except Exception as e:
            error_msg = f"Migration execution failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.errors.append(error_msg)
            self.status["migrations"]["status"] = "failed"
            self.status["migrations"]["error"] = str(e)
            return False
    
    async def verify_service_imports(self) -> bool:
        """Verify that all required service modules can be imported.
        
        Returns:
            True if all services can be imported, False otherwise
        """
        logger.info("")
        logger.info("📦 Verifying Service Imports...")
        
        required_services = [
            ("services.signal_aggregator_v2", "SignalAggregator"),
            ("services.signal_processor", "SignalProcessor"),
            ("services.paper_trading", "PaperTradingEngine"),
            ("services.portfolio", "PortfolioService"),
            ("services.risk_manager", "RiskManager"),
            ("services.market_data_v2", "MarketDataService"),
            ("services.chat_service", "ChatService"),
            ("services.creator_service", "CreatorVerificationService"),
            ("services.user_service", "UserManagementService"),
            ("services.backtest_service", "BacktestingService"),
            ("services.strategy_service", "StrategyService"),
            ("services.kyc_service", "KYCService"),
            ("services.signal_performance_tracker", "SignalPerformanceTracker"),
            ("services.external_signal_validator", "ExternalSignalPerformanceValidator"),
            ("services.market_correlation_analyzer", "MarketCorrelationAnalyzer"),
        ]
        
        import_errors = []
        services_verified = []
        
        for module_name, class_name in required_services:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                services_verified.append(f"{class_name}")
                logger.debug(f"✅ {class_name}")
            except (ImportError, AttributeError) as e:
                error_msg = f"Failed to import {class_name} from {module_name}: {e}"
                logger.warning(f"⚠️  {error_msg}")
                import_errors.append(error_msg)
        
        self.status["services"]["services"] = services_verified
        
        if import_errors:
            self.warnings.extend(import_errors)
            logger.warning(f"⚠️  {len(import_errors)} services failed to import")
            return False
        
        logger.info(f"✅ All {len(services_verified)} required services verified")
        return True
    
    async def startup(self, auto_migrate: bool = False) -> bool:
        """Run complete startup sequence.
        
        Args:
            auto_migrate: If True, automatically run migrations if needed
            
        Returns:
            True if startup successful, False otherwise
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("🚀 AlphaForge Backend Startup")
        logger.info("=" * 70)
        logger.info(f"⏰ Timestamp: {os.popen('date').read().strip()}")
        logger.info(f"🌍 Environment: {os.getenv('API_ENV', 'development')}")
        
        # 1. Verify database connection
        logger.info("")
        db_ok = await self.verify_database_connection()
        if not db_ok:
            logger.error("❌ Cannot proceed without database connection")
            return False
        
        # 2. Check migration status
        logger.info("")
        migrations_ok = await self.check_migration_status()
        
        # 3. Run migrations if needed
        if not migrations_ok:
            if auto_migrate:
                logger.info("")
                logger.info("🔄 Auto-migration enabled, running migrations...")
                migrations_ok = await self.run_migrations_if_needed()
                
                if not migrations_ok:
                    logger.error("❌ Migrations failed")
                    return False
            else:
                logger.error("")
                logger.error("❌ Migrations are incomplete. Run:")
                logger.error("   python scripts/run_all_migrations.py")
                return False
        
        # 4. Verify service imports
        logger.info("")
        services_ok = await self.verify_service_imports()
        if not services_ok:
            logger.warning("⚠️  Some services may not be available")
            # Don't fail the startup - services may have graceful fallbacks
        
        # Print summary
        self._print_summary()
        
        if self.errors:
            logger.error("")
            logger.error("❌ Startup failed due to errors above")
            return False
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ Backend is ready to start!")
        logger.info("=" * 70)
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of all systems.
        
        Returns:
            Dictionary with health status
        """
        health = {
            "timestamp": str(asyncio.get_event_loop().time()),
            "database": await self.verify_database_connection(),
            "migrations": await self.check_migration_status(),
            "services_available": len(self.status["services"]["services"])
        }
        return health
    
    def _print_summary(self):
        """Print startup summary."""
        logger.info("")
        logger.info("=" * 70)
        logger.info("📋 Startup Summary")
        logger.info("=" * 70)
        
        # Database status
        db_status = self.status["database"]["status"]
        db_icon = "✅" if db_status == "connected" else "❌"
        logger.info(f"{db_icon} Database: {db_status}")
        
        # Migration status
        mig_status = self.status["migrations"]["status"]
        mig_icon = "✅" if mig_status == "complete" else "⏳" if mig_status == "pending" else "❌"
        logger.info(f"{mig_icon} Migrations: {mig_status}")
        
        # Services
        num_services = len(self.status["services"]["services"])
        logger.info(f"📦 Services: {num_services} verified")
        
        # Warnings
        if self.warnings:
            logger.info("")
            logger.info("⚠️  Warnings:")
            for warning in self.warnings:
                logger.info(f"   - {warning}")
        
        # Errors
        if self.errors:
            logger.info("")
            logger.info("❌ Errors:")
            for error in self.errors:
                logger.info(f"   - {error}")
        
        logger.info("")


# Singleton instance
_orchestrator: Optional[StartupOrchestrator] = None


def get_orchestrator() -> StartupOrchestrator:
    """Get or create the startup orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = StartupOrchestrator()
    return _orchestrator
