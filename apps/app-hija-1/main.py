# apps/app-hija-1/main.py
import os
import time
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header, Response, Request
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import Base, engine, get_db

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "120"))

app = FastAPI(title="App Hija 1 - FastAPI")

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

def has_permission(db: Session, username: str, app_id: int, client_id: int) -> bool:
    q = text("""
        SELECT 1
        FROM permissions p
        JOIN users u ON u.id = p.user_id
        WHERE u.username = :username
          AND p.app_id = :app_id
          AND p.client_id = :client_id
        LIMIT 1
    """)
    row = db.execute(q, {
        "username": username,
        "app_id": app_id,
        "client_id": client_id
    }).fetchone()
    return row is not None

def has_active_membership(db: Session, username: str, client_id: int) -> bool:
    q = text("""
        SELECT 1
        FROM user_client_memberships ucm
        JOIN users u ON u.id = ucm.user_id
        WHERE u.username = :username
          AND ucm.client_id = :client_id
          AND ucm.status = 'active'
        LIMIT 1
    """)
    row = db.execute(q, {
        "username": username,
        "client_id": client_id
    }).fetchone()
    return row is not None

def has_active_subscription(db: Session, client_id: int, app_id: int) -> bool:
    q = text("""
        SELECT 1
        FROM client_app_subscriptions s
        WHERE s.client_id = :client_id
          AND s.app_id = :app_id
          AND s.is_enabled = 1
          AND s.status IN ('trial', 'active')
          AND (s.end_date IS NULL OR s.end_date >= NOW())
        LIMIT 1
    """)
    row = db.execute(q, {
        "client_id": client_id,
        "app_id": app_id
    }).fetchone()
    return row is not None

def redirect_to_portal_with_message(message: str, level: str = "warning") -> RedirectResponse:
    """
    Redirige al portal principal (/) con mensaje UX amigable.
    El portal ya lee ?msg=...; añadimos también msg_type por compatibilidad futura.
    """
    qs = urlencode({
        "msg": message,
        "msg_type": level
    })
    return RedirectResponse(url=f"/?{qs}", status_code=302)

