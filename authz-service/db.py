import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "proyecto_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "proyecto_pass")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "proyecto_db")
URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
engine = create_engine(URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
