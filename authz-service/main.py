import os
import secrets
import bcrypt

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import get_db


# =========================================================
# Configuración de seguridad (FASE 9.2.4 + FASE 9.3)
# =========================================================

AUTHZ_ADMIN_KEY = os.getenv("AUTHZ_ADMIN_KEY", "").strip()
AUTHZ_ENABLE_DOCS = os.getenv("AUTHZ_ENABLE_DOCS", "false").strip().lower() == "true"

docs_url = "/docs" if AUTHZ_ENABLE_DOCS else None
redoc_url = "/redoc" if AUTHZ_ENABLE_DOCS else None
openapi_url = "/openapi.json" if AUTHZ_ENABLE_DOCS else None

app = FastAPI(
    title="AuthZ Service",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

# Swagger/OpenAPI security scheme real (FASE 9.2.4)
admin_api_key_header = APIKeyHeader(
    name="X-Admin-Key",
    auto_error=False
)


# =========================================================
# Seguridad admin
# =========================================================

def require_admin_key(x_admin_key: str | None = Depends(admin_api_key_header)):
    """
    Protege endpoints administrativos usando header:
    X-Admin-Key: <valor>

    En 9.2.4 se integra con OpenAPI/Swagger vía APIKeyHeader
    para habilitar botón Authorize.
    """
    if not AUTHZ_ADMIN_KEY:
        # Falla segura: si no está configurada la llave, no permitimos operaciones admin
        raise HTTPException(
            status_code=503,
            detail="AUTHZ admin no configurado: falta AUTHZ_ADMIN_KEY"
        )

    if not x_admin_key or not secrets.compare_digest(x_admin_key, AUTHZ_ADMIN_KEY):
        raise HTTPException(
            status_code=401,
            detail="No autorizado: X-Admin-Key inválido o ausente"
        )

    return True


# =========================================================
# Models
# =========================================================

class UserIn(BaseModel):
    username: str
    email: str
    password: str


class ClientIn(BaseModel):
    name: str


class PermissionIn(BaseModel):
    username: str
    client_id: int
    app_id: int
    role: str = "member"  # member | app_client_admin


class MembershipIn(BaseModel):
    username: str
    client_id: int
    role: str = "member"   # member | client_admin
    status: str = "active" # active | inactive


# =========================================================
# Helpers
# =========================================================

def get_user_by_username(db: Session, username: str):
    return db.execute(
        text("""
            SELECT id, username, email
            FROM users
            WHERE username = :u
            LIMIT 1
        """),
        {"u": username}
    ).mappings().first()


def get_client_by_id(db: Session, client_id: int):
    return db.execute(
        text("""
            SELECT id, name
            FROM clients
            WHERE id = :cid
            LIMIT 1
        """),
        {"cid": client_id}
    ).mappings().first()


def get_app_by_id(db: Session, app_id: int):
    return db.execute(
        text("""
            SELECT id, name, slug
            FROM applications
            WHERE id = :aid
            LIMIT 1
        """),
        {"aid": app_id}
    ).mappings().first()


def get_active_membership(db: Session, user_id: int, client_id: int):
    """
    FASE 9.3:
    Guardrail mínimo para evitar permisos huérfanos o incoherentes.
    El usuario debe pertenecer al cliente y estar activo.
    """
    return db.execute(
        text("""
            SELECT id, user_id, client_id, role, status
            FROM user_client_memberships
            WHERE user_id = :uid
              AND client_id = :cid
              AND status = 'active'
            LIMIT 1
        """),
        {"uid": user_id, "cid": client_id}
    ).mappings().first()


def validate_membership_role(role: str) -> str:
    allowed = {"member", "client_admin"}
    normalized = (role or "").strip().lower()

    if normalized not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"membership.role inválido. Valores permitidos: {sorted(allowed)}"
        )

    return normalized


def validate_membership_status(status: str) -> str:
    allowed = {"active", "inactive"}
    normalized = (status or "").strip().lower()

    if normalized not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"membership.status inválido. Valores permitidos: {sorted(allowed)}"
        )

    return normalized


def validate_permission_role(role: str) -> str:
    allowed = {"member", "app_client_admin"}
    normalized = (role or "").strip().lower()

    if normalized not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"permission.role inválido. Valores permitidos: {sorted(allowed)}"
        )

    return normalized


# =========================================================
# Health
# =========================================================

@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "service": "authz-service",
            "docs_enabled": AUTHZ_ENABLE_DOCS,
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB no disponible: {str(e)}")


# =========================================================
# Users
# =========================================================

