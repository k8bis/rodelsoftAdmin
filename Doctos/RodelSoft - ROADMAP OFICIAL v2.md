# RodelSoft — ROADMAP OFICIAL v2 (estado real actualizado)

> Documento maestro de continuidad para evitar reabrir fases cerradas, reducir retrabajo y mantener el alcance real del proyecto.  
> Esta versión reemplaza a v1 como **fuente de verdad actualizada**.

---

# Reglas maestras de continuidad (obligatorias)

1. **No reabrir fases cerradas** salvo evidencia nueva real.
2. **No mezclar deuda residual** con reapertura de fase.
3. **No asumir alcance**: confirmar contra archivos reales antes de proponer cambios.
4. **Siempre priorizar cambios mínimos y seguros** antes que refactors masivos.
5. **Toda app de negocio debe migrar gradualmente de Control Plane DB → Control Plane API**.
6. **No confundir cierre de subfase con cierre total de fase**.
7. **Mantener compatibilidad** con:
   - launch actual
   - catálogo actual
   - shell actual
   - suscripciones actuales
   - apps externas ya validadas
   - POS funcional actual

---

# ESTADO OFICIAL DEL ROADMAP (FUENTE DE VERDAD)

---

## **FASE 4.2 — Multi-tenant mínimo en POS**
**ESTADO: CERRADA**

### Cierre real
- `pos_sales` ya guarda:
  - `client_id`
  - `app_id`
  - `created_by`
- Ya se refleja en:
  - esquema
  - código
  - operación real de ventas

### Regla
- No reabrir FASE 4.2
- Si más adelante se endurece integridad (FK / migración formal), eso vive en **FASE 9B**

---

## **FASE 4.3 — Separación inicial de DB (Control Plane vs POS)**
**ESTADO: CERRADA + DEUDA RESIDUAL**

### Cierre real
- Existe `pos_db`
- Existe `proyecto_db`
- POS usa `POS_MYSQL_DATABASE`
- POS separa `CONTROL_MYSQL_DATABASE`
- `00-init.sql` y `30-pos-schema.sql` contemplan `pos_db`

### Deuda residual (NO reabre 4.3)
- Migraciones más maduras
- Bootstrap más limpio
- API entre servicios

### La deuda vive en
- **FASE 8** (API)
- **FASE 9B** (hardening / migraciones / bootstrap)

---

## **FASE 4.4 — Prueba de app externa**
**ESTADO: CERRADA**

### Cierre real
- App externa real existe
- Ya se probó
- Ya maduró seguridad / integración
- Ya funciona con:
  - launch
  - proxy
  - shell
  - session-check

### Regla
- No reabrir FASE 4.4

---

## **FASE 4.5 — Decisión de Control Plane**
**ESTADO: CERRADA + DEUDA RESIDUAL**

### Cierre real
- `app-hija-1` opera como **Control Plane / IAM de facto**
- Ownership conceptual resuelto
- El runtime actual ya trabaja bajo esta decisión

### Deuda residual (NO reabre 4.5)
- API formal interna más completa
- Naming / limpieza
- Endurecimiento adicional

### La deuda vive en
- **FASE 8**
- **FASE 9B**

---

## **FASE 5 — UI Shell unificado**
**ESTADO: CERRADA**

### Cierre real
- Shell unificado validado
- Base real:
  - `shared/shared-shell.css`
  - `shared/README-ui-shell.md`
- Incluye cierre efectivo de:
  - FASE 5.1
  - FASE 5.2
  - FASE 5.3
- Validado en:
  - Portal
  - Rodel-POS
  - RodelSoft Notes External

### Regla
- No reabrir FASE 5
- Si aparece algo, tratarlo como:
  - deuda visual puntual
  - cleanup puntual
  - no como reapertura de fase

---

## **FASE 6 — Contratación / suscripción**
**ESTADO: PARCIAL (6A CERRADA / 6B ABIERTA)**

---

### **FASE 6A — Backend / motor / enforcement**
**ESTADO: CERRADA**

#### Cierre real
- Motor de suscripción existe
- `client_app_subscriptions` existe
- Launch y catálogo respetan suscripciones
- `migrate_fase6_subscriptions.sql` existe
- `app-hija-1` devuelve datos de suscripción

#### Regla
- No reabrir FASE 6A

---

### **FASE 6B — UI administrativa de gestión**
**ESTADO: ABIERTA**

#### Pendiente real
- UI para alta / baja de usuarios
- UI para gestión de permisos
- UI para gestión de suscripciones
- CRUDs administrativos asociados

#### Lineamiento de diseño
- Reutilizar el menú ya existente
- Priorizar **modals** en lo posible
- Evitar abrir páginas nuevas innecesarias
- Mantener consistencia con el **UI Shell** ya cerrado en FASE 5

#### Dependencia real
- **Depende funcionalmente de FASE 8**

