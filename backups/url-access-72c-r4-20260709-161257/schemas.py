from pydantic import BaseModel
from pydantic import EmailStr


class UserCreate(BaseModel):

    full_name: str

    email: EmailStr

    password: str

    role_id: int

    is_active: bool = True


class UserUpdate(BaseModel):

    full_name: str

    email: EmailStr

    role_id: int

    is_active: bool = True


class PasswordReset(BaseModel):

    password: str
