# apps/app-hija-1/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "proyecto_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "proyecto_pass")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "proyecto_db")

DATABASE_URL = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# pool_pre_ping evita conexiones zombie; recycle evita timeouts
engine = create_engine(
    DATABASE_URL, pool_pre_ping=True, pool_recycle=280
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

