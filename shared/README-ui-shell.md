# RodelSoft UI Shell v1

## Objetivo
Asegurar que todas las apps del ecosistema RodelSoft se perciban como una sola plataforma, aunque estén desplegadas como servicios independientes.

## Alcance v1
- Header estándar
- Footer estándar
- Tokens visuales comunes
- Contrato visual para apps SSR y equivalencia visual para apps React

## Componentes obligatorios
1. Header estándar
2. Footer estándar
3. Contenedor principal (`.rs-app-shell`, `.rs-main`)
4. Botones base (`.rs-btn`, `.rs-btn-primary`, `.rs-btn-secondary`)
5. Cards base (`.rs-card`)
6. Chips de contexto (`.rs-chip`)

## Tokens visuales oficiales
- Primario: `#0A4D8C`
- Primario hover: `#083B6A`
- Acento: `#2563EB`
- Fondo: `#F5F7FB`
- Surface: `#FFFFFF`
- Texto: `#0F172A`
- Texto secundario: `#475569`
- Borde: `#DCE3EE`

## Reglas para apps SSR
Toda app SSR debe:
- cargar `shared-shell.css`
- usar header estándar
- usar footer estándar
- mostrar branding RodelSoft
- mostrar nombre de app
- mostrar cliente/usuario si aplica
- ofrecer “Volver a apps”
- ofrecer “Cerrar sesión” (si aplica)

## Reglas para apps React
No es obligatorio compartir HTML literal en v1, pero sí:
- respetar los mismos colores
- mantener jerarquía visual equivalente
- usar botones y cards visualmente consistentes
- conservar branding RodelSoft

## Regla operativa v1
El archivo fuente oficial vive en:
- `shared/shared-shell.css`

Cada app puede copiar una versión local para evitar acoplamientos de despliegue.

## Evolución futura
- v2: componentes compartidos reales
- v3: design system formal / librería reusable