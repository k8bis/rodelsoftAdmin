# RodelSoft - ROADMAP OFICIAL v4.md

> **Documento de verdad oficial del proyecto**  
> **Estado:** VIGENTE  
> **Versión:** v4  
> **Fecha base:** 2026-04-09  
> **Objetivo:** consolidar el alcance real, las decisiones congeladas, la arquitectura vigente y el plan oficial de implementación para **RodelSoft Platform**, **Rodel-POS v2** y la nueva app externa **Rodel-Stocks v1**, evitando retrabajo, ambigüedad y pérdida de continuidad entre chats.

---

1. Propósito del documento

Este archivo sustituye la ambigüedad de seguimiento entre chats y se convierte en la fuente de verdad oficial para:

el estado real de la plataforma,
las decisiones arquitectónicas vigentes,
el alcance congelado de Rodel-POS v2,
el alcance congelado de Rodel-Stocks v1,
el modelo de integración POS ↔ Stocks,
el alcance mínimo obligatorio de UI/UX,
el plan de fases real para desarrollo.

Regla operativa:
A partir de este documento, no se debe asumir comportamiento, no se debe “recordar” de memoria sin contrastar, y no se debe obviar código, SQL o estructuras cuando un cambio afecte una fuente real.

2. Principios de trabajo (reglas anti-retrabajo)

2.1 No suponer

Ningún cambio funcional, de SQL, de rutas, de contratos API o de UI se debe proponer como definitivo sin:

revisar fuentes reales, o
dejar explícito que se trata de una hipótesis pendiente.

2.2 No mezclar fases cerradas con fases abiertas

Si una fase ya fue cerrada y validada, no se reabre salvo que:

exista una decisión nueva que la afecte, o
exista una evidencia real de inconsistencia.

2.3 Cambios completos, no parciales

Cuando se soliciten cambios de archivos:

deben entregarse archivos completos,
no diffs,
no fragmentos,
no “solo el cambio”.

2.4 El código real manda

Si existe diferencia entre:

lo que se recuerda del chat, y
lo que dicen las fuentes actuales,

las fuentes actuales mandan.

2.5 Diseño antes de ejecución

Antes de desarrollar:

se congela alcance,
se congela modelo,
se congela estrategia,
se congela orden de fases.

3. Estado real de la plataforma (congelado)

La plataforma RodelSoft ya cuenta con una arquitectura funcional orientada a catálogo dinámico de aplicaciones, control de acceso y publicación de apps externas.

3.1 Componentes confirmados del stack
Core / Control Plane
mysql (contenedor único, multi-base)
app-hija-1 (Control Plane API / backend principal)
launch-service
dynamic-app-router
authz-service
portal
nginx
Apps
app-hija-2 (existente, no relevante como patrón objetivo para esta fase)
rodelsoft-pos (app actual de POS)
rodelsoft-notes-external (patrón válido de app externa)
nueva app objetivo: rodel-stocks
3.2 Publicación dinámica de apps (ya vigente)

La plataforma ya soporta:

catálogo de apps en tabla applications
lanzamiento vía launch-service
validación de:
JWT / sesión
membresía activa
permiso por app
suscripción activa
launch_mode = dynamic_proxy
resolución dinámica por slug
publicación bajo /ext/{slug} vía dynamic-app-router

Decisión congelada:
Este es el patrón oficial de apps externas para RodelSoft.

4. Bases de datos oficiales del proyecto
4.1 Modelo de ownership por dominio
proyecto_db

Base del Control Plane:

usuarios
clientes
membresías
permisos
catálogo de apps
suscripciones
pos_db

Base del motor POS:

catálogo POS
ventas
configuración POS
(en v2) impresión, estados, snapshots, integración con Stocks
stocks_db

Base de Rodel-Stocks:

catálogo maestro de inventario
existencias
movimientos
órdenes de compra
integración con POS

Decisión congelada:
Aunque todo viva en el mismo contenedor MySQL para pruebas, cada dominio tendrá su propia base lógica.
No se mezclará Stocks dentro de pos_db.

5. Decisiones arquitectónicas oficiales (congeladas)
5.1 Rodel-Stocks nace como app externa dinámica

Sí.

