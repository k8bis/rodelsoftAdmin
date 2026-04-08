# apps/app-hija-1/core/access.py
from datetime import datetime
from urllib.parse import urlencode

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session


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


def resolve_context(
    request: Request,
    x_app_id: int | None,
    x_client_id: int | None,
) -> tuple[int | None, int | None]:
    """
    Prioridad:
    1) Headers (flujo normal vía Nginx / Launch)
    2) Query params (flujo directo/manual)
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


def enforce_access(
    db: Session,
    username: str,
    app_id: int,
    client_id: int,
) -> None:
    """
    Enforcement único reutilizable para:
    - root
    - /entry
    - /internal/access-check
    - /internal/context-info
    """
    if not has_active_membership(db, username, client_id):
        raise HTTPException(status_code=403, detail="Sin membresía activa para ese cliente")

    if not has_permission(db, username, app_id, client_id):
        raise HTTPException(status_code=403, detail="Sin permiso para esa app/cliente")

    if not has_active_subscription(db, client_id, app_id):
        raise HTTPException(status_code=403, detail="Suscripción inactiva para esa app/cliente")


def get_context_names(
    db: Session,
    app_id: int,
    client_id: int,
) -> tuple[str, str]:
    row = db.execute(
        text("""
            SELECT
                a.name AS app_name,
                c.name AS client_name
            FROM applications a
            JOIN clients c
              ON c.id = :client_id
            WHERE a.id = :app_id
            LIMIT 1
        """),
        {
            "app_id": app_id,
            "client_id": client_id,
        },
    ).mappings().first()

    app_name = row["app_name"] if row else "POS"
    client_name = row["client_name"] if row else "Cliente"

    return app_name, client_name


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


def normalize_subscription_status(value: str | None) -> str:
    allowed = {"trial", "active", "suspended", "expired"}
    normalized = (value or "active").strip().lower()
    if normalized not in allowed:
        raise HTTPException(
            status_code=400,
            detail="status inválido. Usa: trial, active, suspended, expired"
        )
    return normalized


def parse_optional_date(value: str | None, field_name: str):
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} debe tener formato YYYY-MM-DD"
        )