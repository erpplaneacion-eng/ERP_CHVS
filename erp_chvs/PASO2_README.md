# 📊 PASO 2: Migración del Análisis Nutricional a Vista de Preparaciones

## ✅ Estado: COMPLETADO

## 📋 Descripción

El **Paso 2** integra completamente el análisis nutricional en la vista del editor de preparaciones, organizando la información por nivel escolar mediante tabs de Bootstrap.

### Antes del Paso 2:
- Vista simple con tabla plana de preparaciones e ingredientes
- Sin diferenciación por nivel escolar
- Sin análisis nutricional visible
- Rangos agregados (no específicos por nivel)

### Después del Paso 2:
- ✅ Tabs por nivel escolar (Preescolar, Primaria 1-3, Primaria 4-5, Secundaria, Media)
- ✅ Tabla de ingredientes con pesos específicos por nivel
- ✅ Rangos (min/max) filtrados por nivel escolar + modalidad
- ✅ Panel de totales nutricionales en tiempo real
- ✅ Sistema de semaforización (verde/amarillo/rojo)
- ✅ Validación de rangos al editar pesos
- ✅ Cálculo automático de nutrientes
- ✅ Sincronización de pesos base
- ✅ Guardar cambios por nivel

## 🏗️ Arquitectura Implementada

### Backend (`views.py`)

#### Vista principal: `vista_preparaciones_editor(request, id_menu)`
**Ubicación**: `nutricion/views.py` línea 326

**Cambios clave**:
```python
# 1. Obtiene todos los niveles escolares
niveles_escolares = TablaGradosEscolaresUapa.objects.all()

# 2. Obtiene requerimientos nutricionales por modalidad + nivel
requerimientos = TablaRequerimientosNutricionales.objects.filter(
    id_modalidad=menu.id_modalidad
)

# 3. Para cada nivel escolar:
for nivel in niveles_escolares:
    # - Crea o recupera análisis
    analisis, _ = TablaAnalisisNutricionalMenu.objects.get_or_create(...)

    # - Carga ingredientes configurados
    ingredientes_nivel = TablaIngredientesPorNivel.objects.filter(id_analisis=analisis)

    # - Construye filas con rangos específicos del nivel
    rango = _resolver_grupo_y_rango_por_nivel(menu, preparacion, ingrediente, nivel)

    # - Calcula totales, porcentajes y estados de semáforo
    # - Agrega a niveles_data
```

**Estructura de datos enviada al template**:
```python
niveles_data = [
    {
        'nivel': {
            'id': 'prescolar',
            'nombre': 'Preescolar'
        },
        'filas': [
            {
                'id_preparacion': 1,
                'preparacion': 'Leche con chocolate',
                'id_ingrediente': '01234',
                'ingrediente': 'Leche entera',
                'grupo': 'Lácteos',
                'minimo': 150,
                'maximo': 200,
                'peso_neto': 150,
                'calorias': 90,
                'proteina': 4.5,
                # ... otros nutrientes
            },
            # ... más ingredientes
        ],
        'totales': { 'calorias': 280, 'proteina': 12, ... },
        'requerimientos': { 'calorias': 276, 'proteina': 9.9, ... },
        'porcentajes': { 'calorias': 101.4, 'proteina': 121.2, ... },
        'estados': { 'calorias': 'alto', 'proteina': 'alto', ... },
        'id_analisis': 123
    },
    # ... más niveles
]
```

#### Función auxiliar: `_resolver_grupo_y_rango_por_nivel()`
**Ubicación**: `nutricion/views.py` línea 265

**Novedad**: Ahora filtra `MinutaPatronMeta` por nivel escolar específico:
```python
metas = MinutaPatronMeta.objects.filter(
    id_modalidad=menu.id_modalidad,
    id_grado_escolar_uapa=nivel_escolar,  # ← FILTRO POR NIVEL (NUEVO)
    id_grupo_alimentos=grupo
)
```

Antes: Rangos agregados de todos los niveles
Ahora: Rangos específicos para cada nivel

#### Nuevo endpoint: `api_guardar_ingredientes_por_nivel(request, id_menu)`
**Ubicación**: `nutricion/views.py` línea 1637
**Ruta**: `POST /nutricion/api/menus/{id_menu}/guardar-ingredientes-por-nivel/`

**Función**:
1. Recibe datos de todos los niveles escolares
2. Para cada ingrediente:
   - Calcula valores nutricionales con `CalculoService`
   - Calcula peso bruto
   - Actualiza `TablaIngredientesPorNivel`
3. Recalcula totales del análisis
4. Retorna cantidad de registros actualizados

