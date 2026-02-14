# 📋 Plan de Implementación: Validador Semanal de Menús

## 🎯 Objetivo
Implementar un sistema de validación visual que muestre si cada semana de menús cumple con las frecuencias de componentes definidas en `nutricion_requerimientos_semanales`.

---

## 📊 Estructura Actual vs Propuesta

### ❌ ANTES (Actual):
```
┌─────────────────────────────────────────┐
│ MODALIDAD: CAJM AM (mod1)              │
├─────────────────────────────────────────┤
│ [Menú1][Menú2][Menú3][Menú4][Menú5]    │
│ [Menú6][Menú7][Menú8][Menú9][Menú10]   │
│ [Menú11][Menú12][Menú13][Menú14][Menú15]│
│ [Menú16][Menú17][Menú18][Menú19][Menú20]│
│ [+ Especial][🤖 IA]                     │
└─────────────────────────────────────────┘
```

### ✅ DESPUÉS (Propuesta):
```
┌─────────────────────────────────────────────────────────────────┐
│ MODALIDAD: CAJM AM (mod1)                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📅 SEMANA 1                                                     │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ [Menú1][Menú2][Menú3][Menú4][Menú5]                        ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ ✅ VALIDADOR DE CUMPLIMIENTO - SEMANA 1:                       │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ✅ Bebida con leche (com1): 5/5 días                        ││
│ │ ✅ Alimento proteico (com2): 3/3 veces                      ││
│ │ ✅ Cereal acompañante (com3): 5/5 días                      ││
│ │ ❌ Fruta (com4): 1/2 veces - FALTA 1                        ││
│ │ ✅ Azúcares (com5): 5/5 días                                ││
│ │ ✅ Grasas (com6): 5/5 días                                  ││
│ │ ✅ Agua (com15): 5/5 días                                   ││
│ │                                                              ││
│ │ Estado: ❌ NO CUMPLE (1 componente faltante)                ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ 📅 SEMANA 2                                                     │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ [Menú6][Menú7][Menú8][Menú9][Menú10]                       ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ ✅ VALIDADOR DE CUMPLIMIENTO - SEMANA 2:                       │
│ (Similar...)                                                    │
│                                                                 │
│ 📅 SEMANA 3 & 4...                                              │
│                                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ 🌟 MENÚS ESPECIALES Y GENERACIÓN IA                            │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ [+ Crear Menú Especial][🤖 Generar con IA]                 ││
│ │ [Menú Navidad][Menú Día del Niño]...                       ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Archivos a Modificar

### 1. **JavaScript - ModalidadesManager.js**
Archivo: `erp_chvs/static/js/nutricion/modules/ModalidadesManager.js`

**Métodos a modificar:**
- ✏️ `generarTarjetasMenus()` - Agrupar menús en semanas
- ➕ **NUEVO**: `generarValidadorSemanal()` - Crear componente validador
- ➕ **NUEVO**: `validarSemana()` - Lógica de validación
- ➕ **NUEVO**: `contarComponentesPorSemana()` - Contar componentes

**Métodos a crear:**
```javascript
/**
 * Generar HTML del validador semanal
 * @param {Array} menusS semana - Menús de la semana (5 menús)
 * @param {string} modalidadId - ID de la modalidad
 * @param {number} numeroSemana - Número de semana (1-4)
 * @returns {string} HTML del validador
 */
async generarValidadorSemanal(menusSemana, modalidadId, numeroSemana)

/**
 * Validar cumplimiento de frecuencias de una semana
 * @param {Array} menusSemana - Menús de la semana
 * @param {string} modalidadId - ID de la modalidad
 * @returns {Object} Resultado de validación
 */
async validarSemana(menusSemana, modalidadId)

/**
 * Contar apariciones de componentes en los menús de una semana
 * @param {Array} menusSemana - Menús de la semana
 * @returns {Object} Conteo de componentes
 */
