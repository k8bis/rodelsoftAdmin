import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, Header
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import get_db, Category, Product, Sale, SaleItem
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


def render_pos_html(
    request: Request,
    user: str,
    db: Session,
    x_app_id: int | None,
    x_client_id: int | None,
) -> HTMLResponse:
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)

    if not app_id or not client_id:
        raise HTTPException(status_code=400, detail="Faltan app_id o client_id")

    validate_permission(db, user, app_id, client_id)

    app_info = db.execute(
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

    # Si no vienen por env, usamos defaults sanos
    app_menu_url = os.getenv("APP_MENU_URL", "/app1/my/apps")
    logout_redirect_url = os.getenv("LOGOUT_REDIRECT_URL", "/")

    template_path = Path(__file__).resolve().parent / "templates" / "pos_template.html"
    if not template_path.exists():
        raise HTTPException(status_code=500, detail="Template de POS no encontrado")

    html_content = template_path.read_text(encoding="utf-8")

    html_content = html_content.replace("__APP_NAME__", app_name)
    html_content = html_content.replace("__CLIENT_NAME__", client_name)
    html_content = html_content.replace("__USER__", user)
    html_content = html_content.replace("__APP_MENU_URL__", app_menu_url)
    html_content = html_content.replace("__LOGOUT_REDIRECT_URL__", logout_redirect_url)
    html_content = html_content.replace("__APP_BASE_PATH__", APP_BASE_PATH)

    print("[POS] APP_BASE_PATH =", APP_BASE_PATH)
    print("[POS] APP_MENU_URL =", app_menu_url)
    print("[POS] LOGOUT_REDIRECT_URL =", logout_redirect_url)
    print("[POS] HTML placeholders check =>",
        "__APP_BASE_PATH__" in html_content,
        "__APP_MENU_URL__" in html_content,
        "__LOGOUT_REDIRECT_URL__" in html_content)

    return HTMLResponse(content=html_content)


# =========================
# Health
# =========================
@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        now = db.execute(text("SELECT NOW()")).fetchone()[0]
        return {"status": "ok", "db_time": str(now)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")


# =========================
# UI principal (soporta / y /pos)
# =========================
@router.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    return render_pos_html(request, user, db, x_app_id, x_client_id)


@router.get("/pos", response_class=HTMLResponse)
def pos_interface(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    return render_pos_html(request, user, db, x_app_id, x_client_id)


# =========================
# Logout (soporta /logout y /pos/logout)
# =========================
@router.post("/logout")
def logout():
    response = RedirectResponse(url=os.getenv("LOGOUT_REDIRECT_URL", "/"), status_code=302)
    response.delete_cookie("jwt", path="/")
    return response


@router.post("/pos/logout")
def logout_pos():
    response = RedirectResponse(url=os.getenv("LOGOUT_REDIRECT_URL", "/"), status_code=302)
    response.delete_cookie("jwt", path="/")
    return response


# =========================
# Apps menu (opcional)
# =========================
@router.get("/apps-menu")
def apps_menu():
    return RedirectResponse(url=os.getenv("APP_MENU_URL", "/app1/my/apps"), status_code=302)


@router.get("/pos/apps-menu")
def apps_menu_pos():
    return RedirectResponse(url=os.getenv("APP_MENU_URL", "/app1/my/apps"), status_code=302)


# =========================
# Info / entry
# =========================
@router.get("/me")
def me(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    return {
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
    }


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

    validate_permission(db, user, app_id, client_id)

    return {
        "ok": True,
        "user": user,
        "app_id": app_id,
        "client_id": client_id,
        "note": "RodelSoft POS /entry OK",
    }


# =========================
# API - categorías
# Soporta /api/... y /pos/api/...
# =========================
@router.get("/api/categories", response_model=List[CategoryResponse])
@router.get("/pos/api/categories", response_model=List[CategoryResponse])
def get_categories(
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    return db.query(Category).filter(Category.is_active == True).all()


@router.post("/api/categories", response_model=CategoryResponse)
@router.post("/pos/api/categories", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# =========================
# API - productos
# =========================
@router.get("/api/products", response_model=List[ProductResponse])
@router.get("/pos/api/products", response_model=List[ProductResponse])
def get_products(
    request: Request,
    category_id: int | None = None,
    search: str | None = None,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    query = db.query(Product).filter(Product.is_active == True)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.all()
    result = []
    for product in products:
        product_dict = {**product.__dict__, "category_name": product.category.name if product.category else None}
        result.append(product_dict)
    return result


@router.post("/api/products", response_model=ProductResponse)
@router.post("/pos/api/products", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    category_name = db_product.category.name if db_product.category else None
    return {**db_product.__dict__, "category_name": category_name}


# =========================
# API - ventas
# =========================
@router.post("/api/sales", response_model=SaleResponse)
@router.post("/pos/api/sales", response_model=SaleResponse)
def create_sale(
    sale_data: SaleCreate,
    request: Request,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    total_amount = 0.0
    sale_items = []
    for item in sale_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para {product.name}")

        item_total = product.price * item.quantity
        total_amount += item_total

        sale_items.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "unit_price": product.price,
            "total_price": item_total,
        })

        product.stock_quantity -= item.quantity

    db_sale = Sale(
        total_amount=total_amount,
        payment_method=sale_data.payment_method,
        notes=sale_data.notes,
        items=[SaleItem(**item) for item in sale_items],
    )

    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)

    items_response = []
    for item in db_sale.items:
        items_response.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
        })

    return {
        **db_sale.__dict__,
        "items": items_response,
    }


@router.get("/api/sales", response_model=List[SaleResponse])
@router.get("/pos/api/sales", response_model=List[SaleResponse])
def get_sales(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user: str = Depends(verify_token),
    db: Session = Depends(get_db),
    x_app_id: int | None = Header(alias="X-App-Id", default=None),
    x_client_id: int | None = Header(alias="X-Client-Id", default=None),
):
    app_id, client_id = resolve_context(request, x_app_id, x_client_id)
    if app_id and client_id:
        validate_permission(db, user, app_id, client_id)

    sales = db.query(Sale).order_by(Sale.created_at.desc()).limit(limit).offset(offset).all()
    result = []

    for sale in sales:
        items_response = []
        for item in sale.items:
            items_response.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product.name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
            })

        result.append({
            **sale.__dict__,
            "items": items_response,
        })

    return result


# =========================
# Endpoint opcional
# =========================
@router.post("/api/init-sample-data")
@router.post("/pos/api/init-sample-data")
def init_sample_data(db: Session = Depends(get_db)):
    return {"status": "ok", "message": "Init data endpoint"}