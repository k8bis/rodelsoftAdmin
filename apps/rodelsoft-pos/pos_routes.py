import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import get_pos_db, get_control_db, Category, Product, Sale, SaleItem
from auth import verify_token
from permissions import resolve_context, validate_permission
from schemas import (
    CategoryCreate,
    CategoryResponse,
    ProductCreate,
    ProductResponse,
    SaleCreate,
    SaleResponse,
)

router = APIRouter()

# =========================
# Configuración base de rutas
# =========================
APP_BASE_PATH = os.getenv("APP_BASE_PATH", "/pos")
APP_MENU_URL = os.getenv("APP_MENU_URL", "/")
LOGOUT_URL = os.getenv("LOGOUT_URL", f"{APP_BASE_PATH}/logout")
LOGIN_FALLBACK_URL = os.getenv("LOGIN_FALLBACK_URL", "/")
SESSION_CHECK_URL = os.getenv("SESSION_CHECK_URL", f"{APP_BASE_PATH}/session-check")


def get_user_or_redirect(
    request: Request,
    authorization: str | None = None,
) -> str | None:
    """
    Validación browser-safe:
    - Si el token es válido => devuelve username
    - Si no existe / expiró / es inválido => devuelve None
    """
    token = None

    # 1) Header Authorization (inyectado por Nginx)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    # 2) Fallback: cookie jwt
    if not token:
        token = request.cookies.get("jwt")

    if not token:
        return None

    try:
        user = verify_token(request, authorization)
        return user
    except HTTPException:
        return None


def render_pos_html(
    request: Request,
    user: str,
    control_db: Session,
    x_app_id: int | None,
    x_client_id: int | None,
) -> HTMLResponse:
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)

    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(control_db, user, app_id, client_id)

    app_info = control_db.execute(
        text("""
            SELECT a.name AS app,
                   c.name AS client_name
            FROM applications a
            JOIN permissions s ON a.id = s.app_id
            JOIN clients c ON c.id = s.client_id
            JOIN users u ON u.id = s.user_id
            WHERE a.id = :app_id
              AND s.client_id = :client_id
              AND u.username = :username
            LIMIT 1
        """),
        {"app_id": app_id, "client_id": client_id, "username": user},
    ).fetchone()

    app_name = app_info.app if app_info else "POS"
    client_name = app_info.client_name if app_info else "Cliente"

    app_menu_url = APP_MENU_URL
    logout_url = LOGOUT_URL
    login_fallback_url = LOGIN_FALLBACK_URL
    session_check_url = SESSION_CHECK_URL

    template_path = Path(__file__).resolve().parent / "templates" / "pos_template.html"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Template de POS no encontrado")

    html_content = template_path.read_text(encoding="utf-8")

    html_content = html_content.replace("__APP_NAME__", app_name)
    html_content = html_content.replace("__CLIENT_NAME__", client_name)
    html_content = html_content.replace("__USER__", user)
    html_content = html_content.replace("__APP_MENU_URL__", app_menu_url)
    html_content = html_content.replace("__LOGOUT_URL__", logout_url)
    html_content = html_content.replace("__LOGIN_FALLBACK_URL__", login_fallback_url)
    html_content = html_content.replace("__SESSION_CHECK_URL__", session_check_url)
    html_content = html_content.replace("__APP_BASE_PATH__", APP_BASE_PATH)
    # Compatibilidad temporal Fase 5.2
    html_content = html_content.replace("__LOGOUT_REDIRECT_URL__", login_fallback_url)

    print("[POS] APP_BASE_PATH =", APP_BASE_PATH)
    print("[POS] APP_MENU_URL =", app_menu_url)
    print("[POS] LOGOUT_URL =", logout_url)
    print("[POS] LOGIN_FALLBACK_URL =", login_fallback_url)
    print("[POS] SESSION_CHECK_URL =", session_check_url)
    print("[POS] HTML placeholders check =>",
        "__APP_BASE_PATH__" in html_content,
        "__APP_MENU_URL__" in html_content,
        "__LOGOUT_REDIRECT_URL__" in html_content)

    response = HTMLResponse(content=html_content)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# =========================
