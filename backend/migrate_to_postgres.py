#!/usr/bin/env python3
"""
Migration script to copy data from SQLite to PostgreSQL
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Thread, Message, Base
from dotenv import load_dotenv

load_dotenv()

# Source (SQLite)
SQLITE_URL = "sqlite:///./gemixity.db"

# Target (PostgreSQL from .env)
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL or "sqlite" in POSTGRES_URL:
    print("❌ Please set DATABASE_URL to your PostgreSQL connection string in .env")
    exit(1)

def migrate():
    print("🔄 Starting migration from SQLite to PostgreSQL...")

    # Connect to SQLite (source)
    sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()

    # Connect to PostgreSQL (target)
    postgres_engine = create_engine(POSTGRES_URL)
    PostgresSession = sessionmaker(bind=postgres_engine)
    postgres_session = PostgresSession()

    try:
        # Create tables in PostgreSQL
        print("📋 Creating tables in PostgreSQL...")
        Base.metadata.create_all(bind=postgres_engine)

        # Migrate Threads
        threads = sqlite_session.query(Thread).all()
        print(f"📦 Migrating {len(threads)} threads...")

        for thread in threads:
            # Check if thread already exists
            exists = postgres_session.query(Thread).filter_by(id=thread.id).first()
            if not exists:
                postgres_session.add(Thread(
                    id=thread.id,
                    title=thread.title,
                    session_id=thread.session_id,
                    created_at=thread.created_at,
                    updated_at=thread.updated_at,
                    user_id=thread.user_id,
                    is_pinned=thread.is_pinned,
                    share_id=thread.share_id
                ))

        postgres_session.commit()
        print("✅ Threads migrated")

        # Migrate Messages
        messages = sqlite_session.query(Message).all()
        print(f"💬 Migrating {len(messages)} messages...")

        for msg in messages:
            # Check if message already exists
            exists = postgres_session.query(Message).filter_by(id=msg.id).first()
            if not exists:
                postgres_session.add(Message(
                    id=msg.id,
                    thread_id=msg.thread_id,
                    role=msg.role,
                    content=msg.content,
                    sources=msg.sources,
                    created_at=msg.created_at
                ))

        postgres_session.commit()
        print("✅ Messages migrated")

        print("\n🎉 Migration completed successfully!")
        print(f"   Threads: {len(threads)}")
        print(f"   Messages: {len(messages)}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        postgres_session.rollback()
        raise
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    migrate()
