from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    email : EmailStr
    first_name: str  = Field(..., min_length=1, max_length=100)
    last_name: str  = Field(..., min_length=1, max_length=100)
    phone: Optional[str]= None
    date_of_birth: Optional[datetime]= None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None    

class UserInDB(UserBase):
    id: str
    role: UserRole
    is_active: bool
    age_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass

    # Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None  # user id
    exp: Optional[int] = None
    type: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str