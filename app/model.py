import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.sql import func

from .database import Base


class SenderType(enum.Enum):
    USER = "USER"
    SYSTEM = "SYSTEM"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_uuid = Column(String, nullable=False)
    sender_type = Column(Enum(SenderType), nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
