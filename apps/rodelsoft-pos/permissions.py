from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session


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


def validate_permission(db: Session, username: str, app_id: int, client_id: int):
    q = text("""
        SELECT 1
        FROM permissions p
        JOIN users u ON u.id = p.user_id
        WHERE u.username = :username
          AND p.app_id = :app_id
          AND p.client_id = :client_id
        LIMIT 1
    """)
    ok = db.execute(
        q,
        {
            "username": username,
            "app_id": app_id,
            "client_id": client_id,
        },
    ).fetchone()

    if not ok:
        raise HTTPException(status_code=403, detail="Sin permiso para esa app/cliente")
