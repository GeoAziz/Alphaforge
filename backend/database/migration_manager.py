"""
Database Migration Manager for AlphaForge
Handles schema initialization and management across multiple phases.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import psycopg2
from psycopg2 import sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database schema migrations for AlphaForge."""
    
    # Migration phases in execution order
    MIGRATION_PHASES = [
        ("phase_1", "Phase 1: Core Schema", "supabase_phase1_init.sql"),
        ("phase_2", "Phase 2: Recommendations", "recommendations_migration.sql"),
    ]
    
    # Core tables that must exist after Phase 1
    PHASE_1_TABLES = [
        'users', 'signals', 'paper_trades', 'positions', 'portfolios',
        'creator_profiles', 'creator_strategies', 'strategy_subscriptions',
        'kyc_verifications', 'audit_logs', 'external_signals',
        'external_signal_rules', 'api_keys', 'backtests',
        'chat_messages', 'notifications', 'user_risk_settings', 'strategies'
    ]
    
    # Recommendation tables that must exist after Phase 2
    PHASE_2_TABLES = [
        'signal_performance', 'external_signal_performance',
        'market_correlations', 'user_cache_preferences', 'websocket_connections'
    ]
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize migration manager.
        
        Args:
            database_url: PostgreSQL connection string. If None, uses DATABASE_URL env var.
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set or provided")
        
        self.migrations_dir = Path(__file__).parent
        self.migration_status: Dict[str, Dict] = {}
        
    def get_connection(self):
        """Get a database connection."""
        try:
            conn = psycopg2.connect(self.database_url)
            return conn
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    def read_migration_file(self, filename: str) -> str:
        """Read migration SQL file.
        
        Args:
            filename: Name of the SQL file in the migrations directory
            
        Returns:
            SQL content as string
        """
        filepath = self.migrations_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Migration file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse_sql_statements(self, sql_content: str) -> List[str]:
        """Parse SQL content into individual statements.
        
        Handles:
        - Transaction control (BEGIN, COMMIT, ROLLBACK)
        - Multi-line statements
        - Comments
        
        Args:
            sql_content: Raw SQL content
            
        Returns:
            List of individual SQL statements
        """
        # Remove transaction control
        sql_content = sql_content.replace('BEGIN;', '').replace('COMMIT;', '')
        sql_content = sql_content.replace('BEGIN', '').replace('COMMIT', '')
        
        # Split by semicolon
        statements = sql_content.split(';')
        
        # Filter and clean
        cleaned = []
        for stmt in statements:
            stmt = stmt.strip()
            
            # Skip empty statements and comments
            if not stmt or stmt.startswith('--'):
                continue
            
            # Skip lines that are only comments
            lines = [line.strip() for line in stmt.split('\n') 
                    if line.strip() and not line.strip().startswith('--')]
            
            if lines:
                cleaned.append('\n'.join(lines))
        
        return cleaned
    
    def execute_migration(self, conn, statements: List[str], phase_name: str) -> Tuple[bool, int, List[str]]:
        """Execute migration statements.
        
        Args:
            conn: Database connection
            statements: List of SQL statements
            phase_name: Name of the migration phase (for logging)
            
        Returns:
            Tuple of (success, num_executed, errors)
        """
        cursor = conn.cursor()
        executed = 0
        errors = []
        
        try:
            for i, statement in enumerate(statements, 1):
                try:
                    cursor.execute(statement)
                    executed += 1
                    logger.debug(f"[{phase_name}] Statement {i}/{len(statements)} executed")
                except psycopg2.Error as e:
                    error_msg = f"[{phase_name}] Statement {i} failed: {e}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    # Continue to next statement
                    conn.rollback()
                    cursor = conn.cursor()
            
            conn.commit()
            logger.info(f"✅ [{phase_name}] Committed {executed}/{len(statements)} statements")
            return True, executed, errors
            
        except Exception as e:
            logger.error(f"❌ [{phase_name}] Migration failed: {e}")
            conn.rollback()
            return False, executed, [str(e)]
        finally:
            cursor.close()
    
    def verify_tables(self, conn, expected_tables: List[str], phase_name: str) -> Tuple[bool, List[str]]:
        """Verify that expected tables exist.
        
        Args:
            conn: Database connection
            expected_tables: List of table names to check
            phase_name: Name of the phase (for logging)
            
        Returns:
            Tuple of (all_exist, missing_tables)
        """
        cursor = conn.cursor()
        try:
            # Query information_schema
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname='public' 
                AND tablename = ANY(%s)
                ORDER BY tablename
            """, (expected_tables,))
            
            existing = [row[0] for row in cursor.fetchall()]
            missing = set(expected_tables) - set(existing)
            
            if missing:
                logger.warning(f"⚠️  [{phase_name}] Missing tables: {missing}")
                return False, list(missing)
            else:
                logger.info(f"✅ [{phase_name}] All {len(expected_tables)} tables verified")
                return True, []
        finally:
            cursor.close()
    
    def get_table_count(self, conn) -> int:
        """Get total number of tables in public schema."""
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM pg_tables WHERE schemaname='public'
            """)
            return cursor.fetchone()[0]
        finally:
            cursor.close()
    
    def run_migration(self, phase_name: str, phase_display: str, sql_filename: str) -> bool:
        """Run a single migration phase.
        
        Args:
            phase_name: Internal phase name (e.g., "phase_1")
            phase_display: Display name (e.g., "Phase 1: Core Schema")
            sql_filename: SQL filename in migrations directory
            
        Returns:
            True if migration succeeded, False otherwise
        """
        logger.info("=" * 70)
        logger.info(f"🔄 Running {phase_display}")
        logger.info("=" * 70)
        
        try:
            # Connect to database
            conn = self.get_connection()
            logger.info(f"✅ Connected to PostgreSQL")
            
            # Read migration file
            sql_content = self.read_migration_file(sql_filename)
            logger.info(f"📖 Loaded {sql_filename} ({len(sql_content)} bytes)")
            
            # Parse statements
            statements = self.parse_sql_statements(sql_content)
            logger.info(f"📝 Parsed {len(statements)} SQL statements")
            
            # Show initial table count
            initial_count = self.get_table_count(conn)
            logger.info(f"📊 Initial table count: {initial_count}")
            
            # Execute migration
            success, executed, errors = self.execute_migration(conn, statements, phase_name)
            
            if not success:
                logger.error(f"❌ Migration failed to execute")
                self.migration_status[phase_name] = {
                    "status": "failed",
                    "executed": executed,
                    "total": len(statements),
                    "errors": errors
                }
                conn.close()
                return False
            
            # Show final table count
            final_count = self.get_table_count(conn)
            tables_added = final_count - initial_count
            logger.info(f"📊 Final table count: {final_count} (+{tables_added})")
            
            # Verify expected tables
            expected_tables = self.PHASE_1_TABLES if phase_name == "phase_1" else self.PHASE_2_TABLES
            all_exist, missing = self.verify_tables(conn, expected_tables, phase_name)
            
            conn.close()
            
            if not all_exist:
                logger.error(f"❌ Missing tables: {missing}")
                self.migration_status[phase_name] = {
                    "status": "failed",
                    "reason": "Table verification failed",
                    "missing_tables": missing
                }
                return False
            
            # Record success
            self.migration_status[phase_name] = {
                "status": "success",
                "executed": executed,
                "total": len(statements),
                "tables_added": tables_added,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ {phase_display} completed successfully")
            logger.info("")
            return True
            
        except Exception as e:
            logger.error(f"❌ {phase_display} failed: {e}")
            self.migration_status[phase_name] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def run_all_migrations(self) -> bool:
        """Run all migration phases in order.
        
        Returns:
            True if all migrations succeeded, False otherwise
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("🚀 AlphaForge Database Migration")
        logger.info("=" * 70)
        logger.info(f"📍 Database: {self.database_url.split('/')[-1]}")
        logger.info("")
        
        all_success = True
        for phase_name, phase_display, sql_filename in self.MIGRATION_PHASES:
            success = self.run_migration(phase_name, phase_display, sql_filename)
            if not success:
                all_success = False
                # Continue to try next phase
        
        # Summary
        logger.info("=" * 70)
        logger.info("📋 Migration Summary")
        logger.info("=" * 70)
        for phase_name, phase_display, _ in self.MIGRATION_PHASES:
            status_info = self.migration_status.get(phase_name, {})
            status = status_info.get("status", "unknown")
            
            if status == "success":
                executed = status_info.get("executed", "?")
                tables_added = status_info.get("tables_added", "?")
                logger.info(f"✅ {phase_display}: {executed} statements, {tables_added} tables")
            elif status == "failed":
                reason = status_info.get("reason", status_info.get("error", "Unknown error"))
                logger.info(f"❌ {phase_display}: {reason}")
            else:
                logger.info(f"⏳ {phase_display}: Not executed")
        
        if all_success:
            logger.info("")
            logger.info("=" * 70)
            logger.info("✅ All migrations completed successfully!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Next steps:")
            logger.info("1. Verify tables in Supabase Dashboard")
            logger.info("2. Run backend: python main.py")
            logger.info("3. Test APIs: python scripts/test_endpoints.sh")
        else:
            logger.info("")
            logger.info("=" * 70)
            logger.info("❌ Some migrations failed")
            logger.info("=" * 70)
        
        return all_success
