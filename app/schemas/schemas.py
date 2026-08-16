from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer, field_validator


class AuthorOut(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)

class PostCreate(BaseModel):
    title:str
    description: Optional[str] = None
    content: str

class PostOut(BaseModel):
    id: int
    author_id: int
    title: str
    description: Optional[str] = None
    author: AuthorOut

    model_config = ConfigDict(from_attributes=True)

#* ================================COMMENTS================

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None

    @field_validator("parent_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, v):
        if v == 0:
            return None
        return v

class CommentOut(BaseModel):
    id: int
    post_id: int
    author_id: int
    content: str
    parent_id: Optional[int] = None
    created_at: datetime
    is_deleted: bool = False
    author: AuthorOut
    replies: list["CommentOut"] = []

    model_config = ConfigDict(from_attributes=True)


#* =================================AUTH======================================
class RegistrData(BaseModel):
    name: str
    surname: Optional[str] = None 
    username: str
    email: EmailStr 
    password: str

    model_config = ConfigDict(from_attributes=True)

class RegistrResponse(BaseModel):
    name: str
    surname: Optional[str] = None 
    username: str
    email: EmailStr 

    @field_serializer("email")
    @staticmethod
    def mask_email(email: str) -> str:
        if "@" not in email:
            return email
        local, domain = email.rsplit("@", 1)
        return local[0] + "*" * (len(local) - 1) + f"@{domain}"

    model_config = ConfigDict(from_attributes=True)

class LoginData(BaseModel):
    email: EmailStr
    password: str

#* ===============================TOKENS=======================================
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

class RefreshRequest(BaseModel):
    refresh_token: str