# Health
# =========================
@router.get("/health")
def health(db: Session = Depends(get_pos_db)):
    try:
        now = db.execute(text("SELECT NOW()")).fetchone()[0]
        return {"status": "ok", "db_time": str(now)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


# =========================
# UI principal (soporta / y /pos)
# IMPORTANTE:
# NO usar Depends(verify_token) aquí para evitar JSON {"detail":"No token"}
# al navegar con botón Atrás del browser.
# =========================
@router.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    control_db: Session = Depends(get_control_db),
    authorization: str | None = Header(default=None),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    user = get_user_or_redirect(request, authorization)
    if not user:
        return RedirectResponse(url=LOGIN_FALLBACK_URL, status_code=302)

    return render_pos_html(request, user, control_db, x_app_id, x_client_id)

@router.get("/pos", response_class=HTMLResponse)
def pos_interface(
    request: Request,
    control_db: Session = Depends(get_control_db),
    authorization: str | None = Header(default=None),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    user = get_user_or_redirect(request, authorization)
    if not user:
        return RedirectResponse(url=LOGIN_FALLBACK_URL, status_code=302)

    return render_pos_html(request, user, control_db, x_app_id, x_client_id)


# =========================
# Logout (soporta /logout y /pos/logout)
# =========================
@router.post("/logout")
def logout():
    response = RedirectResponse(url=LOGIN_FALLBACK_URL, status_code=302)
    response.delete_cookie("jwt", path="/")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.post("/pos/logout")
def logout_pos():
    response = RedirectResponse(url=LOGIN_FALLBACK_URL, status_code=302)
    response.delete_cookie("jwt", path="/")
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# =========================
# Apps menu (opcional)
# =========================
@router.get("/apps-menu")
def apps_menu():
    return RedirectResponse(url=APP_MENU_URL, status_code=302)


@router.get("/pos/apps-menu")
def apps_menu_pos():
    return RedirectResponse(url=APP_MENU_URL, status_code=302)


# =========================
# Sesión / contexto
# =========================
@router.get("/me")
def me(
    user: str = Depends(verify_token),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    return {"user": user, "app_id": x_app_id, "client_id": x_client_id}


@router.get("/session-check")
def session_check(
    request: Request,
    authorization: str | None = Header(default=None),
):
    """
    Chequeo browser-safe para sesión:
    - Si el token es válido => ok
    - Si no existe / expiró / es inválido => redirect al login
    """
    user = get_user_or_redirect(request, authorization)
    if not user:
        return RedirectResponse(url=LOGIN_FALLBACK_URL, status_code=302)

    return {"ok": True}


@router.get("/entry")
def entry(
    request: Request,
    user: str = Depends(verify_token),
    control_db: Session = Depends(get_control_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(control_db, user, app_id, client_id)

    return {"ok": True, "user": user, "app_id": app_id, "client_id": client_id}


# =========================
# Categorías
# =========================
@router.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(
    request: Request,
    user: str = Depends(verify_token),
    pos_db: Session = Depends(get_pos_db),
    control_db: Session = Depends(get_control_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(control_db, user, app_id, client_id)

    return pos_db.query(Category).filter(Category.is_active == True).all()


@router.post("/api/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    request: Request,
    user: str = Depends(verify_token),
    pos_db: Session = Depends(get_pos_db),
    control_db: Session = Depends(get_control_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(control_db, user, app_id, client_id)

    category = Category(name=data.name)
    pos_db.add(category)
    pos_db.commit()
    pos_db.refresh(category)
    return category


# =========================
# Productos
# =========================
@router.get("/api/products", response_model=List[ProductResponse])
def get_products(
    request: Request,
    user: str = Depends(verify_token),
    pos_db: Session = Depends(get_pos_db),
    control_db: Session = Depends(get_control_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(control_db, user, app_id, client_id)

    rows = (
        pos_db.query(Product, Category.name.label("category_name"))
        .outerjoin(Category, Product.category_id == Category.id)
        .filter(Product.is_active == True)
        .all()
    )

    return [
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price) if product.price is not None else 0.0,
            "cost": float(product.cost) if getattr(product, "cost", None) is not None else 0.0,
            "sku": getattr(product, "sku", None) or "",
            "barcode": getattr(product, "barcode", None) or "",
            "stock_quantity": product.stock_quantity if product.stock_quantity is not None else 0,
            "min_stock": getattr(product, "min_stock", None) if getattr(product, "min_stock", None) is not None else 0,
            "image_url": getattr(product, "image_url", None),
            "category_id": product.category_id,
            "category_name": category_name,
            "is_active": bool(product.is_active),
        }
        for product, category_name in rows
    ]

@router.post("/api/products", response_model=ProductResponse)
def create_product(
    data: ProductCreate,
    request: Request,
    user: str = Depends(verify_token),
    pos_db: Session = Depends(get_pos_db),
    control_db: Session = Depends(get_control_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(control_db, user, app_id, client_id)

    category = None
    if data.category_id is not None:
        category = pos_db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        cost=data.cost,
        sku=data.sku,
        barcode=data.barcode,
        stock_quantity=data.stock_quantity,
        min_stock=data.min_stock,
        category_id=data.category_id,
    )
    pos_db.add(product)
    pos_db.commit()
    pos_db.refresh(product)
    return product


# =========================
# Ventas
# =========================
@router.post("/api/sales", response_model=SaleResponse)
def create_sale(
    data: SaleCreate,
    request: Request,
    user: str = Depends(verify_token),
    pos_db: Session = Depends(get_pos_db),
    control_db: Session = Depends(get_control_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(control_db, user, app_id, client_id)

    if not data.items:
        raise HTTPException(status_code=400, detail="La venta debe contener al menos un producto")

    try:
        total = 0.0
        sale_items = []

        # 1) Validación previa y cálculo
        for item in data.items:
            product = pos_db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado")

            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para {product.name}. Disponible: {product.stock_quantity}",
                )

            item_total = float(product.price) * item.quantity
            total += item_total

            sale_items.append({
                "product": product,
                "product_name": product.name,
                "quantity": item.quantity,
                "unit_price": float(product.price),
                "total_price": item_total,
            })

        # 2) Crear cabecera
        sale = Sale(
            client_id=client_id,
            app_id=app_id,
            created_by=user,
            total_amount=total,
            payment_method=data.payment_method,
            notes=data.notes,
        )
        
        pos_db.add(sale)
        pos_db.flush()

        created_items = []

        # 3) Crear detalle + descontar stock
        for item in sale_items:
            product = item["product"]
            product.stock_quantity -= item["quantity"]

            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                total_price=item["total_price"],
            )
            pos_db.add(sale_item)
            pos_db.flush()

            created_items.append({
                "id": sale_item.id,
                "product_id": product.id,
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "total_price": item["total_price"],
            })

        # 4) Confirmar transacción
        pos_db.commit()
        pos_db.refresh(sale)

        return {
            "id": sale.id,
            "client_id": sale.client_id,
            "app_id": sale.app_id,
            "created_by": sale.created_by,
            "total_amount": float(sale.total_amount) if sale.total_amount is not None else 0.0,
            "tax_amount": float(getattr(sale, "tax_amount", 0.0) or 0.0),
            "discount_amount": float(getattr(sale, "discount_amount", 0.0) or 0.0),
            "payment_method": sale.payment_method,
            "status": getattr(sale, "status", None) or "completed",
            "notes": sale.notes,
            "created_at": sale.created_at,
            "items": created_items,
        }

    except HTTPException:
        pos_db.rollback()
        raise
    except Exception as e:
        pos_db.rollback()
        print(f"[POS] Error inesperado en create_sale: {e}")
        raise HTTPException(status_code=500, detail="Error interno al procesar la venta")