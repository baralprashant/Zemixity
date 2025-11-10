"""
Database optimizer - Adds indexes and optimizations for better performance
Run this script after the initial database setup
"""

from sqlalchemy import Index, text
from database import engine, SessionLocal
from models import Thread, Message, Base
import os
from dotenv import load_dotenv

load_dotenv()


def optimize_database():
    """Add indexes and optimizations to the database"""

    print("🔧 Starting database optimization...")

    db = SessionLocal()

    try:
        # Create indexes for better query performance
        indexes = [
            # Thread indexes
            ("idx_threads_session_id", "threads", ["session_id"]),
            ("idx_threads_updated_at", "threads", ["updated_at DESC"]),
            ("idx_threads_created_at", "threads", ["created_at DESC"]),
            ("idx_threads_user_id", "threads", ["user_id"]),  # For future auth
            ("idx_threads_share_id", "threads", ["share_id"]),
            ("idx_threads_is_pinned", "threads", ["is_pinned", "updated_at DESC"]),

            # Message indexes
            ("idx_messages_thread_id", "messages", ["thread_id"]),
            ("idx_messages_created_at", "messages", ["created_at ASC"]),
            ("idx_messages_thread_created", "messages", ["thread_id", "created_at ASC"]),
            ("idx_messages_role", "messages", ["role"]),
        ]

        for index_name, table_name, columns in indexes:
            try:
                # Check if index already exists
                result = db.execute(text(f"""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name='{index_name}'
                """))

                if result.fetchone():
                    print(f"  ✓ Index {index_name} already exists")
                    continue

                # Create index
                columns_str = ", ".join(columns)
                db.execute(text(f"""
                    CREATE INDEX {index_name} ON {table_name} ({columns_str})
                """))
                print(f"   Created index: {index_name} on {table_name}({columns_str})")

            except Exception as e:
                print(f"  ⚠️  Could not create index {index_name}: {e}")

        db.commit()

        # Analyze database for query optimization
        print("\n📊 Analyzing database for query optimization...")
        db.execute(text("ANALYZE"))
        db.commit()
        print("   Database analysis complete")

        # Vacuum database to reclaim space (SQLite specific)
        print("\n🧹 Vacuuming database...")
        db.execute(text("VACUUM"))
        print("   Database vacuumed")

        print("\n Database optimization complete!")

    except Exception as e:
        print(f" Error during optimization: {e}")
        db.rollback()
    finally:
        db.close()


def get_database_stats():
    """Get database statistics"""
    db = SessionLocal()

    try:
        print("\n📊 Database Statistics:")
        print("=" * 50)

        # Count threads
        thread_count = db.execute(text("SELECT COUNT(*) FROM threads")).scalar()
        print(f"  Threads: {thread_count}")

        # Count messages
        message_count = db.execute(text("SELECT COUNT(*) FROM messages")).scalar()
        print(f"  Messages: {message_count}")

        # Count pinned threads
        pinned_count = db.execute(text("SELECT COUNT(*) FROM threads WHERE is_pinned = 1")).scalar()
        print(f"  Pinned threads: {pinned_count}")

        # Count shared threads
        shared_count = db.execute(text("SELECT COUNT(*) FROM threads WHERE share_id IS NOT NULL")).scalar()
        print(f"  Shared threads: {shared_count}")

        # Database size (SQLite specific)
        db_size = db.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")).scalar()
        db_size_mb = db_size / (1024 * 1024) if db_size else 0
        print(f"  Database size: {db_size_mb:.2f} MB")

        # List all indexes
        print("\n  Indexes:")
        indexes = db.execute(text("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")).fetchall()
        for idx_name, tbl_name in indexes:
            print(f"    - {idx_name} on {tbl_name}")

        print("=" * 50)

    except Exception as e:
        print(f" Error getting stats: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Database Optimization Tool")
    print()

    # Show current stats
    get_database_stats()

    # Run optimization
    optimize_database()

    # Show updated stats
    get_database_stats()