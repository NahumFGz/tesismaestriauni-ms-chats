from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import database, model

app = FastAPI(title="Message API", description="API for managing messages", version="1.0.0")


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=500, description="Message content")


class MessageCreate(MessageBase):
    pass


class MessageUpdate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


@app.post("/messages/", response_model=Message)
async def create_message(message: MessageCreate, db: AsyncSession = Depends(database.get_db)):
    db_message = model.Message(content=message.content)
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


@app.get("/messages/", response_model=List[Message])
async def read_messages(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(database.get_db)
):
    result = await db.execute(select(model.Message).offset(skip).limit(limit))
    messages = result.scalars().all()
    return messages


@app.get("/messages/{message_id}", response_model=Message)
async def read_message(message_id: int, db: AsyncSession = Depends(database.get_db)):
    result = await db.execute(select(model.Message).filter(model.Message.id == message_id))
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@app.put("/messages/{message_id}", response_model=Message)
async def update_message(
    message_id: int, message: MessageUpdate, db: AsyncSession = Depends(database.get_db)
):
    result = await db.execute(select(model.Message).filter(model.Message.id == message_id))
    db_message = result.scalar_one_or_none()

    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    db_message.content = message.content

    await db.commit()
    await db.refresh(db_message)
    return db_message
