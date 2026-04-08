from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db
from core.auth import verify_token
from core.access import normalize_subscription_status, parse_optional_date
from core.admin_security import (
    get_admin_scopes,
    is_system_admin,
    require_admin_module_access,
    require_admin_scope_for_client,
    require_system_admin,
)
from schemas.admin import (
    AdminCreateApplicationPayload,
    AdminCreatePermissionPayload,
    AdminUpdateApplicationPayload,
    AdminUpdateClientPayload,
    AdminUpdatePermissionRolePayload,
    AdminUpdateSubscriptionPayload,
    AdminUpdateUserPayload,
    InternalAdminClientItem,
    InternalAdminCreateClientRequest,
    InternalAdminCreateUserRequest,
    InternalAdminGlobalApplicationItem,
    InternalAdminGlobalClientItem,
    InternalAdminGlobalUserItem,
    InternalAdminPermissionByClientItem,
    InternalAdminSubscriptionByClientItem,
    InternalAdminUpsertSubscriptionRequest,
    InternalAdminUserByClientItem,
)

router = APIRouter()


@router.get("/internal/admin/clients", response_model=list[InternalAdminClientItem])
def internal_admin_clients(
    user: str = Depends(require_admin_module_access),
    db: Session = Depends(get_db),
):
    if is_system_admin(db, user):
        rows = db.execute(text("""
            SELECT
                c.id AS client_id,
                c.name AS client_name
            FROM clients c
            ORDER BY c.name
        """)).mappings().all()
    else:
        rows = db.execute(text("""
            SELECT DISTINCT
                c.id AS client_id,
                c.name AS client_name
            FROM permissions p
            JOIN users u
              ON u.id = p.user_id
            JOIN clients c
              ON c.id = p.client_id
            WHERE u.username = :username
              AND p.role = 'app_client_admin'
            ORDER BY c.name
        """), {
            "username": user
        }).mappings().all()

    return [
        {
            "client_id": r["client_id"],
            "client_name": r["client_name"],
            "status": None,
        }
        for r in rows
    ]


@router.get("/internal/admin/users-by-client", response_model=list[InternalAdminUserByClientItem])
def internal_admin_users_by_client(
    client_id: int = Query(..., gt=0),
    user: str = Depends(require_admin_module_access),
    db: Session = Depends(get_db),
):
    require_admin_scope_for_client(client_id, user, db)

    if is_system_admin(db, user):
        rows = db.execute(text("""
            SELECT DISTINCT
                u.id AS user_id,
                u.username AS username,
                u.email AS email,
                ucm.status AS membership_status
            FROM user_client_memberships ucm
            JOIN users u
              ON u.id = ucm.user_id
            WHERE ucm.client_id = :client_id
            ORDER BY u.username
        """), {
            "client_id": client_id
        }).mappings().all()
    else:
        rows = db.execute(text("""
            SELECT DISTINCT
                u_target.id AS user_id,
                u_target.username AS username,
                u_target.email AS email,
                ucm.status AS membership_status
            FROM permissions p_target
            JOIN users u_target
              ON u_target.id = p_target.user_id
            LEFT JOIN user_client_memberships ucm
              ON ucm.user_id = p_target.user_id
             AND ucm.client_id = p_target.client_id
            WHERE p_target.client_id = :client_id
              AND p_target.app_id IN (
                  SELECT p_admin.app_id
                  FROM permissions p_admin
                  JOIN users u_admin
                    ON u_admin.id = p_admin.user_id
                  WHERE u_admin.username = :username
                    AND p_admin.client_id = :client_id
                    AND p_admin.role = 'app_client_admin'
              )
            ORDER BY u_target.username
        """), {
            "client_id": client_id,
            "username": user,
        }).mappings().all()

    return [
        {
            "user_id": r["user_id"],
            "username": r["username"],
            "email": r["email"],
            "membership_status": r["membership_status"],
        }
        for r in rows
    ]


