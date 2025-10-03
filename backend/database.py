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
    "sqlite:///./gemixity.db"  # SQLite fallback for easy setup
)

# Create engine with proper connection pooling
if "sqlite" in DATABASE_URL:
    # For SQLite, we need check_same_thread=False
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool  # Disable pooling for SQLite
    )
else:
    # For PostgreSQL with connection pooling and reconnection
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,  # Number of connections to maintain
        max_overflow=10,  # Maximum overflow connections
        pool_pre_ping=True,  # Verify connections before using them
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False  # Set to True for SQL debugging
    )

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
