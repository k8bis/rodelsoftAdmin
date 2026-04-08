# apps/app-hija-1/schemas/auth.py
from pydantic import BaseModel


class Login(BaseModel):
    username: str
    password: str


class InternalAccessCheckResponse(BaseModel):
    ok: bool
    user: str
    app_id: int
    client_id: int


class InternalContextInfoResponse(BaseModel):
    ok: bool
    user: str
    app_id: int
    client_id: int
    app_name: str
    client_name: str