Registro esperado:
slug = rodel-stocks
launch_mode = dynamic_proxy
public_url = /ext/rodel-stocks/
internal_url = http://rodel-stocks:8020
entry_path = /
5.2 Rodel-POS no se migra a externa en la primera fase

No de inmediato.

Decisión oficial:
POS permanece en su despliegue actual en la fase inicial.
Pero debe quedar “external-ready” desde POS v2.
5.3 POS será migrable a app externa en fase futura

Sí, como objetivo futuro.

Condición:

La migración de POS a app externa se hará en una fase posterior, cuando POS v2 + Stocks v1 estén estables.

5.4 Integración POS ↔ Stocks será API-first

Sí.

Regla:

Aunque ambas apps vivan inicialmente en el mismo MySQL container:

POS y Stocks deben hablarse por API, no por consultas directas cruzadas entre dominios.
6. Objetivo funcional general del nuevo ciclo

Este ciclo de trabajo tiene dos frentes principales:

6.1 Rodel-Stocks v1

Nueva app externa para gestión de inventarios generales.

6.2 Rodel-POS v2

Refactor funcional y estructural de POS para:

multi-tenant real,
integración con inventario,
notas/tickets imprimibles,
cancelación de ventas,
trazabilidad histórica.
7. Rodel-Stocks v1 — alcance oficial
7.1 Objetivo

Rodel-Stocks será la app responsable del dominio de inventarios.

7.2 Responsabilidades congeladas

Rodel-Stocks será responsable de:

catálogo maestro de artículos/servicios,
categorías de inventario,
entradas manuales,
salidas manuales,
ajustes de inventario,
entradas por orden de compra (v1 ligera),
salidas por ventas provenientes de POS,
saldos actuales,
historial / kardex,
integración API con POS,
operación standalone sin POS.
7.3 Tipos de ítem
item_type
physical
service
Regla:
physical → inventariable
service → vendible/catalogable, pero no inventariable
8. Rodel-Stocks v1 — alcance funcional mínimo obligatorio (UI + operación)

Rodel-Stocks no será solo API.
Debe incluir UI operativa mínima desde v1.

8.1 Dashboard operativo

Debe mostrar como mínimo:

existencias bajas,
últimos movimientos,
entradas recientes,
salidas recientes,
alertas de stock mínimo.
8.2 Catálogo de artículos / servicios

Debe incluir:

listado,
alta,
edición,
activación/desactivación,
búsqueda y filtros por:
nombre
SKU
barcode
marca
modelo
color
categoría
tipo (physical / service)
8.3 Movimientos manuales

Debe soportar:

entrada manual
salida manual
ajuste positivo
ajuste negativo
8.4 Órdenes de compra (v1 ligera)

Debe soportar:

crear orden de compra
agregar items
recibir parcial
recibir total
convertir recepción a movimientos de inventario
8.5 Existencias

Debe soportar:

saldo actual
stock mínimo
alertas visuales
filtros
8.6 Kardex / historial

Debe soportar:

historial por artículo
filtros por fecha
filtros por tipo de movimiento
filtros por referencia (manual / compra / POS)
8.7 Integración visible con POS

Debe poder visualizar:

qué movimientos vienen de POS,
qué movimientos son reversas por cancelación,
referencia de venta externa.
9. Rodel-Stocks v1 — modelo de datos objetivo (congelado)
9.1 stock_categories

Campos mínimos:

id
client_id
name
description
is_active
created_at
updated_at
Regla:
unique lógico recomendado: (client_id, name)
9.2 stock_items

Campos mínimos:

id
client_id
category_id
name
description
item_type
brand
model
color
sku
barcode
track_inventory
is_sellable
is_purchasable
unit_of_measure
min_stock
is_active
created_at
updated_at
Reglas:
item_type obligatorio
track_inventory = 1 para físicos
track_inventory = 0 para servicios
sku y barcode no globales
unique lógico recomendado:
(client_id, sku)
(client_id, barcode)
9.3 stock_balances

Campos mínimos:

id
client_id
stock_item_id
on_hand_qty
reserved_qty
updated_at
Regla:
1 fila por item por cliente
unique recomendado: (client_id, stock_item_id)
9.4 stock_movements

