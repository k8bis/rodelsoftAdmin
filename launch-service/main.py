import os
import requests
import jwt
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "proyecto_db")
MYSQL_USER = os.getenv("MYSQL_USER", "appuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppass")

SECRET_KEY = os.getenv("SECRET_KEY", "miclave_secreta")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="RodelSoft Launch Service")


def get_token(request: Request, authorization: str | None):
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        token = request.cookies.get("jwt")

    if not token:
        raise HTTPException(status_code=401, detail="No token")

    return token


def get_username_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


@app.get("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


@app.get("/launch")
def launch(
    request: Request,
    app_id: int,
    client_id: int,
    authorization: str | None = Header(default=None),
):
    # 1) JWT
    token = get_token(request, authorization)
    username = get_username_from_token(token)

    # 2) Validar permiso
    with engine.connect() as conn:
        perm = conn.execute(
            text("""
                SELECT 1
                FROM permissions p
                JOIN users u ON u.id = p.user_id
                WHERE u.username = :username
                  AND p.app_id = :app_id
                  AND p.client_id = :client_id
                LIMIT 1
            """),
            {"username": username, "app_id": app_id, "client_id": client_id}
        ).fetchone()

        if not perm:
            return RedirectResponse(
                url="/?msg=No tienes permiso para acceder a esa aplicación.",
                status_code=302
            )

        # 3) Obtener datos de la app
        app_row = conn.execute(
            text("""
                SELECT id, name, slug, internal_url, public_url, entry_path, launch_mode
                FROM applications
                WHERE id = :app_id
                LIMIT 1
            """),
            {"app_id": app_id}
        ).fetchone()

    if not app_row:
        return RedirectResponse(
            url="/?msg=La aplicación solicitada no existe.",
            status_code=302
        )

    _, app_name, slug, internal_url, public_url, entry_path, launch_mode = app_row

    entry_path = entry_path or "/"
    if not entry_path.startswith("/"):
        entry_path = "/" + entry_path

    # 4) Health check contra URL interna
    health_url = internal_url.rstrip("/") + "/health"
    try:
        r = requests.get(health_url, timeout=2)
        if r.status_code != 200:
            return RedirectResponse(
                url=f"/?msg=La aplicación {app_name} no está disponible por el momento.",
                status_code=302
            )
    except Exception:
        return RedirectResponse(
            url=f"/?msg=La aplicación {app_name} no está disponible por el momento.",
            status_code=302
        )

    # 5) Redirigir usando URL pública
    final_url = f"{public_url.rstrip('/')}{entry_path}?app_id={app_id}&client_id={client_id}"
    return RedirectResponse(url=final_url, status_code=302)