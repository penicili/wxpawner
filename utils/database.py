from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from config.config import settings

# Construct database URL from settings
DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Configure engine with best practices for MySQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Enables connection health checks
    pool_size=5,  # Number of connections to maintain
    max_overflow=10,  # Max number of connections above pool_size
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

@contextmanager
def get_db():
    """
    Context manager for database sessions.
    Usage:
        with get_db() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise
    finally:
        db.close()
