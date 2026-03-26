# Colores Corporativos RodelSoft

Esta carpeta contiene los logos y los colores corporativos de RodelSoft que deben utilizarse en todos los sitios y aplicaciones.

## Paleta de Colores

### Colores Primarios
- **Azul Oscuro (Primary)**: `#003366` - Color principal corporativo
- **Azul Claro (Secondary)**: `#0066FF` - Color secundario para acentos y botones
- **Azul Accent**: `#00A8E8` - Color para elementos destacados

### Colores de Estado
- **Éxito (Success)**: `#00C853` - Para mensajes exitosos
- **Advertencia (Warning)**: `#FFC107` - Para advertencias
- **Error**: `#F44336` - Para errores
- **Información (Info)**: `#0066FF` - Para información general

### Colores Neutrales
- **Fondo Claro (Light)**: `#F5F7FA` - Color de fondo principal
- **Borde (Border)**: `#E0E6ED` - Color para bordes
- **Texto**: `#1A1A1A` - Color de texto principal
- **Texto Claro**: `#555555` - Color de texto secundario

## Uso en CSS

```css
:root {
  --primary: #003366;
  --secondary: #0066FF;
  --accent: #00A8E8;
  --success: #00C853;
  --warning: #FFC107;
  --error: #F44336;
  --light: #F5F7FA;
  --border: #E0E6ED;
  --text: #1A1A1A;
  --text-light: #555555;
}

/* Uso */
background-color: var(--primary);
color: var(--text);
border-color: var(--border);
```

## Logos Disponibles

Los logos se encuentran en esta carpeta con diferentes variaciones:
- `Logo de RodelSoft con escudo hexagonal.png` - Logo principal con escudo
- `Logo de RodelSoft en azul.png` - Logo en color azul
- `Logo minimalista de RodelSoft.png` - Versión minimalista
- `Logo moderno de RodelSoft.png` - Versión moderna
- `Escudo hexagonal con monograma RD.png` - Solo escudo

## Guías de Uso

### En Componentes React
```jsx
const COLORS = {
  primary: "#003366",
  secondary: "#0066FF",
  accent: "#00A8E8",
  success: "#00C853",
  warning: "#FFC107",
  error: "#F44336",
  light: "#F5F7FA",
  border: "#E0E6ED",
  text: "#1A1A1A",
  textLight: "#555555",
};

<div style={{ backgroundColor: COLORS.primary, color: "white" }}>
  Contenido
</div>
```

### En Tailwind CSS (si se implementa)
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        rodelsoft: {
          primary: '#003366',
          secondary: '#0066FF',
          accent: '#00A8E8',
        },
      },
    },
  },
};
```

## Tipografía Recomendada

- **Familia**: System fonts (`-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto'`)
- **Headings**: Bold (fontWeight: 700)
- **Body**: Regular (fontWeight: 400)
- **Labels**: Semi-bold (fontWeight: 600)

## Espaciado (Escala)

- **xs**: 4px
- **sm**: 8px
- **md**: 12px
- **lg**: 16px
- **xl**: 20px
- **2xl**: 24px
- **3xl**: 32px
- **4xl**: 40px

## Sombras (Recomendadas)

- **Pequeña**: `0 2px 8px rgba(0, 51, 102, 0.08)`
- **Mediana**: `0 8px 24px rgba(0, 51, 102, 0.12)`
- **Grande**: `0 12px 24px rgba(0, 51, 102, 0.15)`

---

**Última actualización**: 24 de marzo de 2026
