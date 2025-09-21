from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import get_db
app = FastAPI(title="AuthZ Service")

class UserIn(BaseModel):
    username: str
    email: str
    password: str

class ClientIn(BaseModel):
    name: str

class PermissionIn(BaseModel):
    username: str
    client_id: int
    app_name: str

@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, username, email FROM users")).fetchall()
    return [{"id": r[0], "username": r[1], "email": r[2]} for r in rows]

@app.post("/users")
def create_user(data: UserIn, db: Session = Depends(get_db)):
    db.execute(text("INSERT INTO users (username, email, password) VALUES (:u,:e,:p)"),
               {"u": data.username, "e": data.email, "p": data.password})
    db.commit()
    return {"status": "ok"}

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM users WHERE id=:i"), {"i": user_id})
    db.commit()
    return {"status": "ok"}

@app.get("/clients")
def list_clients(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name FROM clients")).fetchall()
    return [{"id": r[0], "name": r[1]} for r in rows]

@app.post("/clients")
def create_client(data: ClientIn, db: Session = Depends(get_db)):
    db.execute(text("INSERT INTO clients (name) VALUES (:n)"), {"n": data.name})
    db.commit()
    return {"status": "ok"}

@app.get("/permissions")
def list_permissions(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT p.id, u.username, c.name AS client, a.name AS app
        FROM permissions p
        JOIN users u ON p.user_id = u.id
        JOIN clients c ON p.client_id = c.id
        JOIN applications a ON p.app_id = a.id
        ORDER BY u.username, a.name, c.name
    """)).fetchall()
    return [{"id": r[0], "username": r[1], "client": r[2], "app": r[3]} for r in rows]

@app.post("/permissions")
def create_permission(data: dict, db: Session = Depends(get_db)):
    # data = {"username":"admin","client_id":1,"app_id":2}
    user = db.execute(text("SELECT id FROM users WHERE username=:u"), {"u": data["username"]}).fetchone()
    if not user:
        raise HTTPException(404, "Usuario no existe")
    db.execute(text("""
        INSERT INTO permissions (user_id, client_id, app_id)
        VALUES (:uid, :cid, :aid)
    """), {"uid": user[0], "cid": data["client_id"], "aid": data["app_id"]})
    db.commit()
    return {"status": "ok"}
