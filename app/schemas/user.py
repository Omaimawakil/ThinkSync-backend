from pydantic import BaseModel
from typing import Literal, Optional

Role = Literal["Planner", "Engineering/S&T/TRD", "Admin", "Viewer"]
Department = Literal["Engineering", "S&T", "TRD"]  # only meaningful when role == "Engineering/S&T/TRD"

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: Role
    department: Optional[Department] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    user_id: str

class UserInDB(UserBase):
    user_id: str
    hashed_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
    user_id: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None