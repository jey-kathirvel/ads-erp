from pydantic import BaseModel


class LoginSchema(BaseModel):

    email: str

    password: str


class UserCreate(BaseModel):

    full_name: str

    email: str

    password: str