---

## **FASE 7 — Administración delegada por empresa**
**ESTADO: ABIERTA**

### Base existente
- `permissions`
- `user_client_memberships`
- `client_app_subscriptions`

### Pendiente real
- UI delegada por empresa
- Enforcement administrativo por tenant
- Alta / baja de usuarios por empresa
- Limitar administración a apps contratadas
- Flujo operativo real para admin empresarial

### Regla
- No abrir antes de estabilizar:
  - **FASE 8**
  - y preferentemente **FASE 6B**

---

## **FASE 8 — Control Plane API (transición DB directa → API)**
**ESTADO: ABIERTA (EN EJECUCIÓN)**

### Objetivo real
Eliminar gradualmente las consultas directas desde apps de negocio hacia `proyecto_db` para datos del Control Plane, migrando a consumo por **API interna del Control Plane (`app-hija-1`)**, sin romper el comportamiento actual.

### Alcance oficial de la fase
- Exponer API interna del Control Plane (`app-hija-1`)
- Identificar consultas directas actuales desde apps hacia `proyecto_db`
- Migrar apps para consumir API interna en vez de DB directa
- Mantener compatibilidad con:
  - launch actual
  - multi-tenant actual
  - suscripciones actuales
  - shell actual
  - apps ya funcionales
- No romper:
  - integración externa
  - `dynamic_app_router`
  - `launch_service`

---

### **FASE 8.1 — Primer paquete mínimo POS → Control Plane API**
**ESTADO: CERRADA FUNCIONALMENTE**

#### Objetivo de 8.1
Eliminar el primer bloque de dependencia directa de POS hacia `proyecto_db` para validación de acceso y contexto, migrándolo a **App Hija 1** como **Control Plane API**.

#### Resultado implementado
Se validó que **RodelSoft POS**:

- Mantiene su lógica de negocio en **`pos_db`**
- **Ya no depende de consultas directas a `proyecto_db`** para validación de acceso / contexto
- Consume seguridad mediante **API interna de App Hija 1**
- Sigue operando correctamente dentro del flujo de lanzamiento del portal

#### Endpoints internos ya usados en 8.1
- `GET /internal/access-check`
- `GET /internal/context-info`

#### Validaciones confirmadas
1. **Launch correcto**
   - `app_id=3`
   - `client_id=4`
   - `internal_url=http://rodelsoft-pos:8000`
   - `public_url=/pos/`
   - Health OK
   - Redirect OK

2. **Seguridad desacoplada por API**
   - Confirmado en logs:
     - `GET /internal/access-check -> 200 OK`
     - `GET /internal/context-info -> 200 OK`

3. **Shell / rutas correctas**
   - `/pos/`
   - `/pos/session-check`
   - assets bajo `/pos/static/...`

4. **Catálogo y productos OK**
   - `GET /pos/api/categories -> 200`
   - `GET /pos/api/products -> 200`

5. **Venta OK**
   - `POST /pos/api/sales -> 200`
   - Venta confirmada con folio
   - Stock decrementado correctamente

#### Criterio de cierre
Se considera **cerrada funcionalmente** porque:
- El desacople mínimo de seguridad quedó aplicado
- POS opera sin regresión visible
- Flujo end-to-end validado:
  - launch
  - render
  - session-check
  - categorías
  - productos
  - venta
  - actualización de stock

#### Pendiente técnico menor (no bloqueante)
- **App Hija 1 / Swagger**:
  - warning por `Duplicate Operation ID logout_logout_post`
- Impacto:
  - no rompe funcionalidad
  - no bloquea continuidad
  - conviene limpiar en ajuste menor

#### Regla importante
**El cierre de FASE 8.1 NO cierra FASE 8 completa.**  
Solo cierra el **primer paquete mínimo** de migración POS → Control Plane API.

---

### **FASE 8.2 — Inventario restante de acoplamiento POS → Control Plane**
**ESTADO: ABIERTA (SIGUIENTE SUBFASE RECOMENDADA)**

#### Objetivo
Identificar si aún quedan consultas o dependencias residuales en POS hacia `proyecto_db` fuera del paquete ya migrado en 8.1.

#### Entregables esperados
- Inventario real de accesos residuales
- Confirmación de si:
  - ya no existe dependencia directa adicional
  - o existen casos puntuales pendientes
- Definición del siguiente paquete mínimo de endpoints internos (si aplica)

#### Regla
- No hacer refactor masivo
- Solo cerrar el inventario real y el siguiente paquete mínimo

---

### **FASE 8.3 — Ampliación de Control Plane API para 6B / 7**
**ESTADO: ABIERTA (FUTURA, DEPENDE DE 8.2)**

#### Objetivo
Completar endpoints internos/administrativos que habiliten:
- **FASE 6B**
- y faciliten **FASE 7**

