import os
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from db import engine
from pos_routes import router as pos_router

app = FastAPI(title="RodelSoft - POS")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pos_router)

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