Campos mínimos:

id
client_id
stock_item_id
movement_type
quantity
reference_type
reference_id
source_app
source_app_id
created_by
notes
created_at
movement_type
purchase_entry
manual_entry
sale_exit
manual_exit
adjustment_plus
adjustment_minus
sale_cancel_reversal
reference_type
purchase_order
pos_sale
manual
9.5 stock_purchase_orders

Campos mínimos:

id
client_id
supplier_name
status
notes
created_by
created_at
updated_at
status
draft
received_partial
received_full
cancelled
9.6 stock_purchase_order_items

Campos mínimos:

id
purchase_order_id
stock_item_id
ordered_qty
received_qty
unit_cost
created_at
9.7 stock_external_sale_sync

Tabla obligatoria para idempotencia y ciclo de vida de ventas externas.

Campos mínimos:

id
client_id
source_app
source_app_id
external_sale_id
sync_status
processed_at
cancelled_at
cancelled_by
cancellation_reason
response_snapshot
created_at
sync_status
applied
cancelled
Regla:
unique recomendado:
(client_id, source_app, external_sale_id)
10. Rodel-POS v2 — objetivo oficial

Rodel-POS deja de ser solo una prueba de venta simple y se convierte en:

Módulo formal de ventas con trazabilidad documental e integración de inventario

Debe soportar:

catálogo multi-tenant real,
venta con lógica dual de inventario,
nota/ticket imprimible,
cancelación total de ventas,
reversa de inventario,
snapshots históricos,
preparación para futura migración a app externa.
11. Rodel-POS v2 — decisiones de dominio (congeladas)
11.1 Multi-tenant real
pos_categories y pos_products deben incluir client_id

Decisión congelada:
POS se alinea al modelo tenant-first de la plataforma.

11.2 sku y barcode dejan de ser globales

No deben ser únicos globales.

Regla objetivo:
UNIQUE(client_id, sku) lógico
UNIQUE(client_id, barcode) lógico
11.3 POS mantiene compatibilidad standalone

POS debe seguir funcionando aunque el cliente:

no tenga Stocks,
o no quiera usar inventario externo.
12. Rodel-POS v2 — modelo funcional de productos
12.1 pos_categories

Debe incluir como mínimo:

id
client_id
name
is_active
12.2 pos_products

Debe incluir / evolucionar hacia:

id
client_id
category_id
name
description
sku
barcode
price
product_type
track_inventory
inventory_mode
stock_item_id
stock_quantity (legacy)
is_sellable
is_active
product_type
physical
service
inventory_mode
pos_legacy
stocks_api
none
Reglas:
pos_legacy → usa stock_quantity
stocks_api → delega inventario a Stocks
none → no controla inventario
13. Rodel-POS v2 — ventas (ciclo de vida oficial)
13.1 Toda venta debe tener:
folio visible
estado
detalle histórico
posibilidad de impresión
posibilidad de cancelación total
trazabilidad de inventario
13.2 Estados de venta (pos_sales.status)

Para v2 inicial:

completed
cancelled

No entran en esta fase:

devoluciones,
cancelaciones parciales,
refunds,
notas de crédito,
flujo draft avanzado.
14. Rodel-POS v2 — modelo de ventas objetivo (congelado)
14.1 pos_sales

Debe evolucionar para incluir al menos:

id
client_id
sale_number
status
subtotal_snapshot
discount_snapshot
total_snapshot
customer_name_snapshot (opcional MVP)
cashier_name_snapshot
notes
cancelled_at
cancelled_by
cancellation_reason
inventory_reverted_at
created_at
updated_at
Reglas:
sale_number obligatorio
status obligatorio
sale_number visible para impresión
no se elimina físicamente una venta cancelada
14.2 pos_sale_items

Debe guardar snapshots históricos.

Campos mínimos objetivo:

id
sale_id
product_id
product_name_snapshot
sku_snapshot
product_type_snapshot
inventory_mode_snapshot
stock_item_id_snapshot
quantity
unit_price_snapshot
line_total_snapshot
created_at

Regla congelada:
El histórico de ventas no debe depender del catálogo actual.
Todo lo necesario para renderizar e interpretar la venta debe vivir en snapshots.

