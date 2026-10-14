from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    workspace_name: str = Field(min_length=2, max_length=120)

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    timezone: str

class UserOut(BaseModel):
    id: str
    email: str
    workspaces: list[WorkspaceOut]

class DraftInput(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    caption: str = Field(min_length=1, max_length=3000)
    source_url: HttpUrl

class DraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    workspace_id: str
    title: str
    caption: str
    source_url: str
    status: str
    created_at: datetime
