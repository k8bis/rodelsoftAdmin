import os
import time
from sqlalchemy import create_engine, text, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "proyecto_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "proyecto_pass")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "proyecto_db")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "30"))
RETRY_DELAY = float(os.getenv("DB_RETRY_DELAY", "2"))

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

def wait_for_db():
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[DB] Conexión OK en intento {attempt}")
            return
        except Exception as e:
            last_error = e
            print(f"[DB] Intento {attempt}/{MAX_RETRIES} falló: {e}")
            time.sleep(RETRY_DELAY)

    raise RuntimeError(f"No se pudo conectar a MySQL tras {MAX_RETRIES} intentos: {last_error}")

wait_for_db()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos para el Punto de Venta

class Category(Base):
    __tablename__ = "pos_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), default="#0066FF")  # Color hex para UI
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "pos_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    cost = Column(Float, default=0.0)
    sku = Column(String(50), unique=True, nullable=True)
    barcode = Column(String(50), unique=True, nullable=True)
    category_id = Column(Integer, ForeignKey("pos_categories.id"), nullable=True)
    stock_quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")

class Sale(Base):
    __tablename__ = "pos_sales"

    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    payment_method = Column(String(50), default="cash")  # cash, card, transfer
    status = Column(String(20), default="completed")  # pending, completed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

class SaleItem(Base):
    __tablename__ = "pos_sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("pos_sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("pos_products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")