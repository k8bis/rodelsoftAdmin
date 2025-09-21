# Proyecto Multi-Apps (FastAPI + Express + MySQL + Nginx)

Arquitectura on-prem abierta con:
- **App1**: FastAPI (Python)
- **App2**: Express (Node.js)
- **DB**: MySQL 8 (contenedor dedicado)
- **Gateway**: Nginx (rutas `/app1` y `/app2`)

## Requisitos
- Docker y docker-compose
- Puertos libres: `8080` (Nginx), `3307` (MySQL host), `8000` (App1 host), `3002` (App2 host)

## Estructura
database/ # init.sql, schema.sql, seed.sql (se ejecutan al crear el contenedor)
nginx/
├─ nginx.conf
└─ Dockerfile
apps/
├─ app-hija-1/ # FastAPI
│ ├─ Dockerfile
│ ├─ requirements.txt
│ ├─ main.py
│ └─ db.py
└─ app-hija-2/ # Express
├─ Dockerfile
├─ package.json
├─ package-lock.json
├─ .env (opcional, se usan vars de compose)
├─ index.js
└─ db.js
docker-compose.yml
.env
test/test_e2e.py