14.3 pos_inventory_movements (recomendado)

Tabla recomendada para trazabilidad local cuando inventory_mode = pos_legacy.

Campos sugeridos:

id
client_id
product_id
movement_type
quantity
reference_type
reference_id
created_by
notes
created_at
movement_type
sale_exit
sale_cancel_reversal
manual_entry
manual_exit
adjustment_plus
adjustment_minus

Nota:
Esta tabla es muy recomendable aunque el sistema legacy pudiera funcionar sin ella.

15. Rodel-POS v2 — reglas de venta e inventario (congeladas)
15.1 Venta en pos_legacy

Si el producto tiene inventory_mode = pos_legacy:

valida contra stock_quantity
descuenta localmente
idealmente registra pos_inventory_movements
15.2 Venta en stocks_api

Si el producto tiene inventory_mode = stocks_api:

POS no confía en stock local
POS crea venta
POS invoca Stocks por API
si Stocks falla → la venta debe fallar / revertirse
15.3 Venta en none

Si el producto tiene inventory_mode = none:

no valida inventario
se vende sin movimiento de stock
15.4 Transaccionalidad v1
Modo oficial:

síncrono estricto

Regla:

Si la venta requiere Stocks:

si Stocks no puede aplicar movimientos,
la venta no debe quedar consolidada.
16. Cancelación de ventas — reglas oficiales (congeladas)
16.1 La cancelación es obligatoria en POS v2

Sí entra en esta fase.

16.2 La cancelación es total, no parcial
Solo se permite:
cancelación total de la venta

No entra en esta fase:

cancelación parcial
devolución parcial
devolución total formal
notas de crédito
16.3 La cancelación nunca elimina registros
Regla de oro:
no borrar venta,
no borrar items,
no editar destructivamente.

La venta:

conserva histórico,
cambia a status = cancelled.
16.4 La cancelación revierte inventario por movimiento compensatorio
Nunca:
editar el movimiento original,
“deshacer” cambiando cantidades previas.
Siempre:
crear movimiento inverso auditable.
16.5 Idempotencia

Si una venta ya está cancelada:

no puede volver a cancelarse,
debe responder como ya cancelada / bloqueada.
16.6 Orden correcto de cancelación
Regla:
validar que la venta esté completed
intentar reversa de inventario
si reversa OK → cambiar venta a cancelled
si reversa falla → la venta permanece completed
17. Motor de documentos imprimibles POS (tickets / notas)
17.1 Decisión oficial

La impresión no será un HTML fijo único.

Se implementará un:

Motor de documentos imprimibles basado en machotes HTML físicos
17.2 Diseño oficial v1

El motor funcionará con:

carpeta de plantillas HTML,
nombre de plantilla configurable por cliente,
render server-side,
datos de venta por contexto estándar,
soporte para tickets y notas como plantillas distintas.
17.3 No entra en v1
editor visual
builder drag & drop
HTML libre editable desde UI
CSS libre editable desde UI
18. Motor de plantillas — implementación oficial (congelada)
18.1 Ubicación de plantillas

Se manejará una carpeta tipo:

templates/print/

Ejemplos:

ticket_58mm_basic.html
ticket_80mm_basic.html
nota_venta_a4.html
ticket_cliente_especial.html
18.2 Configuración por cliente

Cada cliente podrá configurar:

el nombre del archivo plantilla a utilizar.
Campo sugerido:
ticket_template_name
18.3 Plantillas especiales

Si un cliente requiere un ticket personalizado:

se diseña un nuevo HTML,
se coloca en la carpeta oficial,
se asigna por nombre en configuración.
18.4 Motor de render recomendado
Jinja2

Aunque conceptualmente se piensa como “marcadores”, la implementación oficial recomendada será:

plantillas HTML físicas
con render mediante Jinja2

Equivalencia conceptual aceptada:
La idea de “machotes con marcadores” se conserva,
pero el motor real recomendado es Jinja2 en vez de reemplazos manuales tipo <<empresa>>.

18.5 Seguridad

El nombre del archivo configurado:

debe validarse,
debe existir dentro de la carpeta permitida,
no debe aceptar rutas arbitrarias (../, paths absolutos, etc).
19. Contexto estándar de datos para plantillas de impresión

Todas las plantillas deberán usar el mismo contrato base de variables.

19.1 Datos de empresa / cliente
company_name
company_slogan
company_address
company_phone
footer_text
19.2 Datos de venta
sale_number
sale_datetime
sale_status
is_cancelled
19.3 Datos de usuario
cashier_name
19.4 Totales
subtotal
discount
total
19.5 Items
items

Cada item debe poder exponer:

product_name
sku
quantity
unit_price
line_total
19.6 Flags de visualización
show_cashier
show_sku
show_phone
show_address
show_cancelled_watermark

Regla congelada:
Todos los machotes deben respetar este contrato base para evitar caos de mantenimiento.

20. Tickets / notas — reglas de negocio congeladas
20.1 La venta es la fuente de verdad

La nota/ticket no es un módulo separado en v1.

Regla:
La venta (pos_sales + pos_sale_items) es la fuente de verdad.
El ticket/nota es una representación documental de esa venta.
20.2 Ventas canceladas siguen siendo imprimibles
Regla:
Se pueden reimprimir.
Deben mostrar claramente el estado CANCELADA.
20.3 Los documentos deben usar snapshots
Regla:

Los documentos imprimibles deben renderizarse con:

snapshots históricos de la venta,
no con datos vivos del catálogo actual.
21. Integración POS ↔ Stocks (contrato oficial v1)
21.1 Principio general

La integración será:

síncrona
API-first
idempotente
estricta
22. POS → Stocks: aplicar venta
22.1 Endpoint oficial
POST /api/integrations/pos/sales-apply
22.2 Request objetivo
{
  "client_id": 4,
  "source_app": "rodelsoft-pos",
  "source_app_id": 3,
  "external_sale_id": 123,
  "created_by": "usuario",
  "notes": "Venta generada desde POS",
  "items": [
    {
      "pos_product_id": 15,
      "stock_item_id": 88,
      "product_name": "Producto X",
      "quantity": 2
    }
  ]
}
22.3 Regla
Si ya fue aplicada, debe responder idempotente.
Si no puede aplicarse por stock insuficiente, debe fallar.
Si falla, POS no debe consolidar la venta final.

23. POS → Stocks: cancelar venta (reversa de inventario)
23.1 Endpoint oficial
POST /api/integrations/pos/sales-cancel
23.2 Request objetivo
{
  "client_id": 4,
  "source_app": "rodelsoft-pos",
  "source_app_id": 3,
  "external_sale_id": 123,
  "cancelled_by": "usuario",
  "cancellation_reason": "Venta cancelada por error"
}
23.3 Regla
Si la venta externa no existe en Stocks, debe fallar de forma controlada.
Si ya fue cancelada previamente, debe responder idempotente.
La reversa debe crear movimientos sale_cancel_reversal.
No debe borrar ni editar destructivamente los movimientos originales.
24. Stocks → POS (consulta / sincronía mínima)
24.1 Objetivo

Aunque la integración principal es POS → Stocks para aplicar y revertir inventario, el diseño debe permitir consultas en sentido inverso.

24.2 Casos previstos

Stocks podrá consultar a POS (por API, no directo a tablas) para:

obtener datos de una venta por sale_id,
obtener datos por sale_number,
validar estado de una venta,
obtener detalle histórico para conciliación.
24.3 Endpoints sugeridos

No son obligatorios en la primera entrega técnica, pero quedan congelados como objetivo de diseño:

GET /api/internal/sales/{sale_id}
GET /api/internal/sales/by-number/{sale_number}
24.4 Regla
Las consultas deben ser solo de lectura.
Deben responder con snapshots.
No deben depender del catálogo actual.
25. POS v2 — configuración por cliente (obligatoria)
25.1 Objetivo

POS v2 debe tener una configuración por cliente para controlar comportamiento operativo sin tocar código.

25.2 Tabla sugerida: pos_client_settings

Campos mínimos recomendados:

