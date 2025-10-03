from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Thread(Base):
    __tablename__ = "threads"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    session_id = Column(String(10), unique=True, nullable=False)  # Original 7-char session ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user_id = Column(String(100), nullable=True)  # For future auth
    is_pinned = Column(Boolean, default=False)
    share_id = Column(String(12), unique=True, nullable=True)  # For public sharing

    # Relationship to messages
    messages = relationship("Message", back_populates="thread", cascade="all, delete-orphan")

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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

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
