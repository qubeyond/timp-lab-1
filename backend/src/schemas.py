import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


#  User Schemas

class UserBase(BaseModel):
    username: str = Field(
        ..., 
        min_length=3, 
        max_length=50
    )


class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=6
    )


class UserResponse(UserBase):
    id: uuid.UUID

    created_at: datetime
    last_login: datetime | None
    is_deleted: bool

    model_config = ConfigDict(
        from_attributes=True
    )


# Post Schemas

class PostBase(BaseModel):
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=100
    )
    body: str = Field(
        ..., 
        min_length=10, 
        max_length=500
    )


class PostCreate(PostBase):
    pass


class PostUpdate(PostBase):
    title: str | None = None
    body: str | None = None
    is_published: bool | None = None


class PostResponse(PostBase):
    id: uuid.UUID
    owner_id: uuid.UUID | None

    created_at: datetime
    updated_at: datetime
    # is_published: bool

    model_config = ConfigDict(
        from_attributes=True
    )


# Auth Schemas

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"