id
client_id
default_ticket_template_name
company_display_name
company_slogan
company_address
company_phone
ticket_footer_text
show_cashier
show_sku
show_phone
show_address
show_cancelled_watermark
inventory_integration_enabled
default_inventory_mode
is_active
created_at
updated_at
25.3 Reglas
default_ticket_template_name define el machote por default.
inventory_integration_enabled permite apagar Stocks aunque el cliente tenga la app.
default_inventory_mode puede sugerir comportamiento para nuevos productos, pero el producto manda.
Debe existir una fila por cliente (o generarse al primer uso).
26. Portal / catálogo de apps — impacto obligatorio
26.1 Nueva app a registrar

Debe agregarse la nueva app:

name: Rodel-Stocks
slug: rodel-stocks
launch_mode: dynamic_proxy
entry_path: /
internal_url: http://rodel-stocks:8020
public_url: /ext/rodel-stocks/
is_active: 1
26.2 Suscripción / membresía

La nueva app debe integrarse al flujo existente de:

catálogo applications
permisos
membresías
suscripciones (client_app_subscriptions o estructura vigente)
26.3 Regla

No se deben romper apps existentes al agregar rodel-stocks.

27. Docker / despliegue — impacto obligatorio
27.1 Nuevo servicio

Debe agregarse contenedor:

rodel-stocks
27.2 Configuración esperada

Ejemplo conceptual de variables:

STOCKS_MYSQL_HOST
STOCKS_MYSQL_PORT
STOCKS_MYSQL_USER
STOCKS_MYSQL_PASSWORD
STOCKS_MYSQL_DATABASE=stocks_db
CONTROL_PLANE_BASE_URL
SECRET_KEY
ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
DB_MAX_RETRIES
DB_RETRY_DELAY
27.3 Regla

Aunque el MySQL sea el mismo contenedor:

Stocks debe usar stocks_db
POS debe usar pos_db
Control Plane debe usar proyecto_db
28. Estrategia de implementación oficial (orden congelado)
28.1 Fase INV-1 — congelación de verdad

Objetivo:

cerrar alcance,
congelar arquitectura,
congelar decisiones,
emitir este roadmap v4.

Estado: CERRADA con este documento.

28.2 Fase INV-2A — SQL real

Objetivo:

definir SQL reales de:
stocks_db
migraciones POS v2
seed de app rodel-stocks
ajustes de catálogo / permissions / subscriptions si aplican
Entregables esperados
60-stocks-schema.sql
55-migrate_pos_v2_inventory.sql (o nombre equivalente según orden real)
65-stocks-seed.sql (si se decide separar seed)
ajuste a 00-init.sql si requiere crear stocks_db
ajuste a 20-seed.sql o migración dedicada para applications

Regla:
Esta fase debe hacerse sobre SQL reales existentes, no asumidos.

28.3 Fase INV-2B — backend base de Rodel-Stocks

Objetivo:

scaffold real de app externa siguiendo patrón notes external / ext_apps
auth / sesión / client context
conexión a stocks_db
routers base
healthcheck
integración mínima con launch / router dinámico
Entregables esperados
main.py
auth.py
db.py
schemas.py
stock_routes.py (o estructura modular equivalente)
Dockerfile
docker-compose update
28.4 Fase INV-3 — CRUD operativo de Stocks v1

Objetivo:

categorías
catálogo de items
balances
movimientos manuales
kardex básico
Entregables
endpoints
HTML base
JS base
estilos base
pruebas mínimas
28.5 Fase INV-4 — órdenes de compra v1 ligera

Objetivo:

alta de OC
items de OC
recepción parcial / total
generación de movimientos de entrada
28.6 Fase POS-2A — refactor estructural de POS

Objetivo:

multi-tenant real
client_id en catálogos
product_type
inventory_mode
stock_item_id
preparación de snapshots
Entregables
migración SQL
ajustes backend
ajustes UI
28.7 Fase POS-2B — venta formal + snapshots

Objetivo:

venta con sale_number
pos_sales
pos_sale_items
snapshots completos
estados completed / cancelled
trazabilidad base
28.8 Fase POS-2C — integración POS ↔ Stocks

Objetivo:

aplicar venta a Stocks
bloquear venta si Stocks falla
idempotencia
manejo de errores
pruebas cruzadas
28.9 Fase POS-2D — cancelación de ventas

