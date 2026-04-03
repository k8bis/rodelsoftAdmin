import os
import time
from typing import Optional

import jwt
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlencode

# =========================================================
# Configuración
# =========================================================
PORTAL_ROOT_URL = os.getenv("PORTAL_ROOT_URL", "/")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

DB_HOST = os.getenv("MYSQL_HOST", "mysql")
DB_PORT = os.getenv("MYSQL_PORT", "3306")
DB_NAME = os.getenv("MYSQL_DATABASE", "proyecto_db")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")

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

def user_has_active_membership(db, user_id: int, client_id: int) -> bool:
    row = db.execute(
        text("""
            SELECT 1
            FROM user_client_memberships
            WHERE user_id = :user_id
              AND client_id = :client_id
              AND status = 'active'
            LIMIT 1
        """),
        {
            "user_id": user_id,
            "client_id": client_id,
        },
    ).first()

    return row is not None

def has_active_subscription(db, client_id: int, app_id: int) -> bool:
    """
    Valida acceso contractual efectivo para la combinación cliente + app.
    Reglas MVP:
    - is_enabled = 1
    - status IN ('trial', 'active')
    - end_date nula o vigente
    """
    row = db.execute(
        text("""
            SELECT 1
            FROM client_app_subscriptions
            WHERE client_id = :client_id
              AND app_id = :app_id
              AND is_enabled = 1
              AND status IN ('trial', 'active')
              AND (end_date IS NULL OR end_date >= NOW())
            LIMIT 1
        """),
        {
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

def build_final_url(request: Request, public_url: str, entry_path: str, app_id: int, client_id: int) -> str:
    """
    Construye la URL final para el navegador soportando:
    - public_url relativo  -> usa host real de la petición (multi-dispositivo)
    - public_url absoluto  -> lo usa tal cual
    - entry_path           -> ruta interna inicial dentro de la app

    Ejemplos:
      public_url=/pos/                     entry_path=/           => http://HOST/pos/?app_id=3&client_id=4
      public_url=/pos/                     entry_path=/dashboard  => http://HOST/pos/dashboard?app_id=3&client_id=4
      public_url=http://192.168.1.120:8005 entry_path=/          => http://192.168.1.120:8005/?app_id=3&client_id=4
      public_url=https://crm.local         entry_path=/workspace  => https://crm.local/workspace?app_id=5&client_id=2
    """
    raw_public = (public_url or "").strip()
    raw_entry = (entry_path or "/").strip()

    # Normaliza entry_path
    if not raw_entry.startswith("/"):
        raw_entry = "/" + raw_entry

    # Detecta host/scheme reales de la petición
    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = forwarded_proto or request.url.scheme or "http"
    host = request.headers.get("host")

    if not host:
        raise HTTPException(status_code=500, detail="No se pudo resolver el host de la petición")

    # Si public_url es relativo => construir base con el host real
    if raw_public.startswith("/"):
        base = raw_public.rstrip("/")
        if base == "":
            base = ""
        base_url = f"{scheme}://{host}{base}"

    # Si public_url es absoluto => usar tal cual
    elif raw_public.startswith("http://") or raw_public.startswith("https://"):
        base_url = raw_public.rstrip("/")

    else:
        raise HTTPException(
            status_code=500,
            detail="public_url inválido: debe iniciar con '/' o con 'http://'/'https://'",
        )

    # Construcción final evitando dobles slashes
    if raw_entry == "/":
        final_path = "/"
    else:
        final_path = raw_entry

    query = urlencode({
        "app_id": app_id,
        "client_id": client_id,
    })

    return f"{base_url}{final_path}?{query}"

def build_dynamic_proxy_url(request: Request, slug: str, entry_path: str, app_id: int, client_id: int) -> str:
    """
    Construye URL dinámica bajo /ext/<slug>/...
    Ejemplo:
      /ext/rodelsoft-notes-external/?app_id=4&client_id=4
    """
    raw_entry = (entry_path or "/").strip()

    if not raw_entry.startswith("/"):
        raw_entry = "/" + raw_entry

    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = forwarded_proto or request.url.scheme or "http"
    host = request.headers.get("host")

    if not host:
        raise HTTPException(status_code=500, detail="No se pudo resolver el host de la petición")

    base_url = f"{scheme}://{host}/ext/{slug}"

    final_path = "/" if raw_entry == "/" else raw_entry

    query = urlencode({
        "app_id": app_id,
        "client_id": client_id,
    })

    return f"{base_url}{final_path}?{query}"

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

def redirect_to_portal_with_message(message: str, level: str = "warning") -> RedirectResponse:
    """
    Redirige al portal principal con mensaje UX amigable.
    El portal ya soporta ?msg=... y ?msg_type=...
    """
    qs = urlencode({
        "msg": message,
        "msg_type": level,
    })
    base = PORTAL_ROOT_URL.rstrip("/") or "/"

    if base == "/":
        return RedirectResponse(url=f"/?{qs}", status_code=302)

    return RedirectResponse(url=f"{base}/?{qs}", status_code=302)

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
    2) Validar membresía activa
    3) Validar permiso
    4) Validar suscripción
    5) Consultar app dinámica desde BD
    6) Health check
    7) Redirigir
    """
    db = SessionLocal()
    try:
        # 1) Usuario autenticado
        user = get_current_user(request, db)
        user_id = int(user["id"])

        print(f"[launch-service] Launch solicitado por user_id={user_id}, app_id={app_id}, client_id={client_id}")

        # 2) Membresía activa
        if not user_has_active_membership(db, user_id, client_id):
            return redirect_to_portal_with_message(
                "Tu usuario no tiene membresía activa para el cliente seleccionado.",
                "warning"
            )
        
        # 3) Permiso
        if not user_has_permission(db, user_id, client_id, app_id):
            return redirect_to_portal_with_message(
                "No tienes permiso para acceder a esta aplicación con el cliente seleccionado.",
                "warning"
            )

        # 3.1) Suscripción activa (FASE 6D)
        if not has_active_subscription(db, client_id, app_id):
            return redirect_to_portal_with_message(
                "La suscripción de esta aplicación no está activa para el cliente seleccionado.",
                "warning"
            )

        # 5) Metadata app
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

        # 6) Health check (FASE 6E: UX amigable)
        healthy = check_app_health(internal_url, health_path, timeout_seconds=2)
        if not healthy:
            return redirect_to_portal_with_message(
                f"La aplicación {app_row['name']} no está disponible por el momento.",
                "warning"
            )

        # 7) URL final según launch_mode
        if launch_mode == "dynamic_proxy":
            slug = (app_row["slug"] or "").strip()
            if not slug:
                raise HTTPException(status_code=500, detail="La aplicación no tiene slug configurado")

            final_url = build_dynamic_proxy_url(request, slug, entry_path, app_id, client_id)
        else:
            final_url = build_final_url(request, public_url, entry_path, app_id, client_id)

        print(f"[launch-service] Redirect final => {final_url}")

        return RedirectResponse(url=final_url, status_code=302)

    except HTTPException as e:
        # UX browser-friendly para launch-service:
        # en vez de JSON crudo, regresar al portal con mensaje.
        if e.status_code == 401:
            return redirect_to_portal_with_message(
                "Tu sesión no está activa o expiró. Inicia sesión nuevamente.",
                "warning"
            )

        if e.status_code == 403:
            return redirect_to_portal_with_message(
                e.detail if isinstance(e.detail, str) else "No tienes acceso a esta aplicación.",
                "warning"
            )

        if e.status_code == 404:
            return redirect_to_portal_with_message(
                "La aplicación solicitada no existe o ya no está disponible.",
                "error"
            )

        if e.status_code == 503:
            return redirect_to_portal_with_message(
                e.detail if isinstance(e.detail, str) else "La aplicación no está disponible por el momento.",
                "warning"
            )

        raise
    except Exception as e:
        print(f"[launch-service] ERROR inesperado: {e}")
        return redirect_to_portal_with_message(
            "Ocurrió un error interno al intentar abrir la aplicación.",
            "error"
        )
    finally:
        db.close()