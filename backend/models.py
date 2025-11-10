from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Boolean, Enum as SQLEnum, Integer, Date, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, date
import uuid
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Thread(Base):
    __tablename__ = "threads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    session_id = Column(String(10), unique=True, nullable=False)  # Original 7-char session ID
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # User isolation fields
    user_id = Column(String(100), nullable=False, index=True)  # Browser user ID or IP address
    is_browser_user = Column(Boolean, default=False, nullable=False)  # True = pro tier, False = free tier

    is_pinned = Column(Boolean, default=False)
    share_id = Column(String(12), unique=True, nullable=True)  # For public sharing

    # Relationship to messages
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")

    # Create index for user_id filtering
    __table_args__ = (
        Index('idx_threads_user_id', 'user_id'),
        Index('idx_threads_user_updated', 'user_id', 'updated_at'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_pinned": self.is_pinned,
            "message_count": len(self.messages) if self.messages else 0
        }

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    thread_id = Column(String(36), ForeignKey('threads.id', ondelete='CASCADE'), nullable=False)
    role = Column(SQLEnum('user', 'assistant', name='message_role'), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # Array of source objects
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to thread
    thread = relationship("Thread", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class RateLimit(Base):
    """Track daily search limits for free tier users (IP-based)"""
    __tablename__ = "rate_limits"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    ip_address = Column(String(45), nullable=False)  # IPv6 compatible
    search_count = Column(Integer, default=0, nullable=False)
    date = Column(Date, default=lambda: datetime.now(timezone.utc).date(), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Create composite index for efficient lookups
    __table_args__ = (
        Index('idx_rate_limit_ip_date', 'ip_address', 'date'),
    )
