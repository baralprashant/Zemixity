from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - defaults to SQLite for easy start, can use PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./zemixity.db"  # SQLite fallback for easy setup
)

# Database connection pool settings (PostgreSQL only)
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # seconds

# Create engine with proper connection pooling
if "sqlite" in DATABASE_URL:
    # For SQLite, we need check_same_thread=False
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool  # Disable pooling for SQLite
    )
    print(f" Database: SQLite (in-memory pooling disabled)")
else:
    # For PostgreSQL with connection pooling and reconnection
    engine = create_engine(
        DATABASE_URL,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=DB_POOL_RECYCLE,
        echo=False  # Set to True for SQL debugging
    )
    print(f" Database: PostgreSQL (pool_size={DB_POOL_SIZE}, max_overflow={DB_MAX_OVERFLOW})")

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