async contarComponentesPorSemana(menusSemana)
```

### 2. **Backend - Views de Nutrición**
Archivo: `erp_chvs/nutricion/views.py`

**Nuevo endpoint API:**
```python
@login_required
def api_validar_semana(request):
    """
    Valida si una semana cumple con las frecuencias requeridas

    GET params:
    - menu_ids: IDs de los 5 menús separados por coma
    - modalidad_id: ID de la modalidad

    Returns:
    {
        "cumple": true/false,
        "componentes": [
            {
                "id": "com1",
                "nombre": "Bebida con leche",
                "requerido": 5,
                "actual": 5,
                "cumple": true
            },
            ...
        ]
    }
    """
```

**Nuevo endpoint para obtener requerimientos:**
```python
@login_required
def api_requerimientos_modalidad(request):
    """
    Obtiene los requerimientos semanales de una modalidad

    GET params:
    - modalidad_id: ID de la modalidad

    Returns:
    {
        "modalidad_id": "mod1",
        "requerimientos": [
            {
                "componente_id": "com1",
                "componente_nombre": "Bebida con leche",
                "frecuencia": 5
            },
            ...
        ]
    }
    """
```

### 3. **CSS - Estilos del Validador**
Archivo: `erp_chvs/static/css/nutricion/lista_menus.css`

**Nuevas clases CSS:**
```css
/* Contenedor de semana */
.semana-container {
    margin-bottom: 40px;
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    padding: 20px;
    background: #fafafa;
}

