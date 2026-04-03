# RodelSoft Platform — Stack Multi-Apps (FastAPI + React + Express + MySQL + Nginx)

Stack on-prem / Docker Compose para portal multiaplicación con control de acceso por cliente y aplicación.

## Componentes principales

- **gateway (Nginx)**  
  Reverse proxy principal. Expone el portal y enruta apps internas/externas.

- **portal (React/Vite servido por Nginx)**  
  UI principal de acceso, login y lanzador de aplicaciones.

- **app-hija-1 (FastAPI)**  
  Servicio actual de autenticación base / validación JWT / endpoints legacy del portal.

- **app-hija-2 (Express)**  
  App interna de ejemplo / app local enrutable por gateway.

- **rodelsoft-pos (FastAPI)**  
  Aplicación POS con base de datos propia (`pos_db`).

- **launch-service (FastAPI)**  
  Resuelve lanzamientos dinámicos por BD:
  - valida JWT
  - valida permisos
  - consulta `applications`
  - revisa health de la app destino
  - redirige a `public_url + entry_path`

- **authz-service (FastAPI)**  
  Administración mínima de:
  - usuarios
  - clientes
  - memberships por cliente
  - permisos por cliente + app

- **dynamic-app-router (FastAPI)**  
  Gateway dinámico para apps externas bajo convención:
  - `/ext/<slug>/...`

- **mysql (MySQL 8)**  
  Control Plane / IAM / catálogo de aplicaciones / permisos / suscripciones

- **notes external (fuera del stack principal)**  
  App externa real publicada detrás del gateway por ruta `/notes/`

---

## Bases de datos

### 1) `proyecto_db` (Control Plane / IAM)
Contiene tablas principales del ecosistema:

- `users`
- `clients`
- `applications`
- `permissions`
- `client_app_subscriptions`
- `user_client_memberships`
- `system_admins` (si aplica en tu entorno)

### 2) `pos_db`
Base separada para POS.

> Nota: POS ya usa `pos_db` como separación inicial de datos.  
> La transición completa de acceso a catálogo/permisos vía API (en vez de acceso directo a Control Plane) queda para fase posterior.

---

## Puertos habituales (host)

> Pueden variar según tu `docker-compose.yml` actual.  
> Confirmar contra el compose vigente.

- `8080` → gateway (entrada principal)
- `3307` → MySQL host
- `8400` → authz-service (si se expone para Swagger/admin)
- Otros puertos internos dependen del compose

Acceso principal recomendado:

- **Portal / Gateway** → `http://localhost:8080`

---

## Rutas principales del gateway

### Portal
- `/`

### Launch dinámico
- `/launch`
- `/launch-health`
- `/app-unavailable`

### Apps internas
- `/app1/`
- `/app2/`
- `/pos/`

### Apps externas
- `/notes/`
- `/ext/<slug>/...`

### Admin / soporte
- `/authz/`
- `/healthz` (health del gateway)

---

## SQL de arranque (orden lógico)

Los nombres reales deben respetar lo que tengas en `database/init/` o la carpeta vigente del repo.  
Validar contra el árbol actual.

Orden recomendado:

1. `10-schema.sql`
   - estructura base de `proyecto_db`
   - incluye tablas de control plane / IAM

2. `20-seed.sql`
   - datos semilla mínimos
   - usuarios iniciales
   - clientes
   - applications
   - memberships/permisos base si aplica

3. Scripts de migración posteriores (si existen)
   - por ejemplo: suscripciones / endurecimiento / columnas nuevas

> Si el entorno ya existe, no asumir que todos los scripts son reejecutables sin revisión.

---

## FASE 9 — Endurecimiento (estado operativo actual)

### Ya aplicado / esperado en entorno actual
- Passwords de usuarios en **bcrypt**
- `authz-service` crea usuarios con password **hasheado**
- Endpoints admin de `authz-service` protegidos con **`X-Admin-Key`**
- Swagger de `authz-service` opcional por env:
  - `AUTHZ_ENABLE_DOCS=true|false`
- `authz-service` expone `/health`
- `launch-service` expone `/health`
- `dynamic-app-router` expone `/health`
- `gateway` expone `/healthz`
- `permissions` en `authz-service` requiere **membership activa** previa en `user_client_memberships`

### Pendiente intencional (fuera del cierre mínimo de Fase 9)
- migraciones versionadas formales (Alembic o equivalente)
- rotación/gestión robusta de secretos
- transición completa POS → API de Control Plane
- endurecimiento profundo de concurrencia POS
- auditoría operativa completa
- backups/restore versionados y probados en repo

---

## Variables de entorno importantes

### Gateway / Portal
- revisar `docker-compose.yml` actual y `.env`

### App1 / Auth base
- `SECRET_KEY`
- variables DB
- configuración JWT/cookies

### AuthZ
- `AUTHZ_ADMIN_KEY`  
  **Obligatoria** para endpoints administrativos
- `AUTHZ_ENABLE_DOCS=true|false`

> Recomendación:
> No dejar secretos reales como default en `docker-compose.yml` si el repo es público.  
> Definirlos en `.env`.

---

## Operación rápida

### Levantar stack
```bash
docker compose up -d --build