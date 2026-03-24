import os
import time
from typing import Optional

import jwt
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# =========================================================
# Configuración
# =========================================================

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

DB_HOST = os.getenv("MYSQL_HOST", "mysql")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "proyecto_db")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "rootpass")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# =========================================================
# DB
# =========================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# =========================================================
# App
# =========================================================

app = FastAPI(title="RodelSoft Launch Service")


# =========================================================
# Helpers
# =========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def extract_token(request: Request) -> Optional[str]:
    """
    Prioridad:
    1) Header Authorization: Bearer <token>
    2) Cookie jwt
    """
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get("jwt")
    if cookie_token:
        return cookie_token.strip()

    return None


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def get_current_user(request: Request, db):
    """
    Resuelve el usuario actual a partir del JWT.
    Se espera que el payload tenga 'sub' = username.
    """
    token = extract_token(request)

    # DEBUG útil (puedes quitarlo después)
    print(f"[launch-service] Cookie jwt presente: {'SI' if request.cookies.get('jwt') else 'NO'}")
    print(f"[launch-service] Authorization header presente: {'SI' if request.headers.get('authorization') else 'NO'}")

    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = decode_jwt_token(token)
    print(f"[launch-service] Payload JWT: {payload}")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Token inválido: falta sub")

    user = db.execute(
        text("""
            SELECT id, username, email
            FROM users
            WHERE username = :username
            LIMIT 1
        """),
        {"username": username},
    ).mappings().first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user


def user_has_permission(db, user_id: int, client_id: int, app_id: int) -> bool:
    row = db.execute(
        text("""
            SELECT 1
            FROM permissions
            WHERE user_id = :user_id
              AND client_id = :client_id
              AND app_id = :app_id
            LIMIT 1
        """),
        {
            "user_id": user_id,
            "client_id": client_id,
            "app_id": app_id,
        },
    ).first()

    return row is not None


def get_app_metadata(db, app_id: int):
    """
    Catálogo dinámico de aplicaciones.
    NO usa hardcode.
    Usa el esquema actual:
      - internal_url
      - public_url
      - entry_path
      - launch_mode
      - health_path
      - is_active
    """
    row = db.execute(
        text("""
            SELECT
                id,
                name,
                slug,
                internal_url,
                public_url,
                entry_path,
                COALESCE(health_path, '/health') AS health_path,
                COALESCE(is_active, 1) AS is_active,
                COALESCE(launch_mode, 'redirect') AS launch_mode
            FROM applications
            WHERE id = :app_id
            LIMIT 1
        """),
        {"app_id": app_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")

    if int(row["is_active"]) != 1:
        raise HTTPException(status_code=503, detail="La aplicación está desactivada")

    return row


def build_health_url(internal_url: str, health_path: str) -> str:
    internal = (internal_url or "").rstrip("/")
    path = (health_path or "/health").strip()

    if not path.startswith("/"):
        path = "/" + path

    return f"{internal}{path}"


def build_final_url(public_url: str, entry_path: str, app_id: int, client_id: int) -> str:
    """
    URL final para el navegador.
    100% dinámica por base de datos.
    """
    base = (public_url or "").rstrip("/")
    path = (entry_path or "/").strip()

    if not path.startswith("/"):
        path = "/" + path

    if path == "/":
        return f"{base}/?app_id={app_id}&client_id={client_id}"

    return f"{base}{path}?app_id={app_id}&client_id={client_id}"


def check_app_health(internal_url: str, health_path: str, timeout_seconds: int = 2) -> bool:
    """
    Health check interno usando la red Docker / red interna.
    """
    health_url = build_health_url(internal_url, health_path)
    print(f"[launch-service] Health URL: {health_url}")

    try:
        resp = requests.get(health_url, timeout=timeout_seconds)
        print(f"[launch-service] Health status: {resp.status_code}")
        return 200 <= resp.status_code < 300
    except Exception as e:
        print(f"[launch-service] Health check error: {e}")
        return False


# =========================================================
# Endpoints
# =========================================================

@app.get("/health")
def health():
    return {"ok": True, "service": "launch-service", "ts": int(time.time())}


@app.get("/launch")
def launch(request: Request, app_id: int, client_id: int):
    """
    Flujo:
    1) Validar JWT / usuario
    2) Validar permiso (user_id + client_id + app_id)
    3) Consultar app dinámica desde BD
    4) Health check a internal_url + health_path
    5) Redirigir a public_url + entry_path + query params
    """
    db = SessionLocal()
    try:
        # 1) Usuario autenticado
        user = get_current_user(request, db)
        user_id = int(user["id"])

        print(f"[launch-service] Launch solicitado por user_id={user_id}, app_id={app_id}, client_id={client_id}")

        # 2) Permiso
        if not user_has_permission(db, user_id, client_id, app_id):
            raise HTTPException(status_code=403, detail="No tienes permiso para esta aplicación/cliente")

        # 3) Metadata app
        app_row = get_app_metadata(db, app_id)

        internal_url = (app_row["internal_url"] or "").strip()
        public_url = (app_row["public_url"] or "").strip()
        entry_path = (app_row["entry_path"] or "/").strip()
        health_path = (app_row["health_path"] or "/health").strip()
        launch_mode = (app_row["launch_mode"] or "redirect").strip().lower()

        if not internal_url:
            raise HTTPException(status_code=500, detail="La aplicación no tiene internal_url configurado")

        if not public_url:
            raise HTTPException(status_code=500, detail="La aplicación no tiene public_url configurado")

        print(
            f"[launch-service] App metadata => "
            f"name={app_row['name']}, slug={app_row['slug']}, "
            f"internal_url={internal_url}, public_url={public_url}, "
            f"entry_path={entry_path}, health_path={health_path}, launch_mode={launch_mode}"
        )

        # 4) Health check
        healthy = check_app_health(internal_url, health_path, timeout_seconds=2)
        if not healthy:
            return JSONResponse(
                status_code=503,
                content={
                    "ok": False,
                    "message": "La aplicación no está disponible por el momento",
                    "app_id": app_id,
                    "client_id": client_id,
                    "app_name": app_row["name"],
                    "slug": app_row["slug"],
                },
            )

        # 5) URL final (100% dinámica por BD)
        final_url = build_final_url(public_url, entry_path, app_id, client_id)
        print(f"[launch-service] Redirect final => {final_url}")

        # Por ahora launch_mode se conserva para futuro, pero el comportamiento actual
        # es redirect porque es el que cumple tu regla de cero hardcode.
        return RedirectResponse(url=final_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[launch-service] ERROR inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno launch-service: {str(e)}")
    finally:
        db.close()