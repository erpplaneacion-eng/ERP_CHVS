# Estructura de Archivos CSS - ERP CHVS

Esta documentación describe la nueva estructura organizada de archivos CSS del sistema ERP CHVS.

## 📁 Estructura de Directorios

```
static/css/
├── erp_style.css          # Estilos base del sistema
├── components/            # Componentes reutilizables
│   └── modals.css        # Estilos para modales y ventanas emergentes
└── modules/               # Estilos específicos por módulo
    ├── principal.css      # Módulo de configuración (departamentos/municipios)
    ├── nutricion.css      # Módulo de nutrición y alimentos
    ├── planeacion.css     # Módulo de planeación (comedores/programas)
    └── facturacion.css    # Módulo de facturación
```

## 🎯 Descripción de Archivos

### **Archivos Base**

#### `erp_style.css`
- **Propósito**: Estilos base del sistema
- **Contenido**: Layout principal, sidebar, header, botones base, tipografía
- **Carga**: En todas las páginas

### **Componentes (`components/`)**

#### `modals.css`
- **Propósito**: Estilos para modales y componentes reutilizables
- **Contenido**:
  - Overlays de modales
  - Headers, body y footer de modales
  - Formularios dentro de modales
  - Animaciones de entrada/salida
  - Botones de acción
- **Carga**: En todas las páginas

### **Módulos (`modules/`)**

#### `principal.css`
- **Propósito**: Módulo de configuración del sistema
- **Contenido**:
  - Página principal con cards de configuración
  - Tablas de departamentos y municipios
  - Estilos específicos para gestión de datos base
- **Carga**: Solo en páginas del namespace `principal`

#### `nutricion.css`
- **Propósito**: Módulo de nutrición y alimentos
- **Contenido**:
  - Formularios complejos para alimentos ICBF
  - Validaciones visuales de campos numéricos
  - Tablas de información nutricional
  - Stats cards específicas para nutrición
  - Badges para categorías de alimentos
- **Carga**: Solo en páginas del namespace `nutricion`

#### `planeacion.css`
- **Propósito**: Módulo de planeación
- **Contenido**:
  - Formularios de comedores y sedes
  - Dashboard de programas con cards
  - Filtros de búsqueda avanzados
  - Estilos para mapas y ubicaciones
- **Carga**: Solo en páginas del namespace `planeacion`

#### `facturacion.css`
- **Propósito**: Módulo de facturación
- **Contenido**:
  - Tablas de facturas con estados
  - Formularios financieros
  - Resúmenes y estadísticas financieras
  - Gráficos y charts
  - Formateado de moneda y valores
- **Carga**: Solo en páginas del namespace `facturacion`

## ⚡ Carga Dinámica

Los archivos CSS se cargan dinámicamente según el módulo activo usando Django templates:

```django
<!-- CSS Base (siempre cargado) -->
<link rel="stylesheet" href="{% static 'css/erp_style.css' %}">
<link rel="stylesheet" href="{% static 'css/components/modals.css' %}">

<!-- CSS específico por módulo -->
{% if request.resolver_match.app_name == 'principal' %}
    <link rel="stylesheet" href="{% static 'css/modules/principal.css' %}">
{% elif request.resolver_match.app_name == 'nutricion' %}
    <link rel="stylesheet" href="{% static 'css/modules/nutricion.css' %}">
{% endif %}
```

## 🎨 Convenciones de CSS

### **Nomenclatura de Clases**
- **BEM Methodology**: `bloque__elemento--modificador`
- **Prefijos por módulo**: `.nutricion-`, `.planeacion-`, `.facturacion-`
- **Componentes**: `.modal-`, `.btn-`, `.form-`

### **Estructura de Archivos**
```css
/* ===================================== */
/* SECCIÓN PRINCIPAL                     */
/* ===================================== */

/* Subsección */
.clase-base {
    /* Propiedades ordenadas alfabéticamente */
}

.clase-base:hover {
    /* Estados hover */
}

/* Responsive Design */
@media (max-width: 768px) {
    /* Estilos móviles */
}
```

### **Colores por Módulo**
- **Principal**: `#3498db` (Azul)
- **Nutrición**: `#27ae60` (Verde)
- **Planeación**: `#0a8f17` (Verde oscuro)
- **Facturación**: `#3498db` (Azul)

## 📱 Responsive Design

Todos los módulos incluyen breakpoints estándar:
- **Desktop**: `> 1200px`
- **Tablet**: `768px - 1199px`
- **Mobile**: `< 768px`
- **Small Mobile**: `< 480px`

## 🔧 Mantenimiento

### **Agregar Nuevo Módulo**
1. Crear archivo `static/css/modules/nuevo_modulo.css`
2. Actualizar `base.html` para carga condicional
3. Seguir convenciones de nomenclatura establecidas

### **Optimización**
- Los archivos se cargan solo cuando son necesarios
- Estilos comunes están en `erp_style.css` y `modals.css`
- Evitar duplicación de código CSS entre módulos

## ✅ Beneficios de la Nueva Estructura

1. **🚀 Rendimiento**: Carga solo el CSS necesario por página
2. **🧹 Mantenibilidad**: Separación clara de responsabilidades
3. **📱 Responsive**: Diseño adaptativo en todos los módulos
4. **🔄 Escalabilidad**: Fácil agregar nuevos módulos
5. **🎯 Especificidad**: Estilos específicos por funcionalidad
6. **📋 Consistencia**: Convenciones uniformes en todo el proyecto