@router.get("/internal/admin/subscriptions-by-client", response_model=list[InternalAdminSubscriptionByClientItem])
def internal_admin_subscriptions_by_client(
    client_id: int = Query(..., gt=0),
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT
            s.id AS subscription_id,
            s.app_id AS app_id,
            a.name AS app_name,
            s.status AS status,
            s.is_enabled AS is_enabled,
            s.start_date AS start_date,
            s.end_date AS end_date
        FROM client_app_subscriptions s
        JOIN applications a
          ON a.id = s.app_id
        WHERE s.client_id = :client_id
        ORDER BY a.name
    """), {
        "client_id": client_id
    }).mappings().all()

    return [
        {
            "subscription_id": r["subscription_id"],
            "app_id": r["app_id"],
            "app_name": r["app_name"],
            "status": r["status"],
            "is_enabled": bool(r["is_enabled"]),
            "start_date": str(r["start_date"]) if r["start_date"] else None,
            "end_date": str(r["end_date"]) if r["end_date"] else None,
        }
        for r in rows
    ]


@router.get("/internal/admin/permissions-by-client", response_model=list[InternalAdminPermissionByClientItem])
def internal_admin_permissions_by_client(
    client_id: int = Query(..., gt=0),
    user: str = Depends(require_admin_module_access),
    db: Session = Depends(get_db),
):
    require_admin_scope_for_client(client_id, user, db)

    if is_system_admin(db, user):
        rows = db.execute(text("""
            SELECT
                p.id AS permission_id,
                u.id AS user_id,
                u.username AS username,
                a.id AS app_id,
                a.name AS app_name,
                c.id AS client_id,
                c.name AS client_name,
                p.role AS role
            FROM permissions p
            JOIN users u
              ON u.id = p.user_id
            JOIN applications a
              ON a.id = p.app_id
            JOIN clients c
              ON c.id = p.client_id
            WHERE p.client_id = :client_id
            ORDER BY a.name, u.username
        """), {
            "client_id": client_id
        }).mappings().all()
    else:
        rows = db.execute(text("""
            SELECT
                p.id AS permission_id,
                u.id AS user_id,
                u.username AS username,
                a.id AS app_id,
                a.name AS app_name,
                c.id AS client_id,
                c.name AS client_name,
                p.role AS role
            FROM permissions p
            JOIN users u
              ON u.id = p.user_id
            JOIN applications a
              ON a.id = p.app_id
            JOIN clients c
              ON c.id = p.client_id
            WHERE p.client_id = :client_id
              AND p.app_id IN (
                  SELECT p_admin.app_id
                  FROM permissions p_admin
                  JOIN users u_admin
                    ON u_admin.id = p_admin.user_id
                  WHERE u_admin.username = :username
                    AND p_admin.client_id = :client_id
                    AND p_admin.role = 'app_client_admin'
              )
            ORDER BY a.name, u.username
        """), {
            "client_id": client_id,
            "username": user,
        }).mappings().all()

    return [
        {
            "permission_id": r["permission_id"],
            "user_id": r["user_id"],
            "username": r["username"],
            "app_id": r["app_id"],
            "app_name": r["app_name"],
            "client_id": r["client_id"],
            "client_name": r["client_name"],
            "role": r["role"],
        }
        for r in rows
    ]


@router.get("/internal/admin/global-users", response_model=list[InternalAdminGlobalUserItem])
def internal_admin_global_users(
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT
            u.id AS user_id,
            u.username AS username,
            u.email AS email,
            CASE
                WHEN sa.user_id IS NOT NULL THEN 1
                ELSE 0
            END AS is_system_admin,
            COUNT(DISTINCT ucm.client_id) AS clients_count,
            COUNT(DISTINCT p.id) AS permissions_count
        FROM users u
        LEFT JOIN system_admins sa
          ON sa.user_id = u.id
        LEFT JOIN user_client_memberships ucm
          ON ucm.user_id = u.id
        LEFT JOIN permissions p
          ON p.user_id = u.id
        GROUP BY
            u.id,
            u.username,
            u.email,
            sa.user_id
        ORDER BY u.username
    """)).mappings().all()

    return [
        {
            "user_id": r["user_id"],
            "username": r["username"],
            "email": r["email"],
            "is_system_admin": bool(r["is_system_admin"]),
            "clients_count": int(r["clients_count"] or 0),
            "permissions_count": int(r["permissions_count"] or 0),
        }
        for r in rows
    ]


