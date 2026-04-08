# apps/app-hija-1/core/auth.py
import os
import jwt
import bcrypt
from datetime import datetime, timedelta

from fastapi import Depends, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))


def verify_token(request: Request, authorization: str | None = Header(default=None)) -> str:
    """
    Devuelve el username del JWT.
    Busca el token primero en Authorization: Bearer ... (inyectado por Nginx),
    y si no existe, intenta leer la cookie 'jwt' (por si llamas directo).
    """
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        token = request.cookies.get("jwt")

    if not token:
        raise HTTPException(status_code=401, detail="No token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def is_bcrypt_hash(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith("$2a$") or value.startswith("$2b$") or value.startswith("$2y$")


def verify_password_and_upgrade(db: Session, username: str, plain_password: str):
    q = text("SELECT id, password FROM users WHERE username=:u LIMIT 1")
    row = db.execute(q, {"u": username}).mappings().first()

    if not row:
        return None

    user_id = row["id"]
    stored_password = row["password"] or ""

    if is_bcrypt_hash(stored_password):
        try:
            if bcrypt.checkpw(plain_password.encode("utf-8"), stored_password.encode("utf-8")):
                return user_id
            return None
        except Exception:
            return None

    if stored_password == plain_password:
        new_hash = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        db.execute(
            text("UPDATE users SET password=:p WHERE id=:id"),
            {"p": new_hash, "id": user_id}
        )
        db.commit()

        print(f"[auth] Password legacy migrado a bcrypt para user_id={user_id}")
        return user_id

    return None


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def validate_token_from_request(request: Request, authorization: str | None = Header(default=None)):
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        token = request.cookies.get("jwt")

    if not token:
        raise HTTPException(status_code=401, detail="No token")

    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"status": "ok"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def _build_logout_response() -> RedirectResponse:
    """
    Cierra sesión real:
    - elimina cookie JWT
    - redirige al login del portal (/)
    """
    response = RedirectResponse(url="/", status_code=302)

    response.delete_cookie(
        key="jwt",
        path="/",
        httponly=True,
        samesite="lax"
    )

    return response