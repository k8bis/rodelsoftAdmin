# RodelSoft - ROADMAP OFICIAL v3

> **Fuente de verdad oficial para continuidad del proyecto RodelSoft Platform**
>
> Este documento reemplaza operativamente las versiones previas cuando exista contradicción.
> Su objetivo es evitar pérdida de contexto, reapertura accidental de fases cerradas y mezcla incorrecta de alcance entre backend, portal y apps de negocio.

---

# 1) OBJETIVO DE ESTE DOCUMENTO

Este roadmap define el **estado real actual** del proyecto **RodelSoft Platform**, consolidando:

- fases ya cerradas
- fases abiertas / vigentes
- subfases ya ejecutadas
- criterios de trabajo obligatorios
- alcance inmediato real
- siguiente fase exacta a trabajar

## REGLA PRINCIPAL

**No reabrir fases cerradas salvo evidencia técnica nueva real** (archivos actuales, pruebas reales, logs o cambio explícito de alcance).

---

# 2) ARQUITECTURA OFICIAL VIGENTE (FUENTE DE VERDAD)

La arquitectura vigente de RodelSoft Platform es:

- **Portal** = front door / UI shell principal
- **app-hija-1** = Control Plane / IAM de facto
- **launch-service** = broker seguro entre catálogo y apps
- **dynamic-app-router** = enrutamiento de apps externas / dynamic proxy
- **apps de negocio** = apps independientes (ej. POS)
- **Control Plane DB** = `proyecto_db`
- **POS DB** = `pos_db`

## Regla arquitectónica oficial

La transición correcta es:

- **apps de negocio → Control Plane API**
- **NO apps de negocio → DB directa del Control Plane**

Es decir:

- Las apps de negocio (ej. POS) **no deben seguir creciendo** con acoplamiento directo a `proyecto_db`
- El patrón correcto es:
  - consumir endpoints internos del Control Plane (`app-hija-1`)
  - mantener su propia DB de negocio separada

---

# 3) ESQUEMA OFICIAL ACTUAL DEL CONTROL PLANE (REFERENCIA)

Tablas reales vigentes del Control Plane:

- `applications`
- `client_app_subscriptions`
- `clients`
- `permissions`
- `system_admins`
- `user_client_memberships`
- `users`
- `v_user_permissions`

## Semántica oficial actual

### `system_admins`
Usuarios con privilegio global transversal sobre toda la plataforma.

### `user_client_memberships`
Control de pertenencia del usuario por empresa (cliente).

Roles vigentes:

- `client_admin`
- `member`

### `permissions`
Permisos por aplicación dentro de un cliente.

Roles vigentes:

- `app_client_admin`
- `member`

### `client_app_subscriptions`
Relación contractual / funcional cliente ↔ aplicación.

Estados vigentes:

- `trial`
- `active`
- `suspended`
- `expired`

---

# 4) REPOSITORIOS / MÓDULOS RELEVANTES (REFERENCIA OPERATIVA)

Estructura vigente relevante:

- `apps/app-hija-1/`
- `apps/app-hija-2/`
- `apps/rodelsoft-pos/`
- `portal/`
- `launch-service/`
- `dynamic-app-router/`
- `database/`
- `shared/`
- `ext_apps/rodelsoft/notes-external`

---

# 5) FASES CERRADAS (NO REABRIR)

---

## FASE 4.2 — Multi-tenant mínimo en POS
**ESTADO: CERRADA**

### Resultado consolidado
- POS opera con contexto `app_id` / `client_id`
- El flujo de acceso multi-tenant mínimo quedó funcional
- Se mantuvo compatibilidad con launch y navegación actual

### Regla
No reabrir salvo que aparezca una ruptura real del contexto tenant.

---

## FASE 4.3 — Separación inicial de DB
**ESTADO: CERRADA (con deuda ya absorbida por FASE 8)**

### Resultado consolidado
- POS cuenta con `pos_db`
- Se separó la base de negocio del POS respecto al Control Plane
- Persisten acoplamientos residuales históricos que ahora se atienden en FASE 8

### Regla
No tratar esto como fase abierta.
La deuda remanente se resuelve exclusivamente dentro de **FASE 8**.

---

## FASE 4.4 — App externa real validada vía dynamic proxy
**ESTADO: CERRADA**

### Resultado consolidado
Se validó una app externa real:

- **RodelSoft Notes External**

Con comportamiento funcional confirmado:

- `launch-service` entrega redirect correcto
- `dynamic-app-router` resuelve la app externa
- `launch_mode = dynamic_proxy`
- health-check funcional
- `session-check` funcional
- assets estáticos cargando correctamente
- convivencia correcta con shell central