@router.get("/internal/admin/global-applications", response_model=list[InternalAdminGlobalApplicationItem])
def internal_admin_global_applications(
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT
            a.id AS app_id,
            a.name AS app_name,
            a.slug AS slug,
            a.description AS description,
            a.internal_url AS internal_url,
            a.public_url AS public_url,
            a.entry_path AS entry_path,
            a.health_path AS health_path,
            a.launch_mode AS launch_mode,
            COALESCE(a.is_active, 1) AS is_enabled,
            COUNT(DISTINCT s.client_id) AS clients_count,
            COUNT(DISTINCT p.id) AS permissions_count
        FROM applications a
        LEFT JOIN client_app_subscriptions s
          ON s.app_id = a.id
        LEFT JOIN permissions p
          ON p.app_id = a.id
        GROUP BY
            a.id,
            a.name,
            a.slug,
            a.description,
            a.internal_url,
            a.public_url,
            a.entry_path,
            a.health_path,
            a.launch_mode,
            a.is_active
        ORDER BY a.name
    """)).mappings().all()

    return [
        {
            "app_id": r["app_id"],
            "app_name": r["app_name"],
            "slug": r["slug"],
            "description": r["description"],
            "internal_url": r["internal_url"],
            "public_url": r["public_url"],
            "entry_path": r["entry_path"],
            "health_path": r["health_path"],
            "launch_mode": r["launch_mode"],
            "is_enabled": bool(r["is_enabled"]),
            "clients_count": int(r["clients_count"] or 0),
            "permissions_count": int(r["permissions_count"] or 0),
        }
        for r in rows
    ]


@router.get("/internal/admin/global-clients", response_model=list[InternalAdminGlobalClientItem])
def internal_admin_global_clients(
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("""
        SELECT
            c.id AS client_id,
            c.name AS client_name,
            COUNT(DISTINCT CASE WHEN ucm.status = 'active' THEN ucm.user_id END) AS active_memberships,
            COUNT(DISTINCT s.id) AS subscriptions_count,
            COUNT(
                DISTINCT CASE
                    WHEN s.is_enabled = 1
                     AND s.status IN ('trial', 'active')
                     AND (s.end_date IS NULL OR s.end_date >= NOW())
                    THEN s.id
                END
            ) AS active_subscriptions_count
        FROM clients c
        LEFT JOIN user_client_memberships ucm
          ON ucm.client_id = c.id
        LEFT JOIN client_app_subscriptions s
          ON s.client_id = c.id
        GROUP BY
            c.id,
            c.name
        ORDER BY c.name
    """)).mappings().all()

    return [
        {
            "client_id": r["client_id"],
            "client_name": r["client_name"],
            "active_memberships": int(r["active_memberships"] or 0),
            "subscriptions_count": int(r["subscriptions_count"] or 0),
            "active_subscriptions_count": int(r["active_subscriptions_count"] or 0),
        }
        for r in rows
    ]


@router.post("/internal/admin/create-user")
def internal_admin_create_user(
    payload: InternalAdminCreateUserRequest,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    username = payload.username.strip()
    email = payload.email.strip() if payload.email else None

    if not username:
        raise HTTPException(status_code=400, detail="username es obligatorio")

    if not payload.password or len(payload.password) < 4:
        raise HTTPException(status_code=400, detail="password inválido o demasiado corto")

    existing = db.execute(
        text("""
            SELECT id
            FROM users
            WHERE username = :username
            LIMIT 1
        """),
        {"username": username}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese username")

    import bcrypt

    password_hash = bcrypt.hashpw(
        payload.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    db.execute(
        text("""
            INSERT INTO users (username, password, email)
            VALUES (:username, :password, :email)
        """),
        {
            "username": username,
            "password": password_hash,
            "email": email,
        }
    )
    db.commit()

    new_user = db.execute(
        text("""
            SELECT id, username, email
            FROM users
            WHERE username = :username
            LIMIT 1
        """),
        {"username": username}
    ).mappings().first()

    if not new_user:
        raise HTTPException(status_code=500, detail="No se pudo recuperar el usuario recién creado")

    if payload.is_system_admin:
        already_admin = db.execute(
            text("""
                SELECT 1
                FROM system_admins
                WHERE user_id = :user_id
                LIMIT 1
            """),
            {"user_id": new_user["id"]}
        ).fetchone()

        if not already_admin:
            db.execute(
                text("""
                    INSERT INTO system_admins (user_id)
                    VALUES (:user_id)
                """),
                {"user_id": new_user["id"]}
            )
            db.commit()

    return {
        "ok": True,
        "message": "Usuario creado correctamente",
        "user_id": new_user["id"],
        "username": new_user["username"],
        "email": new_user["email"],
        "is_system_admin": bool(payload.is_system_admin),
    }


@router.post("/internal/admin/create-client")
def internal_admin_create_client(
    payload: InternalAdminCreateClientRequest,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    client_name = payload.client_name.strip()

    if not client_name:
        raise HTTPException(status_code=400, detail="client_name es obligatorio")

    existing = db.execute(
        text("""
            SELECT id
            FROM clients
            WHERE name = :client_name
            LIMIT 1
        """),
        {"client_name": client_name}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese nombre")

    db.execute(
        text("""
            INSERT INTO clients (name)
            VALUES (:client_name)
        """),
        {"client_name": client_name}
    )
    db.commit()

    new_client = db.execute(
        text("""
            SELECT id, name
            FROM clients
            WHERE name = :client_name
            LIMIT 1
        """),
        {"client_name": client_name}
    ).mappings().first()

    if not new_client:
        raise HTTPException(status_code=500, detail="No se pudo recuperar el cliente recién creado")

    return {
        "ok": True,
        "message": "Cliente creado correctamente",
        "client_id": new_client["id"],
        "client_name": new_client["name"],
    }


@router.post("/internal/admin/upsert-subscription")
def internal_admin_upsert_subscription(
    payload: InternalAdminUpsertSubscriptionRequest,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    if payload.client_id <= 0:
        raise HTTPException(status_code=400, detail="client_id inválido")

    if payload.app_id <= 0:
        raise HTTPException(status_code=400, detail="app_id inválido")

    status = normalize_subscription_status(payload.status)
    start_date = parse_optional_date(payload.start_date, "start_date")
    end_date = parse_optional_date(payload.end_date, "end_date")

    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date no puede ser menor que start_date")

    client_exists = db.execute(
        text("""
            SELECT 1
            FROM clients
            WHERE id = :client_id
            LIMIT 1
        """),
        {"client_id": payload.client_id}
    ).fetchone()

    if not client_exists:
        raise HTTPException(status_code=404, detail="El cliente no existe")

    app_exists = db.execute(
        text("""
            SELECT 1
            FROM applications
            WHERE id = :app_id
            LIMIT 1
        """),
        {"app_id": payload.app_id}
    ).fetchone()

    if not app_exists:
        raise HTTPException(status_code=404, detail="La aplicación no existe")

    existing = db.execute(
        text("""
            SELECT id
            FROM client_app_subscriptions
            WHERE client_id = :client_id
              AND app_id = :app_id
            LIMIT 1
        """),
        {
            "client_id": payload.client_id,
            "app_id": payload.app_id,
        }
    ).mappings().first()

    if existing:
        db.execute(
            text("""
                UPDATE client_app_subscriptions
                SET status = :status,
                    is_enabled = :is_enabled,
                    start_date = :start_date,
                    end_date = :end_date
                WHERE id = :subscription_id
            """),
            {
                "status": status,
                "is_enabled": 1 if payload.is_enabled else 0,
                "start_date": start_date,
                "end_date": end_date,
                "subscription_id": existing["id"],
            }
        )
        db.commit()

        return {
            "ok": True,
            "mode": "updated",
            "message": "Suscripción actualizada correctamente",
            "subscription_id": existing["id"],
            "client_id": payload.client_id,
            "app_id": payload.app_id,
            "status": status,
            "is_enabled": bool(payload.is_enabled),
            "start_date": str(start_date) if start_date else None,
            "end_date": str(end_date) if end_date else None,
        }

    db.execute(
        text("""
            INSERT INTO client_app_subscriptions (
                client_id,
                app_id,
                status,
                is_enabled,
                start_date,
                end_date
            )
            VALUES (
                :client_id,
                :app_id,
                :status,
                :is_enabled,
                :start_date,
                :end_date
            )
        """),
        {
            "client_id": payload.client_id,
            "app_id": payload.app_id,
            "status": status,
            "is_enabled": 1 if payload.is_enabled else 0,
            "start_date": start_date,
            "end_date": end_date,
        }
    )
    db.commit()

    created = db.execute(
        text("""
            SELECT id
            FROM client_app_subscriptions
            WHERE client_id = :client_id
              AND app_id = :app_id
            LIMIT 1
        """),
        {
            "client_id": payload.client_id,
            "app_id": payload.app_id,
        }
    ).mappings().first()

    return {
        "ok": True,
        "mode": "created",
        "message": "Suscripción creada correctamente",
        "subscription_id": created["id"] if created else None,
        "client_id": payload.client_id,
        "app_id": payload.app_id,
        "status": status,
        "is_enabled": bool(payload.is_enabled),
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
    }


@router.post("/internal/admin/update-client")
def internal_admin_update_client(
    payload: AdminUpdateClientPayload,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    client_name = (payload.client_name or "").strip()

    if not client_name:
        raise HTTPException(status_code=400, detail="El nombre del cliente es obligatorio")

    existing = db.execute(
        text("""
            SELECT id, name
            FROM clients
            WHERE id = :client_id
            LIMIT 1
        """),
        {"client_id": payload.client_id}
    ).mappings().first()

    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    duplicate = db.execute(
        text("""
            SELECT id
            FROM clients
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(:client_name))
              AND id <> :client_id
            LIMIT 1
        """),
        {
            "client_name": client_name,
            "client_id": payload.client_id,
        }
    ).fetchone()

    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe otro cliente con ese nombre")

    db.execute(
        text("""
            UPDATE clients
            SET name = :client_name
            WHERE id = :client_id
        """),
        {
            "client_name": client_name,
            "client_id": payload.client_id,
        }
    )
    db.commit()

    return {
        "ok": True,
        "message": "Cliente actualizado correctamente",
        "client_id": payload.client_id,
        "client_name": client_name,
    }


@router.post("/internal/admin/update-subscription")
def internal_admin_update_subscription(
    payload: AdminUpdateSubscriptionPayload,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    status = normalize_subscription_status(payload.status)
    start_date = parse_optional_date(payload.start_date, "start_date")
    end_date = parse_optional_date(payload.end_date, "end_date")

    if start_date and end_date and end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date no puede ser menor que start_date")

    client_exists = db.execute(
        text("""
            SELECT 1
            FROM clients
            WHERE id = :client_id
            LIMIT 1
        """),
        {"client_id": payload.client_id}
    ).fetchone()

    if not client_exists:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    app_exists = db.execute(
        text("""
            SELECT 1
            FROM applications
            WHERE id = :app_id
            LIMIT 1
        """),
        {"app_id": payload.app_id}
    ).fetchone()

    if not app_exists:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")

    existing = db.execute(
        text("""
            SELECT id
            FROM client_app_subscriptions
            WHERE client_id = :client_id
              AND app_id = :app_id
            LIMIT 1
        """),
        {
            "client_id": payload.client_id,
            "app_id": payload.app_id,
        }
    ).mappings().first()

    if not existing:
        raise HTTPException(status_code=404, detail="La suscripción no existe para ese cliente/aplicación")

    db.execute(
        text("""
            UPDATE client_app_subscriptions
            SET status = :status,
                is_enabled = :is_enabled,
                start_date = :start_date,
                end_date = :end_date
            WHERE id = :subscription_id
        """),
        {
            "status": status,
            "is_enabled": 1 if payload.is_enabled else 0,
            "start_date": start_date,
            "end_date": end_date,
            "subscription_id": existing["id"],
        }
    )
    db.commit()

    return {
        "ok": True,
        "message": "Suscripción actualizada correctamente",
        "subscription_id": existing["id"],
        "client_id": payload.client_id,
        "app_id": payload.app_id,
        "status": status,
        "is_enabled": bool(payload.is_enabled),
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None,
    }


@router.post("/internal/admin/update-permission-role")
def internal_admin_update_permission_role(
    payload: AdminUpdatePermissionRolePayload,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    role = (payload.role or "").strip()

    if payload.permission_id <= 0:
        raise HTTPException(status_code=400, detail="permission_id inválido")

    if not role:
        raise HTTPException(status_code=400, detail="El rol es obligatorio")

    allowed_roles = {"member", "app_client_admin"}
    if role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Rol inválido. Valores permitidos: app_client_admin, member"
        )

    existing = db.execute(
        text("""
            SELECT id
            FROM permissions
            WHERE id = :permission_id
            LIMIT 1
        """),
        {"permission_id": payload.permission_id}
    ).fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")

    db.execute(
        text("""
            UPDATE permissions
            SET role = :role
            WHERE id = :permission_id
        """),
        {
            "role": role,
            "permission_id": payload.permission_id,
        }
    )
    db.commit()

    return {
        "ok": True,
        "message": "Rol actualizado correctamente",
        "permission_id": payload.permission_id,
        "role": role,
    }


@router.post("/internal/admin/update-user")
def internal_admin_update_user(
    payload: AdminUpdateUserPayload,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    username_clean = (payload.username or "").strip()
    email_clean = (payload.email or "").strip() or None

    if not username_clean:
        raise HTTPException(status_code=400, detail="El username es obligatorio")

    existing = db.execute(
        text("""
            SELECT id, username
            FROM users
            WHERE id = :user_id
            LIMIT 1
        """),
        {"user_id": payload.user_id}
    ).mappings().first()

    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    duplicate = db.execute(
        text("""
            SELECT id
            FROM users
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(:username))
              AND id <> :user_id
            LIMIT 1
        """),
        {
            "username": username_clean,
            "user_id": payload.user_id,
        }
    ).fetchone()

    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe otro usuario con ese username")

    db.execute(
        text("""
            UPDATE users
            SET username = :username,
                email = :email
            WHERE id = :user_id
        """),
        {
            "username": username_clean,
            "email": email_clean,
            "user_id": payload.user_id,
        }
    )

    admin_row = db.execute(
        text("""
            SELECT 1
            FROM system_admins
            WHERE user_id = :user_id
            LIMIT 1
        """),
        {"user_id": payload.user_id}
    ).fetchone()

    if payload.is_system_admin and not admin_row:
        db.execute(
            text("""
                INSERT INTO system_admins (user_id)
                VALUES (:user_id)
            """),
            {"user_id": payload.user_id}
        )

    if not payload.is_system_admin and admin_row:
        db.execute(
            text("""
                DELETE FROM system_admins
                WHERE user_id = :user_id
            """),
            {"user_id": payload.user_id}
        )

    db.commit()

    return {
        "ok": True,
        "message": "Usuario actualizado correctamente",
        "user_id": payload.user_id,
        "username": username_clean,
        "email": email_clean,
        "is_system_admin": bool(payload.is_system_admin),
    }


@router.post("/internal/admin/create-application")
def internal_admin_create_application(
    payload: AdminCreateApplicationPayload,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    app_name = (payload.app_name or "").strip()
    slug = (payload.slug or "").strip() or None
    internal_url = (payload.internal_url or "").strip() or None
    public_url = (payload.public_url or "").strip()
    entry_path = (payload.entry_path or "").strip() or "/"
    health_path = (payload.health_path or "").strip() or "/health"
    description = (payload.description or "").strip() or None

    if not app_name:
        raise HTTPException(status_code=400, detail="El nombre de la aplicación es obligatorio")

    if not public_url:
        raise HTTPException(status_code=400, detail="public_url es obligatorio")

    if not internal_url:
        raise HTTPException(status_code=400, detail="internal_url es obligatorio")

    duplicate_name = db.execute(
        text("""
            SELECT id
            FROM applications
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(:app_name))
            LIMIT 1
        """),
        {"app_name": app_name}
    ).fetchone()

    if duplicate_name:
        raise HTTPException(status_code=409, detail="Ya existe una aplicación con ese nombre")

    if slug:
        duplicate_slug = db.execute(
            text("""
                SELECT id
                FROM applications
                WHERE LOWER(TRIM(slug)) = LOWER(TRIM(:slug))
                LIMIT 1
            """),
            {"slug": slug}
        ).fetchone()

        if duplicate_slug:
            raise HTTPException(status_code=409, detail="Ya existe una aplicación con ese slug")

    normalized_launch_mode = (payload.launch_mode or "").strip().lower()

    if normalized_launch_mode == "proxy":
        normalized_launch_mode = "dynamic_proxy"

    allowed_launch_modes = {"dynamic_proxy", "redirect"}

    if normalized_launch_mode not in allowed_launch_modes:
        raise HTTPException(
            status_code=400,
            detail="launch_mode inválido. Valores permitidos: dynamic_proxy, redirect"
        )

    db.execute(
        text("""
            INSERT INTO applications (
                name,
                slug,
                internal_url,
                public_url,
                entry_path,
                health_path,
                launch_mode,
                description,
                is_active
            )
            VALUES (
                :app_name,
                :slug,
                :internal_url,
                :public_url,
                :entry_path,
                :health_path,
                :launch_mode,
                :description,
                :is_active
            )
        """),
        {
            "app_name": app_name,
            "slug": slug,
            "internal_url": internal_url,
            "public_url": public_url,
            "entry_path": entry_path,
            "health_path": health_path,
            "launch_mode": normalized_launch_mode,
            "description": description,
            "is_active": 1 if payload.is_enabled else 0,
        }
    )
    db.commit()

    created = db.execute(
        text("""
            SELECT id
            FROM applications
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(:app_name))
            LIMIT 1
        """),
        {"app_name": app_name}
    ).mappings().first()

    return {
        "ok": True,
        "message": "Aplicación creada correctamente",
        "app_id": created["id"] if created else None,
        "app_name": app_name,
        "slug": slug,
        "internal_url": internal_url,
        "public_url": public_url,
        "entry_path": entry_path,
        "health_path": health_path,
        "launch_mode": normalized_launch_mode,
        "description": description,
        "is_enabled": bool(payload.is_enabled),
    }


@router.post("/internal/admin/update-application")
def internal_admin_update_application(
    payload: AdminUpdateApplicationPayload,
    user: str = Depends(require_system_admin),
    db: Session = Depends(get_db),
):
    app_name = (payload.app_name or "").strip()
    slug = (payload.slug or "").strip() or None
    internal_url = (payload.internal_url or "").strip() or None
    public_url = (payload.public_url or "").strip()
    entry_path = (payload.entry_path or "").strip() or "/"
    health_path = (payload.health_path or "").strip() or "/health"
    description = (payload.description or "").strip() or None

    if not app_name:
        raise HTTPException(status_code=400, detail="El nombre de la aplicación es obligatorio")

    if not public_url:
        raise HTTPException(status_code=400, detail="public_url es obligatorio")

    if not internal_url:
        raise HTTPException(status_code=400, detail="internal_url es obligatorio")

    existing = db.execute(
        text("""
            SELECT id
            FROM applications
            WHERE id = :app_id
            LIMIT 1
        """),
        {"app_id": payload.app_id}
    ).fetchone()

    if not existing:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")

    duplicate_name = db.execute(
        text("""
            SELECT id
            FROM applications
            WHERE LOWER(TRIM(name)) = LOWER(TRIM(:app_name))
              AND id <> :app_id
            LIMIT 1
        """),
        {
            "app_name": app_name,
            "app_id": payload.app_id,
        }
    ).fetchone()

    if duplicate_name:
        raise HTTPException(status_code=409, detail="Ya existe otra aplicación con ese nombre")

    if slug:
        duplicate_slug = db.execute(
            text("""
                SELECT id
                FROM applications
                WHERE LOWER(TRIM(slug)) = LOWER(TRIM(:slug))
                  AND id <> :app_id
                LIMIT 1
            """),
            {
                "slug": slug,
                "app_id": payload.app_id,
            }
        ).fetchone()

        if duplicate_slug:
            raise HTTPException(status_code=409, detail="Ya existe otra aplicación con ese slug")

    normalized_launch_mode = (payload.launch_mode or "").strip().lower()

    if normalized_launch_mode == "proxy":
        normalized_launch_mode = "dynamic_proxy"

    allowed_launch_modes = {"dynamic_proxy", "redirect"}

    if normalized_launch_mode not in allowed_launch_modes:
        raise HTTPException(
            status_code=400,
            detail="launch_mode inválido. Valores permitidos: dynamic_proxy, redirect"
        )

    db.execute(
        text("""
            UPDATE applications
            SET name = :app_name,
                slug = :slug,
                internal_url = :internal_url,
                public_url = :public_url,
                entry_path = :entry_path,
                health_path = :health_path,
                launch_mode = :launch_mode,
                description = :description,
                is_active = :is_active
            WHERE id = :app_id
        """),
        {
            "app_name": app_name,
            "slug": slug,
            "internal_url": internal_url,
            "public_url": public_url,
            "entry_path": entry_path,
            "health_path": health_path,
            "launch_mode": normalized_launch_mode,
            "description": description,
            "is_active": 1 if payload.is_enabled else 0,
            "app_id": payload.app_id,
        }
    )
    db.commit()

    return {
        "ok": True,
        "message": "Aplicación actualizada correctamente",
        "app_id": payload.app_id,
        "app_name": app_name,
        "slug": slug,
        "internal_url": internal_url,
        "public_url": public_url,
        "entry_path": entry_path,
        "health_path": health_path,
        "launch_mode": normalized_launch_mode,
        "description": description,
        "is_enabled": bool(payload.is_enabled),
    }


@router.post("/internal/admin/create-permission")
def internal_admin_create_permission(
    payload: AdminCreatePermissionPayload,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    username_clean = (payload.username or "").strip()
    role = (payload.role or "").strip()

    if not username_clean:
        raise HTTPException(status_code=400, detail="El username es obligatorio")

    if role not in {"member", "app_client_admin"}:
        raise HTTPException(status_code=400, detail="Rol inválido")

    actor_is_sysadmin = is_system_admin(db, user)

    if not actor_is_sysadmin:
        scopes = get_admin_scopes(db, user)
        allowed = any(
            int(scope["client_id"]) == int(payload.client_id) and int(scope["app_id"]) == int(payload.app_id)
            for scope in scopes
        )

        if not allowed:
            raise HTTPException(
                status_code=403,
                detail="No tienes alcance administrativo para crear permisos en ese cliente/aplicación"
            )

    target_user = db.execute(
        text("""
            SELECT id, username
            FROM users
            WHERE LOWER(TRIM(username)) = LOWER(TRIM(:username))
            LIMIT 1
        """),
        {"username": username_clean}
    ).mappings().first()

    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_user_id = int(target_user["id"])

    client_exists = db.execute(
        text("SELECT id FROM clients WHERE id = :client_id LIMIT 1"),
        {"client_id": payload.client_id}
    ).fetchone()
    if not client_exists:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    app_exists = db.execute(
        text("SELECT id FROM applications WHERE id = :app_id LIMIT 1"),
        {"app_id": payload.app_id}
    ).fetchone()
    if not app_exists:
        raise HTTPException(status_code=404, detail="Aplicación no encontrada")

    membership = db.execute(
        text("""
            SELECT id
            FROM user_client_memberships
            WHERE user_id = :user_id
              AND client_id = :client_id
            LIMIT 1
        """),
        {
            "user_id": target_user_id,
            "client_id": payload.client_id,
        }
    ).fetchone()

    if not membership:
        raise HTTPException(
            status_code=400,
            detail="El usuario no tiene membresía con ese cliente. Crea primero la membresía."
        )

    duplicate = db.execute(
        text("""
            SELECT id
            FROM permissions
            WHERE user_id = :user_id
              AND client_id = :client_id
              AND app_id = :app_id
            LIMIT 1
        """),
        {
            "user_id": target_user_id,
            "client_id": payload.client_id,
            "app_id": payload.app_id,
        }
    ).fetchone()

    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe un permiso para ese usuario/cliente/aplicación")

    db.execute(
        text("""
            INSERT INTO permissions (user_id, client_id, app_id, role)
            VALUES (:user_id, :client_id, :app_id, :role)
        """),
        {
            "user_id": target_user_id,
            "client_id": payload.client_id,
            "app_id": payload.app_id,
            "role": role,
        }
    )
    db.commit()

    created = db.execute(
        text("""
            SELECT id
            FROM permissions
            WHERE user_id = :user_id
              AND client_id = :client_id
              AND app_id = :app_id
            LIMIT 1
        """),
        {
            "user_id": target_user_id,
            "client_id": payload.client_id,
            "app_id": payload.app_id,
        }
    ).mappings().first()

    return {
        "ok": True,
        "message": "Permiso creado correctamente",
        "permission_id": created["id"] if created else None,
        "user_id": target_user_id,
        "username": target_user["username"],
        "client_id": payload.client_id,
        "app_id": payload.app_id,
        "role": role,
    }