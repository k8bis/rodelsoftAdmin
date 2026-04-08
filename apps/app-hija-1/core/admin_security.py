# apps/app-hija-1/core/admin_security.py
from fastapi import Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from db import get_db
from core.auth import verify_token


def is_system_admin(db: Session, username: str) -> bool:
    """
    Verifica si el usuario pertenece al catálogo de administradores globales.
    MVP de seguridad para /internal/admin/*
    """
    row = db.execute(
        text("""
            SELECT 1
            FROM system_admins sa
            JOIN users u
              ON u.id = sa.user_id
            WHERE u.username = :username
            LIMIT 1
        """),
        {"username": username}
    ).fetchone()

    return row is not None


def require_system_admin(
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
) -> str:
    """
    Dependency reutilizable para endurecer endpoints administrativos internos.
    """
    if not is_system_admin(db, user):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores del sistema")

    return user


def get_admin_scopes(db: Session, username: str) -> list[dict]:
    """
    Devuelve los alcances administrativos funcionales del usuario
    basados en permissions.role = 'app_client_admin'.
    Alcance = (client_id, app_id)
    """
    rows = db.execute(
        text("""
            SELECT
                p.client_id,
                c.name AS client_name,
                p.app_id,
                a.name AS app_name
            FROM permissions p
            JOIN users u
              ON u.id = p.user_id
            JOIN clients c
              ON c.id = p.client_id
            JOIN applications a
              ON a.id = p.app_id
            WHERE u.username = :username
              AND p.role = 'app_client_admin'
            ORDER BY c.name, a.name
        """),
        {"username": username}
    ).mappings().all()

    return [
        {
            "client_id": r["client_id"],
            "client_name": r["client_name"],
            "app_id": r["app_id"],
            "app_name": r["app_name"],
        }
        for r in rows
    ]


def has_any_admin_scope(db: Session, username: str) -> bool:
    """
    True si el usuario es system_admin o tiene al menos un permissions.role='app_client_admin'
    """
    if is_system_admin(db, username):
        return True

    row = db.execute(
        text("""
            SELECT 1
            FROM permissions p
            JOIN users u
              ON u.id = p.user_id
            WHERE u.username = :username
              AND p.role = 'app_client_admin'
            LIMIT 1
        """),
        {"username": username}
    ).fetchone()

    return row is not None


def can_admin_client(db: Session, username: str, client_id: int) -> bool:
    """
    True si:
    - es system_admin
    - o tiene al menos un permission.role='app_client_admin' en ese cliente
    """
    if is_system_admin(db, username):
        return True

    row = db.execute(
        text("""
            SELECT 1
            FROM permissions p
            JOIN users u
              ON u.id = p.user_id
            WHERE u.username = :username
              AND p.client_id = :client_id
              AND p.role = 'app_client_admin'
            LIMIT 1
        """),
        {
            "username": username,
            "client_id": client_id,
        }
    ).fetchone()

    return row is not None


def require_admin_module_access(
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
) -> str:
    """
    Permite acceso al módulo admin si:
    - system_admin
    - o tiene al menos un scope administrativo funcional
    """
    if not has_any_admin_scope(db, user):
        raise HTTPException(status_code=403, detail="Acceso restringido al módulo de administración")

    return user


def require_admin_scope_for_client(
    client_id: int,
    user: str,
    db: Session,
) -> None:
    """
    Enforcement reutilizable por cliente para endpoints admin.
    """
    if not can_admin_client(db, user, client_id):
        raise HTTPException(status_code=403, detail="No tienes alcance administrativo para ese cliente")