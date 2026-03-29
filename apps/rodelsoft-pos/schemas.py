from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

# Modelos Pydantic para API
class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#0066FF"

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    is_active: bool

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    cost: float = 0.0
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    stock_quantity: int = 0
    min_stock: int = 0

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    cost: float
    sku: Optional[str]
    barcode: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str]
    stock_quantity: int
    min_stock: int
    is_active: bool
    image_url: Optional[str]

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int

class SaleCreate(BaseModel):
    items: List[SaleItemCreate]
    payment_method: str = "cash"
    notes: Optional[str] = None

class SaleItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

class SaleResponse(BaseModel):
    id: int
    client_id: Optional[int] = None
    app_id: Optional[int] = None
    created_by: Optional[str] = None
    total_amount: float
    tax_amount: float
    discount_amount: float
    payment_method: str
    status: str
    notes: Optional[str]
    created_at: datetime
    items: List[SaleItemResponse]