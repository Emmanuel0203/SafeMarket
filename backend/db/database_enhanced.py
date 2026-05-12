"""
Enhanced database configuration for PostgreSQL
Supports PostgreSQL with connection pooling and best practices
"""

from sqlalchemy import create_engine, pool, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from core import config
import logging

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = config.DATABASE_URL

# Create SQLAlchemy engine with proper connection pooling
if "postgresql" in DATABASE_URL:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        echo=config.SQLALCHEMY_ECHO,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Test connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,
            "application_name": "safemarket_api"
        }
    )
    logger.info(f"✅ PostgreSQL Engine created: {DATABASE_URL.split('@')[1]}")
else:
    # SQLite fallback
    engine = create_engine(
        DATABASE_URL,
        echo=config.SQLALCHEMY_ECHO,
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool
    )
    logger.info(f"✅ SQLite Engine created: {DATABASE_URL}")

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Import Base from models - This import happens AFTER engine creation
from db.models_enhanced import Base


def get_db() -> Session:
    """
    Dependency for getting database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """Test database connection"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ Database connection test PASSED")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection test FAILED: {str(e)}")
        return False


def init_db():
    """Initialize database with schema"""
    try:
        # Test connection first
        if not test_connection():
            raise Exception("Cannot connect to database")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database schema created successfully")
        
        # Seed data if needed
        try:
            from utils.seed import seed_database
            seed_database()
        except Exception as e:
            logger.warning(f"⚠️ Error seeding database: {str(e)}")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise


if __name__ == "__main__":
    init_db()