**Payload esperado**:
```json
{
  "niveles": [
    {
      "id_nivel_escolar": "prescolar",
      "id_analisis": 123,
      "ingredientes": [
        {
          "id_preparacion": 1,
          "id_ingrediente": "01234",
          "peso_neto": 160.5
        }
      ]
    }
  ]
}
```

### Frontend

#### Template: `preparaciones_editor.html`
**Ubicación**: `templates/nutricion/preparaciones_editor.html`

**Estructura**:
```html
<!-- Toolbar con botones -->
<div class="prep-editor-toolbar">
    <button id="btnAgregarFila">Agregar ingrediente</button>
    <button id="btnGuardarCambios">Guardar cambios</button>
    <button id="btnSincronizarPesos">Sincronizar pesos base</button>
    <button id="btnRecalcular">Recalcular</button>
</div>

<!-- Tabs de niveles escolares -->
<ul class="nav nav-tabs">
    {% for nivel_data in niveles_data %}
    <li class="nav-item">
        <button class="nav-link">{{ nivel_data.nivel.nombre }}</button>
    </li>
    {% endfor %}
</ul>

<!-- Contenido de cada tab -->
<div class="tab-content">
    {% for nivel_data in niveles_data %}
    <div class="tab-pane" id="panel-{{ nivel_data.nivel.id }}">

        <!-- Tabla de ingredientes -->
        <table class="tabla-ingredientes">
            <thead>
                <tr>
                    <th>Preparación</th>
                    <th>Ingrediente ICBF</th>
                    <th>Grupo</th>
                    <th>Rango (g)</th>
                    <th>Peso neto (g)</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {% for fila in nivel_data.filas %}
                <tr>
                    <td>{{ fila.preparacion }}</td>
                    <td>{{ fila.ingrediente }}</td>
                    <td>{{ fila.grupo }}</td>
                    <td>
                        <span class="badge-rango">
                            {{ fila.minimo }} - {{ fila.maximo }}
                        </span>
                    </td>
                    <td>
                        <input type="number" class="input-peso"
                               value="{{ fila.peso_neto }}"
                               data-minimo="{{ fila.minimo }}"
                               data-maximo="{{ fila.maximo }}" />
                    </td>
                    <td>
                        <span class="badge-estado ok">OK</span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- Panel de totales nutricionales -->
        <div class="panel-totales">
            <div class="grid-nutrientes">
                <!-- Card de calorías -->
                <div class="nutriente-card {{ nivel_data.estados.calorias }}">
                    <div class="nutriente-label">Calorías</div>
                    <div class="nutriente-valor">
                        <span class="valor-actual">{{ nivel_data.totales.calorias }}</span> kcal
                    </div>
                    <div class="nutriente-porcentaje {{ nivel_data.estados.calorias }}">
                        <span class="porcentaje-actual">{{ nivel_data.porcentajes.calorias }}</span>%
                    </div>
                    <div class="nutriente-requerimiento">
                        Meta: {{ nivel_data.requerimientos.calorias }} kcal
                    </div>
                </div>
                <!-- ... más nutrientes ... -->
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

**CSS destacado**:
- `.nav-tabs` - Estilo de tabs
- `.tabla-ingredientes` - Tabla scrollable con sticky header
- `.input-peso` - Input de peso con validación visual
- `.input-peso.fuera-rango` - Clase para pesos fuera de rango
- `.nutriente-card.optimo/.aceptable/.alto` - Colores de semáforo
- `.badge-estado.ok/.fuera` - Indicador de validación

#### JavaScript: `preparaciones_editor.js`
**Ubicación**: `static/js/nutricion/preparaciones_editor.js`

**Funciones principales**:

1. **`validarRango(peso, minimo, maximo)`**
   - Valida si el peso está dentro del rango permitido
   - Retorna `{ valido: boolean, clase: 'ok'|'fuera' }`

2. **`actualizarEstadoFila(row)`**
   - Valida el peso de una fila
   - Actualiza clases CSS del input y badge
   - Marca visualmente si está fuera de rango

3. **`calcularTotalesNivel(nivelId)`**
   - Recorre todos los ingredientes del nivel
   - Calcula factor de proporción: `peso_actual / peso_original`
   - Suma nutrientes proporcionalmente
   - Retorna objeto con totales

4. **`actualizarPanelTotales(nivelId, totales, requerimientos)`**
   - Actualiza valores en las cards de nutrientes
   - Calcula porcentajes: `(total / requerimiento) * 100`
   - Determina estado del semáforo:
     - `0-35%` → óptimo (verde)
     - `35-70%` → aceptable (amarillo)
     - `>70%` → alto (rojo)
   - Actualiza clases CSS de las cards

5. **`recalcularNivel(nivelId)`**
   - Llama a `calcularTotalesNivel()`
   - Llama a `actualizarPanelTotales()`
   - Se ejecuta automáticamente al editar pesos

**Event Listeners**:

```javascript
// Input en tiempo real
document.addEventListener('input', (e) => {
    if (e.target.classList.contains('input-peso')) {
        actualizarEstadoFila(row);
        recalcularNivel(nivelId);
    }
});