@app.get("/users", tags=["users"])
def list_users(
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
            SELECT id, username, email, created_at
            FROM users
            ORDER BY id
        """)
    ).fetchall()

    return [
        {
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "created_at": str(r[3]) if r[3] else None,
        }
        for r in rows
    ]


@app.post("/users", tags=["users"])
def create_user(
    data: UserIn,
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    existing = db.execute(
        text("""
            SELECT id
            FROM users
            WHERE username = :u OR email = :e
            LIMIT 1
        """),
        {"u": data.username, "e": data.email}
    ).fetchone()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un usuario con ese username o email"
        )

    hashed_password = bcrypt.hashpw(
        data.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    db.execute(
        text("""
            INSERT INTO users (username, email, password)
            VALUES (:u, :e, :p)
        """),
        {"u": data.username, "e": data.email, "p": hashed_password}
    )
    db.commit()

    created = db.execute(
        text("""
            SELECT id, username, email, created_at
            FROM users
            WHERE username = :u
            LIMIT 1
        """),
        {"u": data.username}
    ).mappings().first()

    return {
        "status": "ok",
        "user": {
            "id": created["id"],
            "username": created["username"],
            "email": created["email"],
            "created_at": str(created["created_at"]) if created["created_at"] else None,
        } if created else None
    }


@app.delete("/users/{user_id}", tags=["users"])
def delete_user(
    user_id: int,
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    exists = db.execute(
        text("SELECT id FROM users WHERE id = :i LIMIT 1"),
        {"i": user_id}
    ).fetchone()

    if not exists:
        raise HTTPException(status_code=404, detail="Usuario no existe")

    db.execute(text("DELETE FROM users WHERE id = :i"), {"i": user_id})
    db.commit()

    return {"status": "ok"}


# =========================================================
# Clients
# =========================================================

@app.get("/clients", tags=["clients"])
def list_clients(
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
            SELECT id, name, created_at
            FROM clients
            ORDER BY id
        """)
    ).fetchall()

    return [
        {
            "id": r[0],
            "name": r[1],
            "created_at": str(r[2]) if r[2] else None,
        }
        for r in rows
    ]


