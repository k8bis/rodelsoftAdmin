# apps/app-hija-1/routes/public.py
from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db
from core.auth import (
    ALGORITHM,
    SECRET_KEY,
    _build_logout_response,
    create_access_token,
    validate_token_from_request,
    verify_password_and_upgrade,
    verify_token,
)
from core.access import (
    enforce_access,
    redirect_to_portal_with_message,
    resolve_context,
)
from core.admin_security import get_admin_scopes, is_system_admin
from schemas.auth import Login

router = APIRouter()


@router.get("/")
def root(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    token = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

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

    app_id, client_id = resolve_context(request, x_app_id, x_client_id)

    if not app_id or not client_id:
        return redirect_to_portal_with_message(
            "No se pudo abrir la aplicación porque faltan datos de contexto.",
            "warning"
        )

    try:
        enforce_access(db, user, app_id, client_id)
    except HTTPException as e:
        detail = e.detail if isinstance(e.detail, str) else "Acceso denegado"
        return redirect_to_portal_with_message(detail, "warning")

    return {
        "message": "App Hija 1 funcionando!",
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
        "secured": True
    }


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        now = db.execute(text("SELECT NOW()")).fetchone()[0]
        return {"status": "ok", "db_time": str(now)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


@router.post("/login")
def login(data: Login, response: Response, db: Session = Depends(get_db)):
    user_id = verify_password_and_upgrade(db, data.username, data.password)

    if not user_id:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    token = create_access_token(data.username)

    response.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        samesite="lax",
        path="/"
    )

    return {"status": "ok", "access_token": token, "token_type": "bearer"}


@router.get("/permissions")
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


@router.get("/validate")
def validate(request: Request, authorization: str | None = Header(default=None)):
    return validate_token_from_request(request, authorization)


@router.api_route("/logout", methods=["GET", "POST"], include_in_schema=False)
def logout_compat():
    return _build_logout_response()


@router.get("/logout", include_in_schema=True, operation_id="logout_get")
def logout_get():
    return _build_logout_response()


@router.post("/logout", include_in_schema=True, operation_id="logout_post")
def logout_post():
    return _build_logout_response()


@router.get("/me")
def get_me(
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    system_admin = is_system_admin(db, user)
    admin_scopes = get_admin_scopes(db, user)

    return {
        "user": user,
        "app_id": x_app_id,
        "client_id": x_client_id,
        "is_system_admin": system_admin,
        "has_admin_scope": system_admin or len(admin_scopes) > 0,
        "admin_scopes": admin_scopes,
    }


@router.get("/my/apps")
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
            a.is_active AS app_enabled,
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
                "app_enabled": bool(row["app_enabled"]) if row["app_enabled"] is not None else False,
                "clients": [],
            }

        raw_status = row["subscription_status"]
        status = raw_status.strip().lower() if raw_status else "missing"

        start_date = row["subscription_start_date"]
        end_date = row["subscription_end_date"]
        subscription_enabled = bool(row["subscription_enabled"]) if row["subscription_enabled"] is not None else False

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

        if end_date:
            if hasattr(end_date, "hour"):
                not_expired = end_date >= now
            else:
                not_expired = end_date >= now.date()
        else:
            not_expired = True

        app_enabled = bool(row["app_enabled"]) if row["app_enabled"] is not None else False

        is_accessible = (
            app_enabled
            and subscription_enabled
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
            "app_enabled": app_enabled,
            "is_accessible": is_accessible,
            "is_expiring_soon": is_expiring_soon,
        })

    return list(grouped.values())


@router.get("/apps")
def apps_catalog(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name, description FROM applications ORDER BY name")).fetchall()
    return [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]


@router.get("/entry")
def entry(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)

    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    enforce_access(db, user, app_id, client_id)

    return {"ok": True, "user": user, "app_id": app_id, "client_id": client_id, "note": "App1 /entry OK"}