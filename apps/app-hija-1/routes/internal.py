# apps/app-hija-1/routes/internal.py
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from db import get_db
from core.auth import verify_token
from core.access import enforce_access, get_context_names, resolve_context
from schemas.auth import InternalAccessCheckResponse, InternalContextInfoResponse

router = APIRouter()


@router.get("/internal/access-check", response_model=InternalAccessCheckResponse)
def internal_access_check(
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

    return {
        "ok": True,
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
    }


@router.get("/internal/context-info", response_model=InternalContextInfoResponse)
def internal_context_info(
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

    app_name, client_name = get_context_names(db, app_id, client_id)

    return {
        "ok": True,
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
        "app_name": app_name,
        "client_name": client_name,
    }