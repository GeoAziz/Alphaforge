"""Database initialization and connection management for PostgreSQL.
Direct connection to Supabase PostgreSQL via SQLAlchemy.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from supabase import create_client
from postgrest import SyncPostgrestClient
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Database:
    """Singleton database connection manager for PostgreSQL with mock fallback."""
    
    _instance: 'Database' = None
    _engine = None
    _session_maker = None
    _use_mock = False
    _mock_db = None
    _supabase_client = None

    @property
    def is_mock_mode(self) -> bool:
        return self._use_mock
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize PostgreSQL connection via SQLAlchemy with mock fallback."""
        is_production = os.getenv("API_ENV", "development").lower() == "production"
        allow_mock_fallback = os.getenv("ALLOW_MOCK_DB_FALLBACK", "true").lower() == "true"
        try:
            # Get DATABASE_URL from environment
            database_url = os.getenv("DATABASE_URL")
            
            if not database_url:
                if is_production:
                    raise ValueError("DATABASE_URL environment variable must be set in production")
                if not allow_mock_fallback:
                    raise ValueError("DATABASE_URL environment variable must be set when ALLOW_MOCK_DB_FALLBACK=false")
                raise ValueError("DATABASE_URL environment variable must be set")
            
            logger.info(f"🔗 Connecting to PostgreSQL at {database_url.split('@')[1] if '@' in database_url else 'localhost'}...")
            
            # Create SQLAlchemy engine with connection pooling
            self._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
            
            # Test connection
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✅ PostgreSQL connection successful")
            
            # Create session maker
            self._session_maker = sessionmaker(bind=self._engine, expire_on_commit=False)
            logger.info("✅ Database session factory initialized")

            # Initialize Supabase client for existing table(...) API usage
            raw_supabase_url = os.getenv("SUPABASE_URL")
            raw_supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

            supabase_url = (raw_supabase_url or "").strip().strip('"').strip("'")
            supabase_service_key = (raw_supabase_service_key or "").strip().strip('"').strip("'")

            if supabase_url and supabase_service_key:
                try:
                    client = create_client(supabase_url, supabase_service_key)
                    if client is None:
                        raise RuntimeError("Supabase client creation returned None")

                    self._supabase_client = client
                    logger.info("✅ Supabase client initialized")

                except Exception as supabase_error:
                    key_prefix = supabase_service_key[:20]
                    logger.warning(f"⚠️ supabase-py client init failed ({type(supabase_error).__name__}): {supabase_error}")

                    # New Supabase keys (sb_secret_*/sb_publishable_*) can fail on older supabase-py.
                    # Fallback to direct PostgREST client so table(...) API remains available.
                    if key_prefix.startswith("sb_secret_") or key_prefix.startswith("sb_publishable_"):
                        rest_url = f"{supabase_url.rstrip('/')}/rest/v1"
                        self._supabase_client = SyncPostgrestClient(
                            rest_url,
                            headers={
                                "apikey": supabase_service_key,
                                "Authorization": f"Bearer {supabase_service_key}",
                            },
                        )
                        logger.info("✅ PostgREST client initialized (sb_* key compatibility mode)")
                    else:
                        raise RuntimeError(f"Supabase client initialization failed: {supabase_error}")
            else:
                if is_production:
                    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in production")
                if not allow_mock_fallback:
                    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set when mock fallback is disabled")
                logger.warning("⚠️ SUPABASE_URL or SUPABASE_SERVICE_KEY missing; falling back to mock table client")
                from .mock_db import MockDatabase
                self._mock_db = MockDatabase()
        
        except Exception as e:
            if is_production or not allow_mock_fallback:
                logger.error(f"❌ Production database initialization failed: {e}")
                raise
            logger.warning(f"⚠️ PostgreSQL connection failed: {e}")
            logger.info("📦 Falling back to mock database for MVP testing...")
            self._use_mock = True
            # Import mock database
            from .mock_db import MockDatabase
            mock_db = MockDatabase()
            self._mock_db = mock_db
            logger.info("✅ Mock database initialized")

    def verify_required_tables(self, required_tables: list[str]) -> dict:
        """Verify required tables exist in public schema."""
        if self._engine is None:
            self._initialize()

        if self._use_mock:
            return {
                "ok": False,
                "missing_tables": required_tables,
                "present_tables": [],
                "reason": "mock_mode",
            }

        table_names = []
        with self._engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                )
            )
            table_names = [row[0] for row in result]

        present_set = set(table_names)
        missing = [name for name in required_tables if name not in present_set]

        return {
            "ok": len(missing) == 0,
            "missing_tables": missing,
            "present_tables": sorted(table_names),
        }
    
    @property
    def engine(self):
        """Get SQLAlchemy engine."""
        if self._engine is None:
            self._initialize()
        return self._engine
    
    @property
    def mock_db(self):
        """Get mock database (for fallback)."""
        if self._mock_db is None and not self._use_mock:
            self._initialize()
        return self._mock_db
    
    @property
    def supabase(self):
        """Get Supabase-like object used by service layer."""
        if self._use_mock:
            if self._mock_db is None:
                from .mock_db import MockDatabase
                self._mock_db = MockDatabase()
            return self._mock_db

        if self._supabase_client is not None:
            return self._supabase_client

        if self._mock_db is None:
            from .mock_db import MockDatabase
            self._mock_db = MockDatabase()

        if os.getenv("API_ENV", "development").lower() == "production":
            raise RuntimeError("No available Supabase client in production mode")

        if self._mock_db is None:
            raise RuntimeError("No available Supabase or mock database client")

        return self._mock_db
    
    @property
    def session_maker(self):
        """Get SQLAlchemy session maker."""
        if self._session_maker is None and not self._use_mock:
            self._initialize()
        return self._session_maker
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions."""
        session = self.session_maker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


def get_db() -> Database:
    """Get global database instance."""
    return Database()
