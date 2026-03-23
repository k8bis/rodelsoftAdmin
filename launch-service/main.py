from fastapi import FastAPI, Depends, HTTPException, Cookie, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from jose import jwt, JWTError
import os
import requests
from urllib.parse import urlencode

app = FastAPI(title="RodelSoft - Launch Service")

# =========================
# ENV
# =========================
DB_USER = os.getenv("MYSQL_USER", "appuser")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "apppass")
DB_HOST = os.getenv("MYSQL_HOST", "mysql")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "proyecto_db")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

PORTAL_URL = os.getenv("PORTAL_URL", "http://portal:80")
HEALTH_TIMEOUT = float(os.getenv("HEALTH_TIMEOUT", "2.0"))

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# =========================
# DB
# =========================
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# AUTH
# =========================
def verify_token(jwt_cookie: str = Cookie(default=None, alias="jwt")) -> str:
    if not jwt_cookie:
        raise HTTPException(status_code=401, detail="No autenticado (cookie jwt no encontrada)")

    try:
        payload = jwt.decode(jwt_cookie, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token inválido: sin subject")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

# =========================
# HELPERS
# =========================
def portal_redirect(message: str):
    params = urlencode({"msg": message})
    return RedirectResponse(url=f"{PORTAL_URL}/?{params}", status_code=302)

def normalize_entry_path(path: str | None) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path

def build_launch_url(upstream: str, entry_path: str, app_id: int, client_id: int) -> str:
    entry_path = normalize_entry_path(entry_path)

    # Si entry_path = "/" → http://service:port/?app_id=...&client_id=...
    # Si entry_path = "/algo" → http://service:port/algo?app_id=...&client_id=...
    base = upstream.rstrip("/")
    if entry_path == "/":
        return f"{base}/?app_id={app_id}&client_id={client_id}"
    else:
        return f"{base}{entry_path}?app_id={app_id}&client_id={client_id}"

def check_app_health(upstream: str) -> tuple[bool, str]:
    # Intento 1: /health
    try:
        r = requests.get(f"{upstream.rstrip('/')}/health", timeout=HEALTH_TIMEOUT)
        if r.ok:
            return True, "ok"
    except Exception:
        pass

    # Intento 2: raíz /
    try:
        r = requests.get(f"{upstream.rstrip('/')}/", timeout=HEALTH_TIMEOUT)
        if r.ok:
            return True, "ok"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)

# =========================
# ROUTES
# =========================
@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        now = db.execute(text("SELECT NOW()")).scalar()
        return {"status": "ok", "db_time": str(now)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

@app.get("/launch")
def launch(
    app_id: int = Query(...),
    client_id: int = Query(...),
    username: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    # 1) Validar permiso
    q_perm = text("""
        SELECT 
            a.id,
            a.name,
            a.slug,
            a.description,
            a.upstream,
            a.entry_path,
            p.role
        FROM permissions p
        JOIN users u ON u.id = p.user_id
        JOIN applications a ON a.id = p.app_id
        JOIN clients c ON c.id = p.client_id
        WHERE u.username = :username
          AND p.app_id = :app_id
          AND p.client_id = :client_id
        LIMIT 1
    """)

    row = db.execute(q_perm, {
        "username": username,
        "app_id": app_id,
        "client_id": client_id
    }).fetchone()

    if not row:
        return portal_redirect("No tienes permiso para acceder a esa aplicación con el cliente seleccionado.")

    resolved_app_id, app_name, slug, description, upstream, entry_path, role = row

    # 2) Health check
    ok, detail = check_app_health(upstream)

    if not ok:
        return portal_redirect(
            f"La aplicación '{app_name}' no está disponible por el momento. Intenta más tarde."
        )

    # 3) Redirección a la app hija
    launch_url = build_launch_url(upstream, entry_path, app_id, client_id)
    return RedirectResponse(url=launch_url, status_code=302)