# Espera a que la DB esté lista (sin tumbar el contenedor)
@app.on_event("startup")
def _startup():
    # Intenta crear tablas y hacer un SELECT NOW() con reintentos
    retries = 20
    for i in range(retries):
        try:
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
def root(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    """
    Endpoint browser-friendly:
    - Si falta autenticación o el acceso no es válido, redirige al portal con mensaje amigable.
    - Mantiene la seguridad real en backend.
    """
    token = None

    # 1) Header Authorization (preferido; Nginx lo inyecta desde la cookie)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    # 2) Fallback: cookie 'jwt'
    if not token:
        token = request.cookies.get("jwt")

    if not token:
        return redirect_to_portal_with_message(
            "Tu sesión no está activa. Inicia sesión para continuar.",
            "warning"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user = payload["sub"]
    except jwt.ExpiredSignatureError:
        return redirect_to_portal_with_message(
            "Tu sesión expiró. Inicia sesión nuevamente.",
            "warning"
        )
    except jwt.InvalidTokenError:
        return redirect_to_portal_with_message(
            "Tu sesión no es válida. Inicia sesión nuevamente.",
            "warning"
        )

    app_id = x_app_id
    client_id = x_client_id

    # fallback: query params si entran directo
    if app_id is None:
        q = request.query_params.get("app_id")
        if q and q.isdigit():
            app_id = int(q)

    if client_id is None:
        q = request.query_params.get("client_id")
        if q and q.isdigit():
            client_id = int(q)

    if not app_id or not client_id:
        return redirect_to_portal_with_message(
            "No se pudo abrir la aplicación porque faltan datos de contexto.",
            "warning"
        )

    if not has_active_membership(db, user, client_id):
        return redirect_to_portal_with_message(
            "Tu usuario no tiene membresía activa para el cliente seleccionado.",
            "warning"
        )

    if not has_permission(db, user, app_id, client_id):
        return redirect_to_portal_with_message(
            "No tienes permiso para acceder a esta aplicación con el cliente seleccionado.",
            "warning"
        )

    if not has_active_subscription(db, client_id, app_id):
        return redirect_to_portal_with_message(
            "La suscripción de esta aplicación no está activa para el cliente seleccionado.",
            "warning"
        )

    return {
        "message": "App Hija 1 funcionando!",
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
        "secured": True
    }

@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        now = db.execute(text("SELECT NOW()")).fetchone()[0]
        return {"status": "ok", "db_time": str(now)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

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

    # Caso 1: password ya hasheado (bcrypt)
    if is_bcrypt_hash(stored_password):
        try:
            if bcrypt.checkpw(plain_password.encode("utf-8"), stored_password.encode("utf-8")):
                return user_id
            return None
        except Exception:
            return None

    # Caso 2: legado en texto plano
    if stored_password == plain_password:
        # Upgrade automático a bcrypt
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

@app.post("/login")
def login(data: Login, response: Response, db: Session = Depends(get_db)):
    user_id = verify_password_and_upgrade(db, data.username, data.password)

    if not user_id:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    payload = {
        "sub": data.username,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    response.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        samesite="lax",
        path="/"
    )

    return {"status": "ok", "access_token": token, "token_type": "bearer"}

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

@app.api_route("/logout", methods=["GET", "POST"])
def logout():
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

@app.get("/me")
def get_me(
    user: str = Depends(verify_token),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    return {"user": user, "app_id": x_app_id, "client_id": x_client_id}

@app.get("/my/apps")
def my_apps(user: str = Depends(verify_token), db: Session = Depends(get_db)):
    q = text("""
        SELECT
            a.id AS app_id,
            a.name AS app,
            a.slug AS slug,
            a.description AS description,
            a.public_url AS public_url,
            a.entry_path AS entry_path,
            a.launch_mode AS launch_mode,
            c.id AS client_id,
            c.name AS client,
            s.status AS subscription_status,
            s.start_date AS subscription_start_date,
            s.end_date AS subscription_end_date,
            s.is_enabled AS subscription_enabled
        FROM permissions p
        JOIN users u
        ON p.user_id = u.id
        JOIN user_client_memberships ucm
        ON ucm.user_id = u.id
        AND ucm.client_id = p.client_id
        AND ucm.status = 'active'
        JOIN applications a
        ON p.app_id = a.id
        JOIN clients c
        ON p.client_id = c.id
        LEFT JOIN client_app_subscriptions s
        ON s.client_id = p.client_id
        AND s.app_id = p.app_id
        WHERE u.username = :username
        ORDER BY a.name, c.name
    """)
    rows = db.execute(q, {"username": user}).mappings().all()

    grouped = {}
    now = datetime.utcnow()

    for row in rows:
        app_id = row["app_id"]

        if app_id not in grouped:
            grouped[app_id] = {
                "app_id": row["app_id"],
                "app": row["app"],
                "slug": row["slug"],
                "description": row["description"],
                "public_url": row["public_url"],
                "entry_path": row["entry_path"] or "/",
                "launch_mode": row["launch_mode"] or "redirect",
                "clients": [],
            }

        # Estado contractual proyectado
        raw_status = row["subscription_status"]
        status = raw_status.strip().lower() if raw_status else "missing"

        start_date = row["subscription_start_date"]
        end_date = row["subscription_end_date"]
        subscription_enabled = bool(row["subscription_enabled"]) if row["subscription_enabled"] is not None else False

        # Expira pronto: 0 a 7 días
        is_expiring_soon = False
        if end_date:
            try:
                if hasattr(end_date, "hour"):
                    delta_days = (end_date - now).days
                    is_not_expired = end_date >= now
                else:
                    delta_days = (end_date - now.date()).days
                    is_not_expired = end_date >= now.date()

                if is_not_expired and 0 <= delta_days <= 7:
                    is_expiring_soon = True
            except Exception:
                is_expiring_soon = False

        # Acceso efectivo
        if end_date:
            if hasattr(end_date, "hour"):
                not_expired = end_date >= now
            else:
                not_expired = end_date >= now.date()
        else:
            not_expired = True

        is_accessible = (
            subscription_enabled
            and status in ("trial", "active")
            and not_expired
        )

        grouped[app_id]["clients"].append({
            "id": row["client_id"],
            "name": row["client"],
            "subscription_status": status,
            "subscription_start_date": str(start_date) if start_date else None,
            "subscription_end_date": str(end_date) if end_date else None,
            "subscription_enabled": subscription_enabled,
            "is_accessible": is_accessible,
            "is_expiring_soon": is_expiring_soon,
        })

    return list(grouped.values())

@app.get("/apps")
def apps_catalog(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name, description FROM applications ORDER BY name")).fetchall()
    return [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]

@app.get("/entry")
def entry(
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    if not x_app_id or not x_client_id:
        raise HTTPException(status_code=400, detail="Faltan X-App-Id o X-Client-Id")

    if not has_active_membership(db, user, x_client_id):
        raise HTTPException(status_code=403, detail="Sin membresía activa para ese cliente")

    # Validar que el usuario tenga ese permiso
    if not has_permission(db, user, x_app_id, x_client_id):
        raise HTTPException(status_code=403, detail="Sin permiso para esa app/cliente")

    if not has_active_subscription(db, x_client_id, x_app_id):
        raise HTTPException(status_code=403, detail="Suscripción inactiva para esa app/cliente")
    
    return {"ok": True, "user": user, "app_id": x_app_id, "client_id": x_client_id, "note": "App1 /entry OK"}