### Regla
No reducir esta fase a “solo prueba”.
Quedó validado el patrón real de app externa.

---

## FASE 4.5 — Decisión de Control Plane
**ESTADO: CERRADA**

### Resultado consolidado
Se consolidó la decisión oficial de arquitectura:

- **`app-hija-1` = Control Plane / IAM de facto**

Responsabilidades reales ya absorbidas:

- autenticación base
- sesión
- catálogo base de apps del usuario
- validación de acceso
- contexto de acceso
- endpoints internos de soporte

### Regla
No reabrir debate de “qué app será el control plane”.
Eso ya está decidido.

---

## FASE 5 — UI Shell unificado
**ESTADO: CERRADA**

### Resultado consolidado
Se consolidó el shell principal:

- Portal como entrada principal
- navegación centralizada
- integración con launch-service
- sesión central
- logout funcional y consistente
- shell compartido para continuidad UX

### Regla
No reabrir FASE 5 por ajustes menores de UX, CSS o deuda puntual.
Eso se atiende dentro de la fase activa correspondiente si aplica.

---

## FASE 6A — Backend / motor / enforcement base de memberships y suscripciones
**ESTADO: CERRADA**

### Resultado consolidado
Quedó implementado el modelo mínimo operativo para administración multi-tenant contractual:

- `client_app_subscriptions`
- `user_client_memberships`
- uso real de `permissions`
- backfill compatible desde permisos
- enforcement base reutilizable

### Resultado funcional real
- Un usuario pertenece a uno o más clientes
- Un cliente puede o no tener suscripción activa a una app
- Un usuario puede tener permisos por app dentro de un cliente
- Esto alimenta launch, visibilidad y validaciones

### Regla
No reabrir la fase como “modelo pendiente”.
La evolución futura ocurre sobre esta base.

---

## FASE 9A — Hardening operativo mínimo MVP
**ESTADO: CERRADA**

### Resultado consolidado
Se endureció el MVP a nivel mínimo operativo:

- restauración de sesión confiable
- validación inicial sin mostrar login prematuro
- logout real con limpieza de cookie
- compatibilidad con sesión central
- robustez mayor en launch / redirección
- endurecimiento de autenticación heredada
- migración automática a bcrypt en login legado exitoso

### Regla
No reabrir 9A por mejoras productivas futuras.
Eso pertenece a **FASE 9B**.

---

# 6) FASES ABIERTAS / VIGENTES

---

## FASE 8 — Control Plane API (transición DB directa → API)
**ESTADO: EN CURSO AVANZADA**

## Objetivo oficial
Eliminar gradualmente las consultas directas desde apps de negocio hacia `proyecto_db`, migrando a consumo por API interna del Control Plane (`app-hija-1`), sin romper el comportamiento actual.

## Alcance oficial de FASE 8
En esta fase **sí** se hace:

1. Mapear consultas directas históricas hacia `proyecto_db`
2. Definir endpoints internos mínimos en `app-hija-1`
3. Migrar por paquetes pequeños y seguros
4. Mantener compatibilidad con:
   - launch actual
   - multi-tenant actual
   - suscripciones actuales
   - shell actual
   - POS funcional actual

## Estado real consolidado de FASE 8

### FASE 8.1 — Inventario de acoplamiento POS → Control Plane DB
**ESTADO: CERRADA / ABSORBIDA**

### FASE 8.2 — Primer paquete mínimo de internal API
**ESTADO: CERRADA / ABSORBIDA**

### FASE 8.3 — Internal access/context API estabilizada
**ESTADO: FUNCIONALMENTE COMPLETADA**

#### Endpoints internos consolidados
- `/internal/access-check`
- `/internal/context-info`

#### Uso real confirmado
Consumidos en flujo real por apps / launch / validaciones de acceso.

---

### FASE 8.4 — Admin API interna v1 (primer paquete)
**ESTADO: FUNCIONALMENTE COMPLETADA**

#### Endpoints internos administrativos disponibles
- `/internal/admin/clients`
- `/internal/admin/users-by-client`
- `/internal/admin/subscriptions-by-client`
- `/internal/admin/permissions-by-client`

#### Objetivo
Exponer por API la información mínima necesaria para el módulo administrativo del Portal sin reintroducir acoplamiento directo desde UI hacia DB.

---

### FASE 8.5 — Scoping correcto por rol (`system_admin` / `app_client_admin`)
**ESTADO: FUNCIONALMENTE COMPLETADA**

