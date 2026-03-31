import os
from urllib.parse import urljoin

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from sqlalchemy import text

from db import SessionLocal

app = FastAPI(title="RodelSoft Dynamic App Router")

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