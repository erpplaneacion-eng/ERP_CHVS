# Editor de Preparaciones - Documentación Frontend

## 📋 Descripción General

El **Editor de Preparaciones** es una interfaz avanzada que permite editar los pesos de ingredientes por nivel escolar para cada menú, con cálculo automático de valores nutricionales y sistema de semaforización.

## 🎯 Funcionalidades Principales

### 1. **Edición Multi-nivel**
- Tabs separados para cada nivel escolar (Preescolar, Primaria 1-3, Primaria 4-5, Secundaria, Media/Ciclo Complementario)
- Edición independiente de pesos por nivel
- Sincronización automática entre inputs numéricos y sliders visuales

### 2. **Validación en Tiempo Real**
- Validación de rangos permitidos (mínimo/máximo) por ingrediente
- Indicadores visuales:
  - ✅ **Verde**: Peso dentro del rango permitido
  - ❌ **Rojo**: Peso fuera del rango
- Tooltips informativos con información nutricional

### 3. **Cálculos Nutricionales Automáticos**
- Recalcula totales al modificar cualquier peso
- Sistema de semaforización por nutriente:
  - 🟢 **Óptimo** (0-35%): Verde
  - 🟡 **Aceptable** (35-70%): Amarillo
  - 🔴 **Alto** (>70%): Rojo

### 4. **Herramientas de Optimización**
- **Copiar pesos**: Copiar pesos de un nivel a otros niveles
- **Sincronizar**: Sincronizar pesos base desde preparaciones
- **Comparar**: Comparar valores actuales con Minuta Patrón
- **Sugerencias**: Análisis automático con recomendaciones de ajuste
- **Optimizar** ⚠️: En desarrollo - optimización automática mediante algoritmo

## 📁 Estructura de Archivos

```
erp_chvs/
├── templates/nutricion/
│   └── preparaciones_editor.html          # Template HTML (ahora optimizado, sin CSS inline)
├── static/
│   ├── css/nutricion/
│   │   ├── preparaciones_editor.css       # 🆕 Estilos separados (530 líneas)
│   │   └── README_PREPARACIONES_EDITOR.md # Este archivo
│   └── js/nutricion/
│       └── preparaciones_editor.js        # Lógica frontend (1113 líneas)
└── nutricion/
    ├── views_preparaciones_editor.py      # Vista Django
    └── urls.py                            # Configuración de rutas
```

## 🎨 Arquitectura CSS

### Organización del CSS

El archivo `preparaciones_editor.css` está organizado en secciones lógicas:

```css
1. Encabezado del editor (.prep-editor-header)
2. Tabs de niveles escolares (.nav-tabs)
3. Toolbar principal (.prep-editor-toolbar)
4. Toolbar de nivel (.nivel-toolbar)
5. Tabla de ingredientes (.tabla-ingredientes)
6. Inputs y controles (.input-peso, .peso-control-container)
7. Slider personalizado (.slider-peso)
8. Badges (.badge-estado, .badge-rango)
9. Panel de totales nutricionales (.panel-totales, .nutriente-card)
10. Panel de sugerencias (.panel-sugerencias)
11. Overlay de guardado (.guardando-overlay)
12. Animaciones (@keyframes)
```

### Mejoras de Rendimiento Aplicadas

✅ **Transiciones específicas** (NO `transition: all`):
```css
/* CORRECTO ✅ */
.input-peso {
    transition: border-color 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}

/* INCORRECTO ❌ - Evitado según CLAUDE.md */
.input-peso {
    transition: all 0.2s ease;  /* Causa animaciones no deseadas */
}
```

✅ **Hover states optimizados**:
```css
.tabla-ingredientes tbody tr {
    transition: background-color 0.2s ease, box-shadow 0.2s ease;
}
```

✅ **Variables CSS para temas**:
```css
.slider-peso {
    --thumb-color: #2563eb;
}
```

## 🔧 JavaScript Integration

### Datos Embebidos

El template HTML incluye datos JSON embebidos que son consumidos por `preparaciones_editor.js`:

```html
<!-- Niveles escolares con totales y requerimientos -->
<script id="niveles-data" type="application/json">{{ niveles_json|safe }}</script>

<!-- Catálogo de ingredientes ICBF -->
<script id="ingredientes-catalogo" type="application/json">{{ ingredientes_json|safe }}</script>

<!-- Preparaciones del menú -->
<script id="preparaciones-catalogo" type="application/json">{{ preparaciones_json|safe }}</script>
```

### Event Listeners

El JavaScript utiliza **event delegation** para mejor rendimiento:

```javascript
// Event listener global para inputs de peso
document.addEventListener('input', (e) => {
    if (e.target.classList.contains('input-peso')) {
        // Lógica de validación y recálculo
    }
});
```

## 📊 Sistema de Semaforización

### Rangos de Evaluación

| Estado | Rango | Color | Clase CSS |
|--------|-------|-------|-----------|
| **Óptimo** | 0-35% | 🟢 Verde | `.nutriente-card.optimo` |
| **Aceptable** | 35-70% | 🟡 Amarillo | `.nutriente-card.aceptable` |
| **Alto** | >70% | 🔴 Rojo | `.nutriente-card.alto` |

### Nutrientes Evaluados

1. **Calorías** (kcal)
2. **Proteína** (g)
3. **Grasa** (g)
4. **Carbohidratos** (g)
5. **Calcio** (mg)
6. **Hierro** (mg)
7. **Sodio** (mg)

## 🚀 Mejoras Implementadas (Febrero 2025)

### ✅ Separación de Archivos (Antes vs Después)

**Antes:**
```html
{% block extra_css %}
<style>
    /* 530 líneas de CSS inline */
    .prep-editor-header { ... }
    .nav-tabs { ... }
    /* ... */
</style>
{% endblock %}
```

**Después:**
```html
{% block extra_css %}
<link rel="stylesheet" href="{% static 'css/nutricion/preparaciones_editor.css' %}">
{% endblock %}
```

**Beneficios:**
- ✅ Mejor mantenibilidad
- ✅ Cache del navegador
- ✅ Reutilización potencial
- ✅ Debugging más fácil
- ✅ Separación de responsabilidades

### ✅ Comentarios Estructurales en HTML

```html
<!-- ========================================
     ENCABEZADO DEL EDITOR
     ======================================== -->

<!-- ========================================
     TOOLBAR PRINCIPAL
     ======================================== -->

<!-- ========================================
     TABS DE NIVELES ESCOLARES
     ======================================== -->
```

**Beneficios:**
- ✅ Navegación rápida en el código
- ✅ Mejor legibilidad
- ✅ Facilita el mantenimiento

## 🔮 Funcionalidades Futuras

### ⚠️ En Desarrollo

1. **Optimización Automática**
   - Algoritmo de programación lineal
   - Ajuste automático de pesos para cumplir metas nutricionales
   - Minimización de diferencias con requerimientos

2. **Exportación de Reportes**
   - Exportar análisis nutricional a PDF
   - Exportar comparativa con Minuta Patrón

3. **Historial de Cambios**
   - Registro de modificaciones
   - Comparación entre versiones
   - Rollback de cambios

## 📝 Convenciones del Proyecto

Según `CLAUDE.md`, este módulo sigue las siguientes convenciones:

### CSS
- ✅ Evitar `transition: all` - usar propiedades específicas
- ✅ Separar CSS del HTML
- ✅ Usar clases descriptivas con nombres en inglés
- ✅ Evitar inline styles (excepto casos específicos)

### HTML
- ✅ Usar event listeners en archivos JS separados
- ✅ Evitar inline `onclick` handlers
- ✅ Comentarios descriptivos por sección
- ✅ Estructura semántica con atributos `data-*`

### JavaScript
- ✅ Event delegation para mejor rendimiento
- ✅ Modularización con IIFE
- ✅ Validación en tiempo real
- ✅ Feedback visual inmediato

## 🐛 Troubleshooting

### El CSS no se aplica después de cambios

**Solución:** Hard refresh del navegador
- **Windows/Linux:** `Ctrl + Shift + R` o `Ctrl + F5`
- **Mac:** `Cmd + Shift + R`

### Los cálculos nutricionales no se actualizan

**Verificar:**
1. Consola del navegador (F12) para errores JavaScript
2. Que los datos JSON estén correctamente embebidos
3. Que los inputs tengan los atributos `data-*` correctos

### Los sliders no se sincronizan con los inputs

**Verificar:**
1. Que cada fila tenga tanto `.input-peso` como `.slider-peso`
2. Que los event listeners estén activos (ver consola)
3. Compatibilidad del navegador con range inputs

## 📚 Referencias

- **CLAUDE.md**: Convenciones del proyecto
- **Frontend Architecture**: Sección en CLAUDE.md sobre arquitectura frontend
- **Performance Guidelines**: Optimizaciones de CSS/DOM en CLAUDE.md

---

**Última actualización:** Febrero 2025
**Autor:** Refactorización frontend según CLAUDE.md
**Estado:** ✅ Producción
