from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type (always 'bearer')")


class SignupRequest(BaseModel):
    email: Annotated[str, Field(..., description="User email address", examples=["user@example.com"])]
    password: Annotated[str, Field(..., min_length=6, description="User password (min 6 chars)")]


class LoginRequest(BaseModel):
    email: Annotated[str, Field(..., description="User email address", examples=["user@example.com"])]
    password: Annotated[str, Field(..., description="User password")]


class TagOut(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class NoteOut(BaseModel):
    id: UUID
    title: str
    content_markdown: str
    is_pinned: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    tags: list[TagOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    title: Annotated[str, Field(default="", description="Note title")]
    content_markdown: Annotated[str, Field(default="", description="Markdown content")]
    is_pinned: Annotated[bool, Field(default=False, description="Whether note is pinned")]
    is_favorite: Annotated[bool, Field(default=False, description="Whether note is favorited")]
    tags: Annotated[list[str], Field(default_factory=list, description="Tag names to apply")]


class NoteUpdate(BaseModel):
    title: Annotated[str | None, Field(default=None, description="New title")]
    content_markdown: Annotated[str | None, Field(default=None, description="New markdown content")]
    is_pinned: Annotated[bool | None, Field(default=None, description="Set pinned")]
    is_favorite: Annotated[bool | None, Field(default=None, description="Set favorite")]
    tags: Annotated[list[str] | None, Field(default=None, description="Replace tags with this list")]


class NotesListResponse(BaseModel):
    items: list[NoteOut]
    total: int