Objetivo:

cancelar venta completa
reversa de inventario
idempotencia
reimpresión como cancelada
28.10 Fase POS-2E — motor de tickets / notas

Objetivo:

carpeta de machotes HTML
configuración por cliente
render con Jinja2
impresión por venta
reimpresión de canceladas
28.11 Fase POS-2F — hardening y preparación de externalización

Objetivo:

dejar POS listo para migración futura a app externa
separar dependencias implícitas
limpiar rutas / acoplamientos
documentar contratos
29. Decisiones explícitas de “NO entra” en esta fase

Para evitar scope creep, no entra en esta versión:

29.1 En Stocks v1
multi-almacén
lotes / caducidades
series obligatorias
costos promedio / PEPS formal
proveedores avanzados
transferencias entre almacenes
reservas complejas
picking / packing
devoluciones de compra formales
inventario cíclico avanzado
29.2 En POS v2
cancelación parcial
devolución parcial
devolución total formal
notas de crédito
clientes frecuentes / CRM
caja / cortes complejos
pagos mixtos avanzados
fiscalización / CFDI
editor visual de tickets
HTML libre editable por cliente
sincronización asíncrona eventual con colas
30. Riesgos conocidos y mitigaciones
30.1 Riesgo: sobreacoplar POS y Stocks
Mitigación:
contratos API explícitos
no queries cruzadas directas entre bases
inventory_mode por producto
inventory_integration_enabled por cliente
30.2 Riesgo: romper compatibilidad standalone de POS
Mitigación:
mantener pos_legacy
mantener stock_quantity en transición
fallback controlado
30.3 Riesgo: tickets personalizados se vuelvan inmantenibles
Mitigación:
carpeta de machotes controlados
Jinja2
contrato estándar de variables
sin editor visual en v1
30.4 Riesgo: ventas inconsistentes si Stocks falla
Mitigación:
integración síncrona estricta
no consolidar venta si no aplica inventario
idempotencia de endpoints
30.5 Riesgo: reabrir temas cerrados por pérdida de contexto
Mitigación:
este roadmap v4 es el documento de verdad
cada fase debe contrastarse con fuentes reales
no asumir cierres previos sin evidencia
31. Reglas operativas finales (obligatorias)
31.1 Toda implementación futura deberá respetar:
este roadmap v4,
las fuentes reales vigentes,
el orden de fases,
el principio de no asumir.
31.2 Toda modificación de archivos debe entregarse:
completa,
no parcial,
no por diff,
no con “solo cambia esto”.
31.3 Toda modificación SQL debe:
respetar orden real de ejecución,
evitar romper ambientes existentes,
considerar migración compatible cuando aplique.
31.4 Toda integración entre apps debe:
documentar request / response,
documentar errores,
documentar idempotencia.
31.5 Toda decisión nueva que afecte alcance debe:
agregarse a este roadmap,
antes de ejecutar desarrollo mayor.
32. Estado oficial al cierre de este documento
32.1 Estado del roadmap

VIGENTE y CONGELADO

32.2 Documento de verdad oficial

A partir de este punto:

RodelSoft - ROADMAP OFICIAL v4.md

es el archivo de verdad oficial para este ciclo.

32.3 Siguiente fase oficial

La siguiente fase correcta y autorizada es:

FASE INV-2A — SQL real
Objetivo inmediato:

Generar, sobre fuentes reales:

60-stocks-schema.sql
migración POS v2 inicial
seed / alta de rodel-stocks
orden exacto de ejecución
impacto real en docker-compose y despliegue
33. Criterio rector del proyecto (cláusula final)

El proyecto RodelSoft debe evolucionar con estas prioridades, en este orden:

claridad del dominio
compatibilidad operativa
trazabilidad
configurabilidad real
desacoplamiento progresivo
no romper lo que ya funciona
no asumir donde hay código real

Cláusula final oficial:
Si existe duda entre una solución “rápida” y una solución “alineada al dominio real”,
se debe preferir la solución alineada al dominio, aunque implique una fase más.

FIN DEL DOCUMENTO
RodelSoft - ROADMAP OFICIAL v4.md
Documento de verdad oficial del ciclo actual

