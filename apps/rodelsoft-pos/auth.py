import os
import jwt
from fastapi import Header, Request, HTTPException

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def verify_token(request: Request, authorization: str | None = Header(default=None)) -> str:
    """
    Devuelve el username del JWT.
    Busca el token primero en Authorization: Bearer ... (inyectado por Nginx),
    y si no existe, intenta leer la cookie 'jwt' (por si llamas directo).
    """
    token = None

    # 1) Header Authorization (preferido; Nginx lo inyecta desde la cookie)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    # 2) Fallback: cookie 'jwt'
    if not token:
        token = request.cookies.get("jwt")

    if not token:
        raise HTTPException(status_code=401, detail="No token")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]  # username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