#### Reglas consolidadas
- `system_admin` = alcance global
- `app_client_admin` = alcance limitado a cliente/app donde tiene administración
- `member` = sin alcance administrativo

#### Regla de modelado oficial
Para permisos administrativos por app/cliente, el rol de referencia correcto es:

- **`permissions.role = 'app_client_admin'`**

No debe depender de `users.role` como fuente principal de administración delegada.

---

### FASE 8.6 — Catálogos globales para `system_admin`
**ESTADO: SIGUIENTE SUBFASE ACTIVA / LISTA PARA IMPLEMENTAR**

## Objetivo exacto
Agregar endpoints internos de catálogo global (solo lectura por ahora) para `system_admin`, de forma que el Portal pueda mostrar:

- catálogo global de usuarios
- catálogo global de clientes
- catálogo global de aplicaciones

## Nota de alcance
En esta subfase se prioriza:

- lectura / consulta
- visibilidad correcta
- no necesariamente CRUD completo todavía

---

## FASE 6B — UI administrativa del Portal
**ESTADO: EN CURSO**

## Objetivo oficial
Construir el módulo administrativo mínimo del Portal, consumiendo la Control Plane API y respetando el alcance real de roles.

## Regla crítica
**FASE 6B depende funcionalmente de FASE 8, pero avanza en tándem por paquetes.**

Es decir:

- backend/API y UI pueden avanzar juntos por subfases acopladas
- no debe asumirse que 6B “está detenida” si ya existe el paquete backend mínimo correspondiente

---

### FASE 6B.1 — Modal admin base + tabs + selector de cliente
**ESTADO: FUNCIONALMENTE COMPLETADA**

#### Resultado consolidado
- botón **Administración** en menú de usuario
- modal administrativo
- tabs base
- selector de cliente
- carga de datasets por cliente
- consumo real de endpoints internos

---

### FASE 6B.2 — Alcance por `app_client_admin` y visibilidad operativa
**ESTADO: FUNCIONALMENTE COMPLETADA**

#### Resultado consolidado
- `app_client_admin` ve únicamente lo que debe ver
- `system_admin` conserva alcance mayor
- separación funcional de datasets por tab
- comportamiento estable validado en pruebas

---

### FASE 6B.3 — Catálogos globales para `system_admin`
**ESTADO: SIGUIENTE SUBFASE ACTIVA / LISTA PARA IMPLEMENTAR**

## Objetivo exacto
Agregar al modal administrativo la capacidad de mostrar para `system_admin`:

- usuarios globales
- clientes globales
- aplicaciones globales

## Regla de alcance
- Solo `system_admin`
- En principio **solo lectura**
- No mezclar todavía con CRUD completo si no es estrictamente necesario

---

### FASE 6B.4 — Acciones mínimas controladas (si aplica)
**ESTADO: PENDIENTE**

## Posible alcance futuro
- acciones mínimas sobre usuarios/permisos dentro del alcance permitido
- no abrir todavía CRUD masivo sin definir FASE 7

---

## FASE 7 — Administración delegada por empresa
**ESTADO: PENDIENTE / NO INICIAR TODAVÍA**

## Objetivo futuro
Permitir que admins delegados gestionen parcialmente información dentro de su alcance.

## Alcance esperado futuro
- altas/bajas de usuarios dentro de cliente
- asignación de permisos por app dentro del cliente
- operación restringida por `app_client_admin`
- respeto de memberships y suscripciones

## Regla
No mezclar esta fase con FASE 8.6 / 6B.3 si solo se está construyendo visibilidad de catálogos.

---

## FASE 9B — Hardening productivo / madurez operativa
**ESTADO: PENDIENTE**

## Alcance futuro
- auditoría / trazabilidad
- observabilidad
- rate limiting
- seguridad de producción
- secretos / rotación
- endurecimiento de cookies y headers
- manejo más robusto de errores / retries / fallbacks
- hardening de endpoints internos y políticas de acceso

---

## FASE 10 — Expansión avanzada / constructor / features congeladas
**ESTADO: CONGELADA**

## Regla
No proponer ni abrir trabajo aquí salvo instrucción explícita.

---

# 7) REGLA OFICIAL NUEVA: SUBFASES ACOPLADAS `8.x / 6B.x`

Para evitar perder el hilo, desde esta versión del roadmap se declara oficialmente:

## Las subfases de FASE 8 y FASE 6B pueden avanzar en tándem

Cuando un paquete backend habilita un paquete UI, el trabajo se rastrea como:

- `FASE 8.x / 6B.x`

## Ejemplos válidos
- `FASE 8.3 / 6B.1`
- `FASE 8.4 / 6B.2`
- `FASE 8.6 / 6B.3`