// Botón guardar cambios
btnGuardarCambios.addEventListener('click', async () => {
    // Recolecta datos de todos los niveles
    // POST a /nutricion/api/menus/{id}/guardar-ingredientes-por-nivel/
    // Recarga la página
});

// Botón sincronizar pesos
btnSincronizarPesos.addEventListener('click', async () => {
    // Confirma con usuario
    // Para cada nivel: POST a /nutricion/api/sincronizar-pesos-preparaciones/
    // Recarga la página
});

// Botón recalcular
btnRecalcular.addEventListener('click', () => {
    // Recalcula todos los niveles manualmente
});
```

## 🚀 Cómo Probar

### 1. Acceder a la vista

```bash
# Iniciar servidor Django
cd erp_chvs/
python manage.py runserver
```

Navegar a: `http://localhost:8000/nutricion/menus/{id_menu}/preparaciones-editor/`

### 2. Verificar tabs por nivel escolar

✅ Debería ver 5 tabs (uno por cada nivel escolar)
✅ Al cambiar de tab, se muestra tabla diferente con pesos específicos
✅ Rangos (min/max) varían según el nivel

### 3. Editar pesos

1. Cambiar el valor en un input de peso
2. **Observar**:
   - ✅ Si está fuera de rango → input se marca en rojo
   - ✅ Badge cambia de "OK" a "FUERA"
   - ✅ Totales nutricionales se actualizan en tiempo real
   - ✅ Porcentajes se recalculan
   - ✅ Colores de semáforo cambian (verde/amarillo/rojo)

### 4. Guardar cambios

1. Click en "Guardar cambios"
2. **Observar**:
   - ✅ Mensaje de confirmación
   - ✅ Recarga la página
   - ✅ Pesos se mantienen guardados

### 5. Sincronizar pesos base

1. Click en "Sincronizar pesos base"
2. Confirmar acción
3. **Observar**:
   - ✅ Se copian gramajes de `TablaPreparacionIngredientes`
   - ✅ A todos los niveles en `TablaIngredientesPorNivel`
   - ✅ Se recalculan nutrientes automáticamente

### 6. Verificar en base de datos

```sql
-- Ver pesos por nivel
SELECT
    n.nivel_escolar_uapa,
    p.preparacion,
    i.nombre_ingrediente,
    inp.peso_neto,
    inp.calorias,
    inp.proteina
FROM nutricion_tabla_ingredientes_por_nivel inp
JOIN nutricion_tabla_analisis_nutricional_menu anm ON inp.id_analisis_id = anm.id_analisis
JOIN tabla_grados_escolares_uapa n ON anm.id_nivel_escolar_uapa_id = n.id_grado_escolar_uapa
JOIN nutricion_tabla_preparaciones p ON inp.id_preparacion_id = p.id_preparacion
JOIN tabla_ingredientes_siesa i ON inp.id_ingrediente_siesa_id = i.id_ingrediente_siesa
WHERE anm.id_menu_id = 1
ORDER BY n.nivel_escolar_uapa, p.preparacion;

-- Ver totales del análisis
SELECT
    m.menu,
    n.nivel_escolar_uapa,
    anm.total_calorias,
    anm.total_proteina,
    anm.porcentaje_adecuacion_calorias,
    anm.estado_adecuacion_calorias
FROM nutricion_tabla_analisis_nutricional_menu anm
JOIN nutricion_tabla_menus m ON anm.id_menu_id = m.id_menu
JOIN tabla_grados_escolares_uapa n ON anm.id_nivel_escolar_uapa_id = n.id_grado_escolar_uapa
WHERE m.id_menu = 1;
```

## 📁 Archivos Modificados

### Backend
- ✅ `nutricion/views.py` (líneas 265-511, 1637-1763)
  - `vista_preparaciones_editor()` - Reescrita completamente
  - `_resolver_grupo_y_rango_por_nivel()` - Nueva función
  - `api_guardar_ingredientes_por_nivel()` - Nuevo endpoint

- ✅ `nutricion/urls.py` (línea 52)
  - Agregada ruta para `api_guardar_ingredientes_por_nivel`

