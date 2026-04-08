# RodelSoft — ROADMAP OFICIAL v1 (estado real actualizado)

> Documento maestro de continuidad para evitar reabrir fases cerradas, reducir retrabajo y mantener el alcance real del proyecto.

---

## FASE 4.2 — Multi-tenant mínimo en POS

**ESTADO: CERRADA**

### Cierre real

* `pos_sales` ya guarda:

  * `client_id`
  * `app_id`
  * `created_by`
* Ya se refleja en:

  * export
  * esquema
  * código

### Regla

* No reabrir FASE 4.2
* Si más adelante se endurece integridad (FK / migración formal), eso vive en **FASE 9B**

---

## FASE 4.3 — Separación inicial de DB (Control Plane vs POS)

**ESTADO: CERRADA + DEUDA RESIDUAL**

### Cierre real

* Existe `pos_db`
* Existe `proyecto_db`
* POS usa `POS_MYSQL_DATABASE`
* POS separa `CONTROL_MYSQL_DATABASE`
* `00-init.sql` y `30-pos-schema.sql` contemplan `pos_db`

### Deuda residual (NO reabre 4.3)

* Migraciones más maduras
* Bootstrap más limpio
* API entre servicios

### La deuda vive en

* **FASE 8** (API)
* **FASE 9B** (hardening / migraciones / bootstrap)

---

## FASE 4.4 — Prueba de app externa

**ESTADO: CERRADA**

### Cierre real

* App externa real existe
* Ya se probó
* Ya maduró seguridad / integración
* Ya funciona con launch + proxy + shell + session-check

### Regla

* No reabrir FASE 4.4

---

## FASE 4.5 — Decisión de Control Plane

**ESTADO: CERRADA + DEUDA RESIDUAL**

### Cierre real

* `app-hija-1` opera como Control Plane / IAM de facto
* Ownership conceptual resuelto
* El runtime actual ya trabaja bajo esta decisión

### Deuda residual (NO reabre 4.5)

* API formal interna
* Naming / limpieza
* Endurecimiento adicional

### La deuda vive en

* **FASE 8**
* **FASE 9B**

---

## FASE 5 — UI Shell unificado

**ESTADO: CERRADA**

### Cierre real

* Shell unificado validado
* Base real:

  * `shared/shared-shell.css`
  * `shared/README-ui-shell.md`
* Incluye cierre efectivo de:

  * FASE 5.1
  * FASE 5.2
  * FASE 5.3
* Validado en:

  * Portal
  * Rodel-POS
  * RodelSoft Notes External

### Regla

* No reabrir FASE 5
* Si aparece algo, tratarlo como:

  * deuda visual puntual
  * cleanup puntual
  * no como reapertura de fase

---

## FASE 6 — Contratación / suscripción

**ESTADO: PARCIAL (6A CERRADA / 6B ABIERTA)**

---

### FASE 6A — Backend / motor / enforcement

**ESTADO: CERRADA**

#### Cierre real

* Motor de suscripción existe
* `client_app_subscriptions` existe
* Launch y catálogo respetan suscripciones
* `migrate_fase6_subscriptions.sql` existe
* `app-hija-1` devuelve datos de suscripción

#### Regla

* No reabrir FASE 6A

---

### FASE 6B — UI administrativa de gestión

**ESTADO: ABIERTA**

#### Pendiente real

* UI para alta / baja de usuarios
* UI para gestión de permisos
* UI para gestión de suscripciones
* CRUDs administrativos asociados

#### Lineamiento de diseño

* Reutilizar el menú ya existente
* Priorizar **modals** en lo posible
* Evitar abrir páginas nuevas innecesarias
* Mantener consistencia con el **UI Shell** ya cerrado en FASE 5

#### Dependencia real

* **Depende funcionalmente de FASE 8 (Control Plane API)**

---

## FASE 7 — Administración delegada por empresa

**ESTADO: ABIERTA**

### Base existente

* `permissions`
* `user_client_memberships`
* `client_app_subscriptions`

### Pendiente real

* UI delegada por empresa
* Enforcement administrativo por tenant
* Alta / baja de usuarios por empresa
* Limitar administración a apps contratadas
* Flujo operativo real para admin empresarial

### Regla

* No abrir antes de estabilizar:

  * **FASE 8**
  * y preferentemente **FASE 6B**

---

## FASE 8 — Control Plane API (transición DB directa → API)

**ESTADO: ABIERTA (SIGUIENTE FASE RECOMENDADA)**

### Punto técnico real

* POS todavía consulta `proyecto_db` directamente para datos del Control Plane

### Alcance

* Exponer API interna del Control Plane (`app-hija-1`)
* Identificar consultas directas actuales desde POS hacia `proyecto_db`
* Migrar POS para consumir API interna en vez de DB directa
* Mantener compatibilidad con:

  * launch actual
  * multi-tenant actual
  * suscripciones actuales
  * shell actual
  * POS funcional actual
* No romper:

  * integración externa
  * `dynamic_app_router`
  * `launch_service`

### Nota

* Esta fase desbloquea técnicamente:

  * **FASE 6B**
  * y facilita **FASE 7**

---

## FASE 9 — Endurecimiento operativo

**ESTADO: PARCIAL (9A CERRADA / 9B ABIERTA)**

---

### FASE 9A — Hardening operativo mínimo MVP

**ESTADO: CERRADA**

#### Cierre real

* Ajustes de Docker / compose validados
* Ajustes de `nginx.conf` validados
* Ajustes de `README.md` validados
* Ajustes de `authz_service/main.py` validados
* Ajustes de `dynamic_app_router` validados
* Launch / proxy / assets / session-check funcionales
* Hardening mínimo de credenciales / admin key / docs opcionales / bcrypt

#### Regla

* No reabrir FASE 9A

---

### FASE 9B — Hardening productivo / madurez operativa

**ESTADO: ABIERTA**

#### Pendiente real

* Migraciones versionadas reales
* Bootstrap maduro
* Seeds limpios / consistentes
* Limpieza de datos demo
* Concurrencia de stock
* Auditoría
* Backups / restore
* Versionado formal de cambios de schema

#### Regla

* Tratar como backlog productivo o fase futura
* No mezclar con fases funcionales salvo que sea estrictamente necesario

---

## FASE 10 — GPT constructor de apps hijas

**ESTADO: CONGELADA**

### Regla

No abrir hasta que:

* FASE 4.2 ✔
* FASE 4.4 ✔
* FASE 4.5 ✔
* FASE 5 ✔
* FASE 8 suficientemente estable
* FASE 9B razonablemente controlada

---

# Orden recomendado de continuidad (oficial)

1. **FASE 8**
2. **FASE 6B**
3. **FASE 7**
4. **FASE 9B**
5. **FASE 10**

---

# Reglas maestras de continuidad

* No reabrir fases cerradas sin evidencia nueva real
* No mezclar deuda residual con reapertura de fase
* No asumir alcance: confirmar antes de cambiar código
* Siempre pedir archivos reales antes de proponer cambios
* Mantener el roadmap dentro del prompt de continuidad de cada nuevo chat