#### Candidatos naturales
- usuarios
- membresías
- permisos
- clientes
- suscripciones
- catálogo administrativo

#### Regla
- Priorizar API útil para UI administrativa real
- Evitar sobre-diseñar endpoints “por si acaso”

---

## **FASE 9 — Endurecimiento operativo**
**ESTADO: PARCIAL (9A CERRADA / 9B ABIERTA)**

---

### **FASE 9A — Hardening operativo mínimo MVP**
**ESTADO: CERRADA**

#### Cierre real
- Ajustes de Docker / compose validados
- Ajustes de `nginx.conf` validados
- Ajustes de `README.md` validados
- Ajustes de `authz_service/main.py` validados
- Ajustes de `dynamic_app_router` validados
- Launch / proxy / assets / session-check funcionales
- Hardening mínimo de credenciales / admin key / docs opcionales / bcrypt

#### Regla
- No reabrir FASE 9A

---

### **FASE 9B — Hardening productivo / madurez operativa**
**ESTADO: ABIERTA**

#### Pendiente real
- Migraciones versionadas reales
- Bootstrap maduro
- Seeds limpios / consistentes
- Limpieza de datos demo
- Concurrencia de stock
- Auditoría
- Backups / restore
- Versionado formal de cambios de schema

#### Regla
- Tratar como backlog productivo / fase futura
- No mezclar con cierres funcionales salvo necesidad estricta

---

## **FASE 10 — GPT constructor de apps hijas**
**ESTADO: CONGELADA**

### Regla
No abrir hasta que:
- FASE 4.2 ✔
- FASE 4.4 ✔
- FASE 4.5 ✔
- FASE 5 ✔
- **FASE 8 suficientemente estable**
- **FASE 9B razonablemente controlada**

---

# CONTEXTO ARQUITECTÓNICO OFICIAL (CONGELADO)

- **Portal** = front door / UI Shell
- **app-hija-1** = Control Plane / IAM de facto
- **Launch Service** = broker seguro entre catálogo y apps
- **POS** = app de negocio independiente
- **POS ya tiene `pos_db`**
- **Control Plane vive en `proyecto_db`**
- La transición correcta es:

  - **apps de negocio → Control Plane API**
  - **NO apps de negocio → DB directa del Control Plane**

---

# ESQUEMA REAL DEL CONTROL PLANE (REFERENCIA)

Tablas reales relevantes:

- `applications`
- `client_app_subscriptions`
- `clients`
- `permissions`
- `system_admins`
- `user_client_memberships`
- `users`
- `v_user_permissions`

---

# ORDEN OFICIAL DE CONTINUIDAD (ACTUALIZADO)

1. **FASE 8.2** — Inventario restante de acoplamiento POS → Control Plane
2. **FASE 8.3** — Ampliación de Control Plane API para 6B / 7
3. **FASE 6B** — UI administrativa de gestión
4. **FASE 7** — Administración delegada por empresa
5. **FASE 9B** — Hardening productivo / madurez operativa
6. **FASE 10** — Sigue congelada hasta estabilización suficiente

---

# REGLA OPERATIVA PARA LOS SIGUIENTES CHATS

Cuando se abra un nuevo chat para continuidad:

- Pegar este roadmap como **fuente de verdad**
- Indicar la **subfase exacta** a trabajar (ej. `FASE 8.2`)
- Pedir **solo el set mínimo de archivos**
- No saltar de subfase sin confirmar cierre real
- No confundir:
  - cierre de subfase
  - con cierre de fase completa

---

# RESUMEN EJECUTIVO FINAL (v2)

### Cerrado real
- 4.2
- 4.3
- 4.4
- 4.5
- 5
- 6A
- 8.1 (nuevo cierre funcional)
- 9A

### Abierto real
- 6B
- 7
- 8.2
- 8.3
- 9B

### Congelado
- 10

---

# Etiquetas cortas sugeridas (para seguimiento rápido)

```md
- [x] FASE 4.2 — Multi-tenant mínimo en POS
- [x] FASE 4.3 — Separación inicial de DB
- [x] FASE 4.4 — Prueba de app externa
- [x] FASE 4.5 — Decisión de Control Plane
- [x] FASE 5 — UI Shell unificado
- [x] FASE 6A — Backend / motor / enforcement de suscripciones
- [x] FASE 8.1 — Primer paquete mínimo POS → Control Plane API (desacople de seguridad / contexto)
- [x] FASE 9A — Hardening operativo mínimo MVP

- [ ] FASE 8.2 — Inventario restante de acoplamiento POS → Control Plane
- [ ] FASE 8.3 — Ampliación de Control Plane API para 6B / 7
- [ ] FASE 6B — UI administrativa de gestión
- [ ] FASE 7 — Administración delegada por empresa
- [ ] FASE 9B — Hardening productivo / madurez operativa

- [~] FASE 10 — CONGELADA
