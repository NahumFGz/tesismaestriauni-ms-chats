import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class SenderType(enum.Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    chat_uuid = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=True)
    user_id = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con Message
    messages = relationship("Message", back_populates="chat")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_uuid = Column(String, ForeignKey("chats.chat_uuid"), nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relación con Chat
    chat = relationship("Chat", back_populates="messages")
