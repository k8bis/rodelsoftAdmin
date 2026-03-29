import os
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from db import pos_engine, control_engine
from pos_routes import router as pos_router

app = FastAPI(title="RodelSoft - POS")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(pos_router)

def wait_engine(engine_to_check, label: str, retries: int = 20):
    for i in range(retries):
        try:
            with engine_to_check.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[startup] DB {label} OK")
            return
        except Exception as e:
            if i == retries - 1:
                print(f"[startup] DB {label} no disponible: {e}")
            else:
                print(f"[startup] Esperando DB {label}... intento {i+1}/{retries}")
                time.sleep(2)

@app.on_event("startup")
def _startup():
    wait_engine(pos_engine, "POS")
    wait_engine(control_engine, "CONTROL")