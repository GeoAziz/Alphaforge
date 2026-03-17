"""Database initialization and connection management for PostgreSQL.
Direct connection to Supabase PostgreSQL via SQLAlchemy.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from supabase import create_client, Client
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
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize PostgreSQL connection via SQLAlchemy with mock fallback."""
        is_production = os.getenv("API_ENV", "development").lower() == "production"
        try:
            # Get DATABASE_URL from environment
            database_url = os.getenv("DATABASE_URL")
            
            if not database_url:
                if is_production:
                    raise ValueError("DATABASE_URL environment variable must be set in production")
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
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

            if supabase_url and supabase_service_key:
                client = create_client(supabase_url, supabase_service_key)
                if client is not None:
                    self._supabase_client = client
                    logger.info("✅ Supabase client initialized")
                else:
                    if is_production:
                        raise RuntimeError("Supabase client creation returned None in production")
                    logger.warning("⚠️ Supabase client creation returned None; falling back to mock table client")
                    from .mock_db import MockDatabase
                    self._mock_db = MockDatabase()
            else:
                if is_production:
                    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in production")
                logger.warning("⚠️ SUPABASE_URL or SUPABASE_SERVICE_KEY missing; falling back to mock table client")
                from .mock_db import MockDatabase
                self._mock_db = MockDatabase()
        
        except Exception as e:
            if is_production:
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
