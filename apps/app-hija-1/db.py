import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "proyecto_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
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