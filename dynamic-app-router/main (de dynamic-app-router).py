import os
from urllib.parse import urljoin

import jwt
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from sqlalchemy import text

from db import SessionLocal

app = FastAPI(title="RodelSoft Dynamic App Router")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY no configurada en dynamic-app-router")

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-encoding",
    "content-length",
    "host",
}


def get_app_by_slug(db, slug: str):
    row = db.execute(
        text("""
            SELECT
                id,
                name,
                slug,
                internal_url,
                entry_path,
                COALESCE(health_path, '/health') AS health_path,
                COALESCE(is_active, 1) AS is_active,
                COALESCE(launch_mode, 'redirect') AS launch_mode
            FROM applications
            WHERE slug = :slug
            LIMIT 1
        """),
        {"slug": slug},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")

    if int(row["is_active"]) != 1:
        raise HTTPException(status_code=503, detail="La aplicación está desactivada")

    return row


def build_target_url(internal_url: str, tail_path: str, query_string: str) -> str:
    base = (internal_url or "").rstrip("/") + "/"
    tail = (tail_path or "").lstrip("/")

    target = urljoin(base, tail)

    if query_string:
        target = f"{target}?{query_string}"

    return target


def filter_request_headers(request: Request, app_id: int, prefix: str) -> dict:
    headers = {}

    for key, value in request.headers.items():
        k = key.lower()
        if k in HOP_BY_HOP_HEADERS:
            continue
        headers[key] = value

    # Contexto importante para apps bajo prefijo dinámico
    headers["X-Forwarded-Prefix"] = prefix
    headers["X-Script-Name"] = prefix
    headers["X-App-Id"] = str(app_id)

    return headers


def rewrite_location(location: str, prefix: str) -> str:
    """
    Reglas:
    - Location: /         => dejar / (portal/login)
    - Location: /algo     => /ext/<slug>/algo
    - Absolutas           => dejarlas tal cual por ahora
    """
    if not location:
        return location

    if location == "/":
        return "/"

    if location.startswith("/") and not location.startswith(prefix + "/"):
        return f"{prefix}{location}"

    return location

def extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()

    cookie_token = request.cookies.get("jwt")
    if cookie_token:
        return cookie_token.strip()

    return None


def get_current_user(db, request: Request):
    token = extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Token inválido: falta sub")

    user = db.execute(
        text("""
            SELECT id, username
            FROM users
            WHERE username = :username
            LIMIT 1
        """),
        {"username": username},
    ).mappings().first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user


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


def has_active_subscription(db, client_id: int, app_id: int) -> bool:
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


def is_html_navigation_request(request: Request, tail_path: str) -> bool:
    """
    Detecta si la petición parece ser la navegación principal HTML.
    No se usa para assets.
    """
    if request.method.upper() != "GET":
        return False

    accept = (request.headers.get("accept") or "").lower()

    if "text/html" in accept:
        return True

    if not tail_path:
        return True

    return False

@app.get("/health")
def health():
    return {"ok": True, "service": "dynamic-app-router"}


@app.api_route("/ext/{slug}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
@app.api_route("/ext/{slug}/{tail_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def dynamic_proxy(request: Request, slug: str, tail_path: str = ""):
    db = SessionLocal()
    try:
        app_row = get_app_by_slug(db, slug)

        internal_url = (app_row["internal_url"] or "").strip()
        app_id = int(app_row["id"])

        if not internal_url:
            raise HTTPException(status_code=500, detail="La aplicación no tiene internal_url configurado")

        prefix = f"/ext/{slug}"
        
        # Blindaje FASE 6.0.A:
        # Solo exigir contexto/seguridad en navegación HTML principal.
        if is_html_navigation_request(request, tail_path):
            client_id_raw = request.query_params.get("client_id")
            app_id_raw = request.query_params.get("app_id")

            if not client_id_raw or not app_id_raw:
                raise HTTPException(status_code=400, detail="Falta contexto app_id/client_id")

            try:
                client_id = int(client_id_raw)
                requested_app_id = int(app_id_raw)
            except ValueError:
                raise HTTPException(status_code=400, detail="Contexto app_id/client_id inválido")

            if requested_app_id != app_id:
                raise HTTPException(status_code=400, detail="app_id no corresponde al slug solicitado")

            user = get_current_user(db, request)
            user_id = int(user["id"])

            if not user_has_active_membership(db, user_id, client_id):
                raise HTTPException(status_code=403, detail="Sin membresía activa para ese cliente")

            if not user_has_permission(db, user_id, client_id, app_id):
                raise HTTPException(status_code=403, detail="Sin permiso para esa app/cliente")

            if not has_active_subscription(db, client_id, app_id):
                raise HTTPException(status_code=403, detail="Suscripción inactiva para esa app/cliente")

        # Si entra a /ext/<slug> o /ext/<slug>/ -> respetar raíz de la app
        target_url = build_target_url(
            internal_url=internal_url,
            tail_path=tail_path,
            query_string=request.url.query,
        )

        body = await request.body()

        headers = filter_request_headers(request, app_id, prefix)

        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=body if body else None,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30,
        )

        response_headers = {}
        for key, value in resp.headers.items():
            k = key.lower()
            if k in HOP_BY_HOP_HEADERS:
                continue

            if k == "location":
                value = rewrite_location(value, prefix)

            response_headers[key] = value

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=response_headers,
            media_type=resp.headers.get("content-type"),
        )

    except HTTPException:
        raise
    except requests.RequestException as e:
        print(f"[dynamic-app-router] Error proxy: {e}")
        return JSONResponse(
            status_code=502,
            content={"ok": False, "detail": f"Error conectando a app destino: {str(e)}"},
        )
    except Exception as e:
        print(f"[dynamic-app-router] ERROR inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno dynamic-app-router: {str(e)}")
    finally:
        db.close()