### Frontend
- ✅ `templates/nutricion/preparaciones_editor.html` (completamente reescrito)
  - Tabs de Bootstrap
  - Tablas por nivel
  - Panel de totales nutricionales
  - Indicadores de semáforo

- ✅ `static/js/nutricion/preparaciones_editor.js` (completamente reescrito)
  - Cálculo en tiempo real
  - Validación de rangos
  - Sincronización de pesos
  - Guardar cambios

## 🎯 Funcionalidades Implementadas

### ✅ Visualización
- [x] Tabs por nivel escolar
- [x] Tabla de ingredientes por nivel
- [x] Rangos específicos por nivel
- [x] Panel de totales nutricionales
- [x] Indicadores de semáforo (verde/amarillo/rojo)

### ✅ Edición
- [x] Editar pesos por nivel
- [x] Validación de rangos en tiempo real
- [x] Cálculo automático de nutrientes
- [x] Actualización de totales y porcentajes

### ✅ Persistencia
- [x] Guardar cambios en `TablaIngredientesPorNivel`
- [x] Recalcular totales en `TablaAnalisisNutricionalMenu`
- [x] Sincronizar pesos base desde preparaciones

### ✅ UX
- [x] Feedback visual de validación
- [x] Colores de semáforo dinámicos
- [x] Notificaciones de éxito/error
- [x] Confirmación antes de acciones importantes

## 🔄 Comparación con Paso 1

| Aspecto | Paso 1 | Paso 2 |
|---------|--------|--------|
| **Alcance** | Sincronización de gramajes | Vista integrada completa |
| **Interfaz** | Sin cambios en UI | Tabs + Panel de análisis |
| **Edición** | No permite edición | Edición en tiempo real |
| **Validación** | Solo en backend | Frontend + Backend |
| **Cálculos** | Backend estático | Tiempo real en frontend |
| **Rangos** | Agregados | Específicos por nivel |

## 📊 Próximos Pasos

### PASO 3: Asegurar filtrado por nivel en todos los cálculos ✅ (Parcialmente completado)
- [x] `_resolver_grupo_y_rango_por_nivel()` ya filtra por nivel
- [ ] Verificar otros puntos del sistema que usen rangos

### PASO 4: Mejorar UI con sliders
- [ ] Reemplazar inputs numéricos por sliders
- [ ] Validación visual de rangos con colores
- [ ] Tooltips con información nutricional

### PASO 5: Funciones auxiliares
- [ ] Copiar pesos entre niveles
- [ ] Calcular peso óptimo automáticamente
- [ ] Sugerencias de ajuste para cumplir metas

## 🐛 Debugging

### Error: "niveles_data is not defined"
**Solución**: Verificar que el template tenga:
```html
<script id="niveles-data" type="application/json">{{ niveles_json|safe }}</script>
```

### Error: "Cannot read property 'filas' of undefined"
**Solución**: Asegurarse de que todos los niveles escolares tienen datos en `niveles_data`

### Los totales no se actualizan al editar
**Solución**:
1. Verificar que el input tenga clase `input-peso`
2. Verificar que el evento `input` esté conectado
3. Abrir consola del navegador para ver errores JS

### Rangos no se muestran correctamente
**Solución**: Verificar que `MinutaPatronMeta` tiene datos para:
- La modalidad del menú
- El nivel escolar específico
- El grupo de alimentos del ingrediente

```sql
SELECT
    mo.modalidad,
    n.nivel_escolar_uapa,
    c.componente,
    g.grupo_alimentos,
    mpm.peso_neto_minimo,
    mpm.peso_neto_maximo
FROM nutricion_minuta_patron_meta mpm
JOIN modalidades_de_consumo mo ON mpm.id_modalidad_id = mo.id_modalidad
JOIN tabla_grados_escolares_uapa n ON mpm.id_grado_escolar_uapa_id = n.id_grado_escolar_uapa
JOIN componentes_de_alimentos c ON mpm.id_componente_id = c.id_componente
JOIN grupos_de_alimentos g ON mpm.id_grupo_alimentos_id = g.id_grupo_alimentos
WHERE mo.id_modalidad = 'CAJM'
  AND n.id_grado_escolar_uapa = 'prescolar';
```

## ✅ Conclusión

El **PASO 2** ha sido completado exitosamente. La vista de preparaciones ahora incluye:

✅ Análisis nutricional completo por nivel escolar
✅ Edición en tiempo real con validación
✅ Cálculos automáticos de nutrientes y porcentajes
✅ Sistema de semaforización visual
✅ Persistencia de cambios en base de datos

**Resultado**: Los nutricionistas pueden ahora gestionar menús con análisis nutricional integrado, viendo en tiempo real cómo sus ajustes afectan los requerimientos de cada nivel escolar.
