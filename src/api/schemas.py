import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AlertCreate(BaseModel):
    name: str
    keywords: list[str] = []
    topic: str | None = None
    use_llm: bool = False
    threshold: float = 0.7


class AlertUpdate(BaseModel):
    name: str | None = None
    keywords: list[str] | None = None
    topic: str | None = None
    use_llm: bool | None = None
    threshold: float | None = None
    is_active: bool | None = None


class AlertResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    keywords: list[str]
    topic: str | None
    use_llm: bool
    threshold: float
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelCreate(BaseModel):
    type: str
    config: dict


class ChannelResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    config: dict
    is_active: bool

    model_config = {"from_attributes": True}
