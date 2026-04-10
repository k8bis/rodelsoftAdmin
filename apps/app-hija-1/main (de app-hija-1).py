# apps/app-hija-1/main.py
import time
from fastapi import FastAPI
from sqlalchemy import text

from db import engine
from routes.public import router as public_router
from routes.internal import router as internal_router
from routes.admin import router as admin_router

app = FastAPI(title="App Hija 1 - FastAPI")


@app.on_event("startup")
def _startup():
    retries = 20
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as e:
            if i == retries - 1:
                print(f"[startup] DB no disponible: {e}")
            else:
                print(f"[startup] Esperando DB... intento {i+1}/{retries}")
                time.sleep(2)


app.include_router(public_router)
app.include_router(internal_router)
app.include_router(admin_router)