/* Título de semana */
.semana-titulo {
    font-size: 1.3rem;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* Grid de menús de la semana */
.semana-menus-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

/* Validador semanal */
.validador-semanal {
    background: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.validador-titulo {
    font-size: 1.1rem;
    font-weight: bold;
    margin-bottom: 15px;
    color: #34495e;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Lista de componentes */
.validador-lista {
    list-style: none;
    padding: 0;
    margin: 0;
}

.validador-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    border-radius: 6px;
    margin-bottom: 8px;
    transition: background 0.2s;
}

.validador-item:hover {
    background: #f8f9fa;
}

/* Estados de cumplimiento */
.validador-item.cumple {
    background: #d4edda;
    border-left: 4px solid #28a745;
}

.validador-item.no-cumple {
    background: #f8d7da;
    border-left: 4px solid #dc3545;
}

/* Íconos de estado */
.estado-icono {
    font-size: 1.2rem;
    margin-right: 8px;
}

.estado-icono.cumple {
    color: #28a745;
}

.estado-icono.no-cumple {
    color: #dc3545;
}

/* Badge de frecuencia */
.frecuencia-badge {
    background: #007bff;
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: bold;
}

.frecuencia-badge.error {
    background: #dc3545;
}

/* Resumen final */
.validador-resumen {
    margin-top: 15px;
    padding: 15px;
    border-radius: 6px;
    font-weight: bold;
    text-align: center;
}

.validador-resumen.cumple {
    background: #d4edda;
    color: #155724;
}

.validador-resumen.no-cumple {
    background: #f8d7da;
    color: #721c24;
}

/* Sección de menús especiales */
.menus-especiales-section {
    margin-top: 50px;
    padding-top: 30px;
    border-top: 3px dashed #dee2e6;
}

.menus-especiales-titulo {
    font-size: 1.4rem;
    font-weight: bold;
    color: #6c757d;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}
```

---

## 🔧 Implementación Detallada

### PASO 1: Modificar `generarTarjetasMenus()`

**Ubicación:** `ModalidadesManager.js` línea 198

**Código propuesto:**
```javascript
/**
 * Generar tarjetas de menús agrupadas por semana
 */
generarTarjetasMenus(menus, animate = false) {
    const menusRegulares = menus.filter(m => !isNaN(m.menu) && parseInt(m.menu) >= 1 && parseInt(m.menu) <= 20);
    const menusEspeciales = menus.filter(m => isNaN(m.menu) || parseInt(m.menu) < 1 || parseInt(m.menu) > 20);

    let html = '';

    // Agrupar menús regulares en semanas (5 menús cada una)
    for (let semana = 1; semana <= 4; semana++) {
        const inicio = (semana - 1) * 5;
        const fin = inicio + 5;
        const menusSemana = menusRegulares.slice(inicio, fin);

        if (menusSemana.length > 0) {
            html += this.generarSeccionSemana(menusSemana, semana, animate);
        }
    }

    // Sección de menús especiales + IA al final
    html += this.generarSeccionEspeciales(menusEspeciales, menus[0]?.id_modalidad__id_modalidades, animate);

    return html;
}

/**
 * Generar sección de una semana con validador
 */
generarSeccionSemana(menusSemana, numeroSemana, animate) {
    const modalidadId = menusSemana[0]?.id_modalidad__id_modalidades;

    let html = `
        <div class="semana-container" data-semana="${numeroSemana}">
            <div class="semana-titulo">
                <i class="fas fa-calendar-week"></i>
                SEMANA ${numeroSemana}
            </div>

            <div class="semana-menus-grid">
    `;

    // Tarjetas de menús
    menusSemana.forEach((menu, index) => {
        const menuEscaped = String(menu.menu).replace(/'/g, "\\'");
        const downloadUrl = `/nutricion/exportar-excel/${menu.id_menu}/`;
        const animStyle = animate ? `style="animation-delay: ${index * 0.05}s"` : '';
        const animClass = animate ? 'menu-card-anim' : '';

        html += `
            <div class="menu-card ${animClass} ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                 ${animStyle}
                 onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                    <i class="fas fa-file-excel"></i>
                </a>
                <div class="menu-numero">${menu.menu}</div>
                <div class="menu-actions">
                    <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menu.menu}')">
                        <i class="fas fa-utensils"></i> Preparaciones
                    </button>
                </div>
            </div>
        `;
    });

    html += `
            </div>

            <!-- Validador Semanal -->
            <div class="validador-semanal" id="validador-semana-${numeroSemana}-${modalidadId}">
                <div class="validador-titulo">
                    <i class="fas fa-clipboard-check"></i>
                    Validación de Cumplimiento - Semana ${numeroSemana}
                </div>
                <div class="loading-validador">
                    <i class="fas fa-spinner fa-spin"></i> Cargando validación...
                </div>
            </div>
        </div>
    `;

    // Cargar validación asíncrona
    setTimeout(() => {
        this.cargarValidadorSemana(menusSemana, modalidadId, numeroSemana);
    }, 100);

    return html;
}

/**
 * Generar sección de menús especiales e IA
 */
generarSeccionEspeciales(menusEspeciales, modalidadId, animate) {
    let html = `
        <div class="menus-especiales-section">
            <div class="menus-especiales-titulo">
                <i class="fas fa-star"></i>
                Menús Especiales y Generación IA
            </div>
            <div class="menus-grid">
    `;

    // Menús especiales existentes
    menusEspeciales.forEach((menu, index) => {
        const menuEscaped = String(menu.menu).replace(/'/g, "\\'");
        const downloadUrl = `/nutricion/exportar-excel/${menu.id_menu}/`;
        const animStyle = animate ? `style="animation-delay: ${index * 0.05}s"` : '';
        const animClass = animate ? 'menu-card-anim' : '';

        html += `
            <div class="menu-card menu-card-especial ${animClass} ${menu.tiene_preparaciones ? 'has-preparaciones' : ''}"
                 ${animStyle}
                 onclick="abrirGestionPreparaciones(${menu.id_menu}, '${menuEscaped}')">
                <a href="${downloadUrl}" class="btn-download-excel" onclick="event.stopPropagation();" title="Descargar Excel">
                    <i class="fas fa-file-excel"></i>
                </a>
                <div class="menu-numero-especial">
                    ${menu.menu}
                </div>
                <div class="menu-actions" style="flex-direction: column;">
                    <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); abrirGestionPreparaciones(${menu.id_menu}, '${menuEscaped}')">
                        <i class="fas fa-utensils"></i> Preparaciones
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="event.stopPropagation(); abrirEditarMenuEspecial(${menu.id_menu}, '${menuEscaped}')">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </div>
        `;
    });

    // Botones de crear especial y generar IA
    html += `
                <div class="menu-card menu-card-especial ${animate ? 'menu-card-anim' : ''}"
                     onclick="abrirModalMenuEspecial('${modalidadId}')">
                    <div class="menu-numero-especial">
                        <i class="fas fa-plus-circle"></i>
                    </div>
                    <div class="menu-label-especial">Crear Especial</div>
                </div>
                <div class="menu-card menu-card-ia ${animate ? 'menu-card-anim' : ''}"
                     onclick="abrirModalMenuIA('${modalidadId}')">
                    <div class="menu-numero-ia">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="menu-label-ia">Generar con IA</div>
                </div>
            </div>
        </div>
    `;

    return html;
}

/**
 * Cargar validador semanal
 */
async cargarValidadorSemana(menusSemana, modalidadId, numeroSemana) {
    const containerId = `validador-semana-${numeroSemana}-${modalidadId}`;
    const container = document.getElementById(containerId);

    if (!container) return;

    try {
        // Obtener IDs de menús
        const menuIds = menusSemana.map(m => m.id_menu).join(',');

        // Llamar al API de validación
        const response = await fetch(
            `/nutricion/api/validar-semana/?menu_ids=${menuIds}&modalidad_id=${modalidadId}`
        );
        const data = await response.json();

        // Generar HTML del validador
        let html = `
            <div class="validador-titulo">
                <i class="fas fa-clipboard-check"></i>
                Validación de Cumplimiento - Semana ${numeroSemana}
            </div>
            <ul class="validador-lista">
        `;

        data.componentes.forEach(comp => {
            const cumple = comp.cumple;
            const icono = cumple ? '<i class="fas fa-check-circle estado-icono cumple"></i>' : '<i class="fas fa-times-circle estado-icono no-cumple"></i>';
            const claseItem = cumple ? 'cumple' : 'no-cumple';
            const badge = cumple
                ? `<span class="frecuencia-badge">${comp.actual}/${comp.requerido}</span>`
                : `<span class="frecuencia-badge error">${comp.actual}/${comp.requerido} - FALTA ${comp.requerido - comp.actual}</span>`;

            html += `
                <li class="validador-item ${claseItem}">
                    <div>
                        ${icono}
                        <strong>${comp.nombre}</strong>
                    </div>
                    ${badge}
                </li>
            `;
        });

        html += `
            </ul>
            <div class="validador-resumen ${data.cumple ? 'cumple' : 'no-cumple'}">
                ${data.cumple
                    ? '<i class="fas fa-check-circle"></i> ✅ SEMANA CUMPLE CON LA MINUTA PATRÓN'
                    : `<i class="fas fa-exclamation-triangle"></i> ❌ NO CUMPLE (${data.componentes.filter(c => !c.cumple).length} componente(s) faltante(s))`
                }
            </div>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error('Error al cargar validador:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                Error al cargar la validación. Por favor, recargue la página.
            </div>
        `;
    }
}
```

### PASO 2: Implementar Backend API

**Archivo:** `erp_chvs/nutricion/views.py`

```python
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from .models import (
    TablaMenus,
    TablaPreparaciones,
    TablaRequerimientosSemanales,
    ComponentesAlimentos
)

@login_required
def api_validar_semana(request):
    """
    Valida si una semana cumple con las frecuencias requeridas
    """
    try:
        menu_ids = request.GET.get('menu_ids', '').split(',')
        modalidad_id = request.GET.get('modalidad_id')

        if not menu_ids or not modalidad_id:
            return JsonResponse({'error': 'Faltan parámetros'}, status=400)

        # Obtener requerimientos de la modalidad
        requerimientos = TablaRequerimientosSemanales.objects.filter(
            modalidad_id=modalidad_id
        ).select_related('componente_id')

        # Contar componentes en los menús de la semana
        conteo_componentes = {}

        for menu_id in menu_ids:
            preparaciones = TablaPreparaciones.objects.filter(
                id_menu_id=menu_id
            ).select_related('id_componente')

            for prep in preparaciones:
                comp_id = prep.id_componente.id_componente
                conteo_componentes[comp_id] = conteo_componentes.get(comp_id, 0) + 1

        # Validar contra requerimientos
        componentes_resultado = []
        cumple_total = True

        for req in requerimientos:
            comp_id = req.componente_id.id_componente
            comp_nombre = req.componente_id.componente
            requerido = req.frecuencia
            actual = conteo_componentes.get(comp_id, 0)
            cumple = actual == requerido

            if not cumple:
                cumple_total = False

            componentes_resultado.append({
                'id': comp_id,
                'nombre': comp_nombre,
                'requerido': requerido,
                'actual': actual,
                'cumple': cumple
            })

        return JsonResponse({
            'cumple': cumple_total,
            'componentes': componentes_resultado
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_requerimientos_modalidad(request):
    """
    Obtiene los requerimientos semanales de una modalidad
    """
    try:
        modalidad_id = request.GET.get('modalidad_id')

        if not modalidad_id:
            return JsonResponse({'error': 'Falta modalidad_id'}, status=400)

        requerimientos = TablaRequerimientosSemanales.objects.filter(
            modalidad_id=modalidad_id
        ).select_related('componente_id')

        resultado = []
        for req in requerimientos:
            resultado.append({
                'componente_id': req.componente_id.id_componente,
                'componente_nombre': req.componente_id.componente,
                'frecuencia': req.frecuencia
            })

        return JsonResponse({
            'modalidad_id': modalidad_id,
            'requerimientos': resultado
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
```

**Agregar rutas en `erp_chvs/nutricion/urls.py`:**
```python
urlpatterns = [
    # ... rutas existentes ...
    path('api/validar-semana/', views.api_validar_semana, name='api_validar_semana'),
    path('api/requerimientos-modalidad/', views.api_requerimientos_modalidad, name='api_requerimientos_modalidad'),
]
```

---

## ✅ Checklist de Implementación

- [x] 1. Agregar nuevos estilos CSS al archivo `lista_menus.css`
- [x] 2. Modificar `ModalidadesManager.js`:
  - [x] Actualizar `generarTarjetasMenus()`
  - [x] Agregar `generarSeccionSemana()`
  - [x] Agregar `generarSeccionEspeciales()`
  - [x] Agregar `cargarValidadoresSemana()` (método para cargar validadores asíncronamente)
- [x] 3. Crear endpoints en backend:
  - [x] `api_validar_semana()` en `views.py`
  - [x] `api_requerimientos_modalidad()` en `views.py`
  - [x] Agregar rutas en `urls.py`
- [ ] 4. **Probar en desarrollo** (pendiente del usuario):
  - [ ] Cargar modalidad con 20 menús
  - [ ] Verificar agrupación por semanas
  - [ ] Verificar validador en cada semana
  - [ ] Verificar sección de menús especiales al final
- [ ] 5. **Casos de prueba** (pendiente del usuario):
  - [ ] Semana que cumple todos los requisitos (verde)
  - [ ] Semana que no cumple (rojo)
  - [ ] Modalidad sin requerimientos definidos
  - [ ] Menos de 20 menús generados

---

## 🎉 ESTADO: IMPLEMENTACIÓN COMPLETADA Y BUGS CORREGIDOS

**Fecha de implementación:** 2026-02-13
**Fecha de corrección de bugs:** 2026-02-13

### Archivos Modificados:

1. **`erp_chvs/nutricion/views.py`**
   - ✅ Agregado `api_validar_semana()` (líneas 1043-1135)
   - ✅ Agregado `api_requerimientos_modalidad()` (líneas 1137-1182)

2. **`erp_chvs/nutricion/urls.py`**
   - ✅ Agregadas rutas para validación semanal (líneas 54-55)

3. **`erp_chvs/static/css/nutricion/lista_menus.css`**
   - ✅ Agregados ~200 líneas de estilos CSS para validador semanal

4. **`erp_chvs/static/js/nutricion/modules/ModalidadesManager.js`**
   - ✅ Reemplazado método `generarTarjetasMenus()` (líneas 198-272)
   - ✅ Agregado método `generarSeccionSemana()` (nuevo)
   - ✅ Agregado método `generarSeccionEspeciales()` (nuevo)
   - ✅ Agregado método `cargarValidadoresSemana()` (nuevo)
   - ✅ Modificado `crearAcordeon()` para cargar validadores
   - ✅ Modificado `generarMenusAutomaticos()` para cargar validadores
   - ✅ Modificado `actualizarMenusModalidad()` para recargar validadores

### Archivos de Respaldo:

- **`ModalidadesManager.js.backup`** - Respaldo del archivo original

### Bugs Corregidos (2026-02-13):

#### 🔴 Bug #1 - Lógica de conteo (CRÍTICO)
- **Problema:** Contaba preparaciones totales en lugar de días únicos
- **Solución:** Implementado algoritmo con `set()` para contar días únicos
- **Impacto:** Validaciones ahora matemáticamente correctas

#### 🟠 Bug #2 - Inconsistencia nombre/componente (ALTO)
- **Problema:** Backend devolvía `'nombre'`, frontend esperaba `'componente'`
- **Solución:** Backend cambiado a `'componente'`
- **Impacto:** Nombres de componentes ahora se muestran correctamente

#### 🟡 Bug #3 - Clases CSS faltantes (MEDIO)
- **Problema:** 13 clases CSS usadas en JS pero no definidas
- **Solución:** Agregadas todas las clases faltantes (+140 líneas CSS)
- **Impacto:** UI completa con estilos apropiados

### Próximos Pasos para el Usuario:

1. **Refrescar caché del navegador** (Ctrl+Shift+R en Windows/Linux, Cmd+Shift+R en Mac)
2. **Reiniciar servidor Django** si está corriendo
3. **Acceder a** `/nutricion/menus/`
4. **Seleccionar un municipio y programa** con menús existentes
5. **Verificar que se muestren las 4 semanas** con validadores
6. **Verificar que los menús especiales** aparezcan en sección separada al final
7. **Probar escenarios de validación:**
   - Semana que cumple (todos ✅ verdes)
   - Semana que NO cumple (algunos ❌ rojos con mensajes "Falta X")

---

## 🎨 Vista Previa Visual

```
┌───────────────────────────────────────────────────────────────────────┐
│ MODALIDAD: COMPLEMENTO ALIMENTARIO PREPARADO AM (mod1)               │
│ 20 / 20 menús                                                         │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│ 📅 SEMANA 1                                                           │
│ ┌───────────────────────────────────────────────────────────────────┐│
│ │   [1]     [2]     [3]     [4]     [5]                            ││
│ └───────────────────────────────────────────────────────────────────┘│
│                                                                       │
│ ✅ Validación de Cumplimiento - Semana 1                             │
│ ┌───────────────────────────────────────────────────────────────────┐│
│ │ ✅ Bebida con leche                              5/5              ││
│ │ ✅ Alimento proteico                             3/3              ││
│ │ ✅ Cereal acompañante                            5/5              ││
│ │ ❌ Fruta                                         1/2 - FALTA 1    ││
│ │ ✅ Azúcares                                      5/5              ││
│ │ ✅ Grasas                                        5/5              ││
│ │ ✅ Agua                                          5/5              ││
│ │                                                                   ││
│ │ ❌ NO CUMPLE (1 componente faltante)                             ││
│ └───────────────────────────────────────────────────────────────────┘│
│                                                                       │
│ 📅 SEMANA 2, 3, 4... (similar)                                        │
│                                                                       │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│ 🌟 Menús Especiales y Generación IA                                  │
│ ┌───────────────────────────────────────────────────────────────────┐│
│ │ [+]         [🤖]      [Navidad]   [Día Niño]                     ││
│ │ Crear       IA                                                    ││
│ │ Especial                                                          ││
│ └───────────────────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Notas Importantes

1. **Performance**: El validador se carga asíncronamente para no bloquear el renderizado inicial
2. **Flexibilidad**: Si hay menos de 20 menús, solo se muestran las semanas con menús
3. **Escalabilidad**: El sistema permite agregar más de 20 menús (especiales) sin romper la agrupación
4. **UX**: Los menús especiales están claramente separados de los regulares
5. **Validación**: Solo visual - no bloquea guardar (según requisito del usuario)

---

## 🚀 Próximos Pasos

1. ¿Apruebas este plan?
2. ¿Hay algo que quieras modificar o agregar?
3. ¿Procedemos con la implementación?
