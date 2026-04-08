import os
import requests
from fastapi import HTTPException, Request


CONTROL_PLANE_BASE_URL = os.getenv("CONTROL_PLANE_BASE_URL", "http://app-hija-1:8000")
CONTROL_PLANE_TIMEOUT = float(os.getenv("CONTROL_PLANE_TIMEOUT", "5"))


def resolve_context(request: Request, x_app_id: int | None, x_client_id: int | None):
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


def _extract_bearer_or_cookie(request: Request, authorization: str | None = None) -> str | None:
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization

    if not token:
        raw_cookie = request.cookies.get("jwt")
        if raw_cookie:
            token = f"Bearer {raw_cookie}"

    return token


def _call_control_plane(
    request: Request,
    endpoint: str,
    app_id: int,
    client_id: int,
    authorization: str | None = None,
) -> requests.Response:
    """
    Helper común para llamadas internas al Control Plane.
    Centraliza:
    - extracción de bearer/cookie
    - headers de contexto
    - timeout
    - manejo de errores de conectividad
    """
    bearer = _extract_bearer_or_cookie(request, authorization)

    if not bearer:
        raise HTTPException(status_code=401, detail="No token")

    try:
        response = requests.get(
            f"{CONTROL_PLANE_BASE_URL}{endpoint}",
            headers={
                "Authorization": bearer,
                "X-App-Id": str(app_id),
                "X-Client-Id": str(client_id),
            },
            timeout=CONTROL_PLANE_TIMEOUT,
        )
        return response
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Control Plane no disponible: {e}")


def _extract_error_detail(response: requests.Response, fallback: str) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return payload.get("detail", fallback)
        return fallback
    except Exception:
        return fallback


def validate_permission(
    request: Request,
    username: str,
    app_id: int,
    client_id: int,
    authorization: str | None = None,
):
    """
    FASE 8.1/8.2:
    POS NO consulta proyecto_db directo.
    Toda validación de acceso vive en Control Plane API.
    """
    response = _call_control_plane(
        request=request,
        endpoint="/internal/access-check",
        app_id=app_id,
        client_id=client_id,
        authorization=authorization,
    )

    if response.status_code == 200:
        return True

    detail = _extract_error_detail(response, "Acceso denegado por Control Plane")
    raise HTTPException(status_code=response.status_code, detail=detail)


def get_context_info(
    request: Request,
    app_id: int,
    client_id: int,
    authorization: str | None = None,
) -> dict:
    """
    Obtiene app_name y client_name desde Control Plane API.
    """
    response = _call_control_plane(
        request=request,
        endpoint="/internal/context-info",
        app_id=app_id,
        client_id=client_id,
        authorization=authorization,
    )

    if response.status_code == 200:
        return response.json()

    detail = _extract_error_detail(response, "No se pudo obtener contexto desde Control Plane")
    raise HTTPException(status_code=response.status_code, detail=detail)