## Regla operativa
- **8.x** = API / backend / enforcement / exposición de datos
- **6B.x** = UI / modal / tabs / visibilidad / experiencia de administración

## Prohibición
No volver a tratar 6B como “no iniciada” cuando ya existe el paquete backend correspondiente.

---

# 8) ESTADO REAL CONSOLIDADO DEL MÓDULO ADMIN ACTUAL

Actualmente ya existe un módulo administrativo mínimo funcional en el Portal.

## Capacidades ya consolidadas
- menú de usuario con entrada a **Administración**
- modal administrativo
- detección de scope administrativo
- consumo de endpoints internos
- datasets por cliente
- separación por tabs

## Roles funcionales reales
- `system_admin`
- `app_client_admin`
- `member`

## Fuente de verdad de administración delegada
Para administración por cliente/app, la fuente principal es:

- **`permissions.role`**

y específicamente:

- **`app_client_admin`**

No usar `users.role` como modelo central de autorización administrativa delegada.

---

# 9) FUERA DE ALCANCE ACTUAL (NO HACER TODAVÍA)

No hacer todavía, salvo instrucción explícita:

- CRUD administrativo completo global
- administración delegada completa por empresa (FASE 7)
- refactor visual masivo del portal
- reabrir FASE 5 por temas menores de CSS
- reabrir FASE 6A como si el modelo no existiera
- reabrir FASE 9A por mejoras productivas futuras
- rediseñar el esquema completo sin necesidad estricta
- constructor GPT / generador de apps (FASE 10)

---

# 10) FORMA DE TRABAJO OBLIGATORIA PARA EL SIGUIENTE CHAT

Cuando se retome el proyecto en un nuevo chat:

## PASO 1 — Pedir solo archivos exactos
Antes de proponer cambios:

- pedir **exactamente** los archivos necesarios
- no pedir archivos innecesarios
- priorizar el set mínimo útil

## PASO 2 — Analizar archivos reales
Con los archivos adjuntos:

- analizar el código real actual
- contrastar contra este roadmap
- detectar alcance real
- evitar cambios inventados o genéricos

## PASO 3 — Entregar cambios concretos
La respuesta debe incluir:

- diagnóstico ejecutivo corto
- archivos exactos a modificar
- parche exacto o código final completo cuando aplique
- orden de despliegue
- checklist de pruebas

## PASO 4 — No perder el hilo
Si hay duda entre fases:

1. priorizar este roadmap
2. luego priorizar archivos actuales
3. luego priorizar pruebas reales
4. no reabrir fases cerradas por intuición

---

# 11) SIGUIENTE FASE EXACTA A TRABAJAR

# **FASE 8.6 / 6B.3 — Catálogos globales para `system_admin`**

## Objetivo técnico exacto

### Backend (`app-hija-1`)
Agregar endpoints internos de solo lectura para `system_admin`:

- catálogo global de usuarios
- catálogo global de clientes
- catálogo global de aplicaciones

### Frontend (`portal`)
Extender el modal de Administración para que `system_admin` pueda ver:

- usuarios globales
- clientes globales
- aplicaciones globales

## Restricción de alcance
- priorizar **lectura**
- no abrir CRUD completo todavía
- no mezclar con FASE 7 salvo necesidad explícita

---

# 12) PROMPT RECOMENDADO DE ARRANQUE PARA EL SIGUIENTE CHAT

Puedes iniciar el siguiente chat con algo como:

> Vamos a continuar RodelSoft Platform usando como fuente de verdad **RodelSoft - ROADMAP OFICIAL v3**.
> No reabras fases cerradas.
> La fase activa exacta es **FASE 8.6 / 6B.3**.
> Primero dime **exactamente qué archivos debo adjuntar** para implementar:
> - endpoints internos de catálogo global para `system_admin` en `app-hija-1`
> - consumo UI en Portal para mostrar:
>   - usuarios globales
>   - clientes globales
>   - aplicaciones globales
> Solo pide el set mínimo de archivos.

---

# 13) RESUMEN EJECUTIVO FINAL

## Estado oficial actual

### Cerrado
- FASE 4.2
- FASE 4.3
- FASE 4.4
- FASE 4.5
- FASE 5
- FASE 6A
- FASE 9A

### En curso
- **FASE 8** (avanzada)
- **FASE 6B** (en ejecución real)

### Siguiente paso
- **FASE 8.6 / 6B.3**

### Regla más importante
- **FASE 8 y FASE 6B avanzan en tándem por paquetes acoplados (`8.x / 6B.x`)**

---

# FIN DEL DOCUMENTO
