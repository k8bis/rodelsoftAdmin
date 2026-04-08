import os
import time
from sqlalchemy import create_engine, text, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.sql import func

# =========================
# Configuración DB de negocio (POS)
# =========================
POS_MYSQL_HOST = os.getenv("POS_MYSQL_HOST", "mysql")
POS_MYSQL_PORT = int(os.getenv("POS_MYSQL_PORT", "3306"))
POS_MYSQL_USER = os.getenv("POS_MYSQL_USER", "proyecto_user")
POS_MYSQL_PASSWORD = os.getenv("POS_MYSQL_PASSWORD")
POS_MYSQL_DATABASE = os.getenv("POS_MYSQL_DATABASE", "pos_db")

POS_DATABASE_URL = (
    f"mysql+pymysql://{POS_MYSQL_USER}:{POS_MYSQL_PASSWORD}"
    f"@{POS_MYSQL_HOST}:{POS_MYSQL_PORT}/{POS_MYSQL_DATABASE}"
)

MAX_RETRIES = int(os.getenv("DB_MAX_RETRIES", "30"))
RETRY_DELAY = float(os.getenv("DB_RETRY_DELAY", "2"))

# =========================
# Engine POS
# =========================
pos_engine = create_engine(
    POS_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    future=True,
)

# Compatibilidad temporal con código existente
engine = pos_engine

def wait_for_db(engine_to_check, label: str):
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with engine_to_check.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[DB:{label}] Conexión OK en intento {attempt}")
            return
        except Exception as e:
            last_error = e
            print(f"[DB:{label}] Intento {attempt}/{MAX_RETRIES} falló: {e}")
            time.sleep(RETRY_DELAY)

    raise RuntimeError(f"No se pudo conectar a MySQL ({label}) tras {MAX_RETRIES} intentos: {last_error}")

# Esperar solo POS DB
wait_for_db(pos_engine, "POS")

PosSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=pos_engine, future=True)

Base = declarative_base()

def get_pos_db():
    db = PosSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Compatibilidad temporal con imports existentes
def get_db():
    yield from get_pos_db()

# =========================
# Modelos para el Punto de Venta (viven en POS DB)
# =========================

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

    # Multi-tenant persistente
    client_id = Column(Integer, nullable=False, index=True)
    app_id = Column(Integer, nullable=False, index=True)
    created_by = Column(String(100), nullable=False, index=True)

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