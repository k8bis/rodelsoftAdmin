# apps/app-hija-1/main.py
import os
import time
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header, Response, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import Base, engine, get_db

SECRET_KEY = os.getenv("SECRET_KEY", "miclave_secreta")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

app = FastAPI(title="App Hija 1 - FastAPI")
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
    # Intenta crear tablas y hacer un SELECT NOW() con reintentos
    retries = 20
    for i in range(retries):
        try:
            Base.metadata.create_all(bind=engine)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as e:
            if i == retries - 1:
                # Ya no reintenta: levanta app pero endpoints darán error controlado
                print(f"[startup] DB no disponible: {e}")
            else:
                print(f"[startup] Esperando DB... intento {i+1}/{retries}")
                time.sleep(2)

class Login(BaseModel):
    username: str
    password: str

@app.get("/")
def root():
    return {"message": "App Hija 1 funcionando!"}

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        now = db.execute(text("SELECT NOW()")).fetchone()[0]
        return {"status": "ok", "db_time": str(now)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

@app.post("/login")
def login(data: Login, response: Response, db: Session = Depends(get_db)):
    q = text("SELECT id FROM users WHERE username=:u AND password=:p")
    user = db.execute(q, {"u": data.username, "p": data.password}).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    payload = {
        "sub": data.username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # COOKIE con el JWT (para que Nginx pueda leerla)
    # HttpOnly para que JS no lo lea; SameSite=Lax para navegación básica
    response.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        samesite="lax",
        path="/"
    )

    return {"status": "ok"}


@app.get("/permissions")
def permissions(user: str = Depends(verify_token), db: Session = Depends(get_db)):
    q = text("""
        SELECT a.id AS app_id, a.name AS app,
               c.id AS client_id, c.name AS client
        FROM permissions p
        JOIN applications a ON p.app_id = a.id
        JOIN clients      c ON p.client_id = c.id
        JOIN users        u ON p.user_id = u.id
        WHERE u.username = :username
        ORDER BY a.name, c.name
    """)
    rows = db.execute(q, {"username": user}).fetchall()
    return [
        {"app_id": r[0], "app": r[1], "client_id": r[2], "client": r[3]}
        for r in rows
    ]

@app.get("/validate")
def validate(request: Request, authorization: str | None = Header(default=None)):
    """
    Usado por Nginx auth_request. Valida JWT desde:
    - Header Authorization: Bearer <token> (si Nginx lo pasa)
    - Cookie 'jwt' (fallback)
    """
    token = None
    # 1) Prioridad: header Authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    # 2) Si no hay header, tomar cookie
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

@app.post("/logout")
def logout(response: Response):
    """
    Elimina la cookie JWT para cerrar sesión.
    """
    response.delete_cookie("jwt", path="/")
    return {"status": "bye"}

@app.get("/me")
def get_me(x_client_name: str = Header(None)):
    return {"cliente_seleccionado": x_client_name}

@app.get("/entry")
def entry(
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    if not x_app_id or not x_client_id:
        raise HTTPException(status_code=400, detail="Faltan X-App-Id o X-Client-Id")
    # Validar que el usuario tenga ese permiso
    q = text("""
      SELECT 1
      FROM permissions p
      JOIN users u ON u.id = p.user_id
      WHERE u.username = :username AND p.app_id = :app_id AND p.client_id = :client_id
      LIMIT 1
    """)
    ok = db.execute(q, {"username": user, "app_id": x_app_id, "client_id": x_client_id}).fetchone()
    if not ok:
        raise HTTPException(status_code=403, detail="Sin permiso para esa app/cliente")
    return {"status":"ok", "user": user, "app_id": x_app_id, "client_id": x_client_id}