@app.post("/clients", tags=["clients"])
def create_client(
    data: ClientIn,
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    existing = db.execute(
        text("""
            SELECT id
            FROM clients
            WHERE name = :n
            LIMIT 1
        """),
        {"n": data.name}
    ).fetchone()

    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un cliente con ese nombre")

    db.execute(
        text("INSERT INTO clients (name) VALUES (:n)"),
        {"n": data.name}
    )
    db.commit()

    created = db.execute(
        text("""
            SELECT id, name, created_at
            FROM clients
            WHERE name = :n
            LIMIT 1
        """),
        {"n": data.name}
    ).mappings().first()

    return {
        "status": "ok",
        "client": {
            "id": created["id"],
            "name": created["name"],
            "created_at": str(created["created_at"]) if created["created_at"] else None,
        } if created else None
    }


# =========================================================
# Memberships (user_client_memberships)
# =========================================================

@app.get("/memberships", tags=["memberships"])
def list_memberships(
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
            SELECT
                ucm.id,
                u.username,
                u.email,
                ucm.client_id,
                c.name AS client,
                ucm.role,
                ucm.status,
                ucm.created_at,
                ucm.updated_at
            FROM user_client_memberships ucm
            JOIN users u
              ON u.id = ucm.user_id
            JOIN clients c
              ON c.id = ucm.client_id
            ORDER BY u.username, c.name
        """)
    ).fetchall()

    return [
        {
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "client_id": r[3],
            "client": r[4],
            "role": r[5],
            "status": r[6],
            "created_at": str(r[7]) if r[7] else None,
            "updated_at": str(r[8]) if r[8] else None,
        }
        for r in rows
    ]


@app.post("/memberships", tags=["memberships"])
def create_membership(
    data: MembershipIn,
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    role = validate_membership_role(data.role)
    status = validate_membership_status(data.status)

    user = get_user_by_username(db, data.username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no existe")

    client = get_client_by_id(db, data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no existe")

    existing = db.execute(
        text("""
            SELECT id, role, status
            FROM user_client_memberships
            WHERE user_id = :uid
              AND client_id = :cid
            LIMIT 1
        """),
        {"uid": user["id"], "cid": data.client_id}
    ).mappings().first()

    if existing:
        db.execute(
            text("""
                UPDATE user_client_memberships
                SET role = :role,
                    status = :status
                WHERE id = :id
            """),
            {
                "role": role,
                "status": status,
                "id": existing["id"],
            }
        )
        db.commit()

        updated = db.execute(
            text("""
                SELECT id, user_id, client_id, role, status, created_at, updated_at
                FROM user_client_memberships
                WHERE id = :id
                LIMIT 1
            """),
            {"id": existing["id"]}
        ).mappings().first()

        return {
            "status": "ok",
            "action": "updated",
            "membership": {
                "id": updated["id"],
                "user_id": updated["user_id"],
                "client_id": updated["client_id"],
                "role": updated["role"],
                "status": updated["status"],
                "created_at": str(updated["created_at"]) if updated["created_at"] else None,
                "updated_at": str(updated["updated_at"]) if updated["updated_at"] else None,
            } if updated else None
        }

    db.execute(
        text("""
            INSERT INTO user_client_memberships (user_id, client_id, role, status)
            VALUES (:uid, :cid, :role, :status)
        """),
        {
            "uid": user["id"],
            "cid": data.client_id,
            "role": role,
            "status": status,
        }
    )
    db.commit()

    created = db.execute(
        text("""
            SELECT id, user_id, client_id, role, status, created_at, updated_at
            FROM user_client_memberships
            WHERE user_id = :uid
              AND client_id = :cid
            LIMIT 1
        """),
        {"uid": user["id"], "cid": data.client_id}
    ).mappings().first()

    return {
        "status": "ok",
        "action": "created",
        "membership": {
            "id": created["id"],
            "user_id": created["user_id"],
            "client_id": created["client_id"],
            "role": created["role"],
            "status": created["status"],
            "created_at": str(created["created_at"]) if created["created_at"] else None,
            "updated_at": str(created["updated_at"]) if created["updated_at"] else None,
        } if created else None
    }


# =========================================================
# Permissions
# =========================================================

@app.get("/permissions", tags=["permissions"])
def list_permissions(
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    rows = db.execute(
        text("""
            SELECT
                p.id,
                u.username,
                c.id   AS client_id,
                c.name AS client,
                a.id   AS app_id,
                a.name AS app,
                p.role,
                p.created_at
            FROM permissions p
            JOIN users u
              ON p.user_id = u.id
            JOIN clients c
              ON p.client_id = c.id
            JOIN applications a
              ON p.app_id = a.id
            ORDER BY u.username, a.name, c.name
        """)
    ).fetchall()

    return [
        {
            "id": r[0],
            "username": r[1],
            "client_id": r[2],
            "client": r[3],
            "app_id": r[4],
            "app": r[5],
            "role": r[6],
            "created_at": str(r[7]) if r[7] else None,
        }
        for r in rows
    ]


@app.post("/permissions", tags=["permissions"])
def create_permission(
    data: PermissionIn,
    _admin=Depends(require_admin_key),
    db: Session = Depends(get_db)
):
    role = validate_permission_role(data.role)

    user = get_user_by_username(db, data.username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no existe")

    client = get_client_by_id(db, data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no existe")

    app_row = get_app_by_id(db, data.app_id)
    if not app_row:
        raise HTTPException(status_code=404, detail="Aplicación no existe")

    # =========================================================
    # FASE 9.3 Guardrail:
    # No permitir permisos si el usuario no pertenece ACTIVO al cliente
    # =========================================================
    membership = get_active_membership(db, user["id"], data.client_id)
    if not membership:
        raise HTTPException(
            status_code=409,
            detail="No se puede asignar permiso: el usuario no tiene membership ACTIVA para ese cliente"
        )

    existing = db.execute(
        text("""
            SELECT id, role
            FROM permissions
            WHERE user_id = :uid
              AND client_id = :cid
              AND app_id = :aid
            LIMIT 1
        """),
        {
            "uid": user["id"],
            "cid": data.client_id,
            "aid": data.app_id,
        }
    ).mappings().first()

    if existing:
        db.execute(
            text("""
                UPDATE permissions
                SET role = :role
                WHERE id = :id
            """),
            {
                "role": role,
                "id": existing["id"],
            }
        )
        db.commit()

        updated = db.execute(
            text("""
                SELECT id, user_id, client_id, app_id, role, created_at
                FROM permissions
                WHERE id = :id
                LIMIT 1
            """),
            {"id": existing["id"]}
        ).mappings().first()

        return {
            "status": "ok",
            "action": "updated",
            "permission": {
                "id": updated["id"],
                "user_id": updated["user_id"],
                "client_id": updated["client_id"],
                "app_id": updated["app_id"],
                "role": updated["role"],
                "created_at": str(updated["created_at"]) if updated["created_at"] else None,
            } if updated else None
        }

    db.execute(
        text("""
            INSERT INTO permissions (user_id, client_id, app_id, role)
            VALUES (:uid, :cid, :aid, :role)
        """),
        {
            "uid": user["id"],
            "cid": data.client_id,
            "aid": data.app_id,
            "role": role,
        }
    )
    db.commit()

    created = db.execute(
        text("""
            SELECT id, user_id, client_id, app_id, role, created_at
            FROM permissions
            WHERE user_id = :uid
              AND client_id = :cid
              AND app_id = :aid
            LIMIT 1
        """),
        {
            "uid": user["id"],
            "cid": data.client_id,
            "aid": data.app_id,
        }
    ).mappings().first()

    return {
        "status": "ok",
        "action": "created",
        "permission": {
            "id": created["id"],
            "user_id": created["user_id"],
            "client_id": created["client_id"],
            "app_id": created["app_id"],
            "role": created["role"],
            "created_at": str(created["created_at"]) if created["created_at"] else None,
        } if created else None
    }