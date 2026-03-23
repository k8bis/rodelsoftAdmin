import os
import time
import jwt
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Header, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import Base, engine, get_db

SECRET_KEY = os.getenv("SECRET_KEY", "miclave_secreta")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

app = FastAPI(title="RodelSoft - POS")

Base.metadata.create_all(bind=engine)


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


# Espera a que la DB esté lista (sin tumbar el contenedor)
@app.on_event("startup")
def _startup():
    retries = 20
    for i in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as e:
            if i == retries - 1:
                print(f"[startup] DB no disponible: {e}")
            else:
                print(f"[startup] Esperando DB... intento {i+1}/{retries}")
                time.sleep(2)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        now = db.execute(text("SELECT NOW()")).fetchone()[0]
        return {"status": "ok", "db_time": str(now)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


def resolve_context(
    request: Request,
    x_app_id: int | None,
    x_client_id: int | None,
):
    """
    Prioridad:
    1) Headers (cuando entra por Nginx)
    2) Query params (cuando entra directo por navegador)
    """
    app_id = x_app_id
    client_id = x_client_id

    if app_id is None:
        q = request.query_params.get("app_id")
        if q and q.isdigit():
            app_id = int(q)

    if client_id is None:
        q = request.query_params.get("client_id")
        if q and q.isdigit():
            client_id = int(q)

    return app_id, client_id


def validate_permission(
    db: Session,
    username: str,
    app_id: int,
    client_id: int,
):
    q = text("""
        SELECT 1
        FROM permissions p
        JOIN users u ON u.id = p.user_id
        WHERE u.username = :username
          AND p.app_id = :app_id
          AND p.client_id = :client_id
        LIMIT 1
    """)
    ok = db.execute(
        q,
        {
            "username": username,
            "app_id": app_id,
            "client_id": client_id,
        }
    ).fetchone()

    if not ok:
        raise HTTPException(status_code=403, detail="Sin permiso para esa app/cliente")


@app.get("/")
def root(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)

    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(db, user, app_id, client_id)

    return {
        "message": "RodelSoft - POS funcionando!",
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
        "secured": True,
    }


@app.get("/me")
def me(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)

    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    return {
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
    }


@app.get("/entry")
def entry(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)

    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(db, user, app_id, client_id)

    return {
        "ok": True,
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
        "note": "RodelSoft POS /entry OK",
    }