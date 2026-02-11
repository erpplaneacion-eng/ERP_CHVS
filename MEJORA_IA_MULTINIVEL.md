# ✅ Mejora Implementada: Generación Multi-nivel con IA

**Fecha**: 2026-02-11
**Tipo**: Feature Enhancement
**Módulo**: Nutrición - Generación de Menús con IA (Gemini)

---

## 🎯 Objetivo

Permitir que el servicio de IA genere menús con **pesos específicos para TODOS los niveles educativos** en una sola llamada, aprovechando al máximo la capacidad del backend.

---

## 📋 Problema Anterior

### **Antes de la mejora:**
- ❌ El usuario debía seleccionar **1 solo nivel educativo**
- ❌ Se generaba menú solo para ese nivel
- ❌ Los otros 4 niveles quedaban **sin análisis nutricional**
- ❌ Se requerían **5 llamadas separadas** para completar un menú
- ❌ Inconsistencia: el backend podía generar multi-nivel, pero el frontend no lo permitía

### **Flujo anterior:**
```
Usuario selecciona "Preescolar"
    ↓
Gemini genera menú solo para Preescolar
    ↓
❌ Primaria 1-3: Sin pesos
❌ Primaria 4-5: Sin pesos
❌ Secundaria: Sin pesos
❌ Media: Sin pesos
```

---

## ✨ Solución Implementada

### **Después de la mejora:**
- ✅ El usuario **NO selecciona niveles** (automático)
- ✅ Se genera menú completo para **todos los niveles** (5 niveles)
- ✅ **Una sola llamada** a Gemini
- ✅ Menú completo desde el inicio

### **Flujo nuevo:**
```
Usuario hace clic en "🤖 Generar con IA"
    ↓
Gemini genera menú para TODOS los niveles
    ↓
✅ Preescolar: Con pesos y análisis
✅ Primaria 1-3: Con pesos y análisis
✅ Primaria 4-5: Con pesos y análisis
✅ Secundaria: Con pesos y análisis
✅ Media: Con pesos y análisis
```

---

## 🔧 Archivos Modificados

### **1. Backend: `nutricion/views.py`**

**Cambios:**
- Eliminado parámetro `nivel_educativo` de la validación
- Se pasa `niveles_educativos=None` al servicio (genera todos)
- Mensaje de éxito actualizado

**Antes:**
```python
nivel_educativo = data.get('nivel_educativo')
if not all([programa_id, modalidad_id, nivel_educativo]):
    return JsonResponse({'error': 'Faltan parámetros...'}, status=400)

menu = MenuService.generar_menu_con_ia(
    id_programa=programa_id,
    id_modalidad=modalidad_id,
    nivel_educativo=nivel_educativo  # Solo 1 nivel
)
```

**Después:**
```python
# No se requiere nivel_educativo
if not all([programa_id, modalidad_id]):
    return JsonResponse({'error': 'Faltan parámetros...'}, status=400)

menu = MenuService.generar_menu_con_ia(
    id_programa=programa_id,
    id_modalidad=modalidad_id,
    niveles_educativos=None  # None = todos los niveles
)
```

---

### **2. Frontend: `templates/nutricion/lista_menus.html`**

**Cambios:**
- Eliminado el `<select>` de niveles educativos
- Agregada información detallada sobre la generación multi-nivel
- Mensajes de loading actualizados

**Antes:**
```html
<div class="form-group">
    <label>Nivel Educativo <span class="required">*</span></label>
    <select id="nivelEducativoIA" class="form-control" required>
        <option value="">Seleccione un nivel...</option>
        <option value="Preescolar">Preescolar</option>
        <!-- ... -->
    </select>
</div>
```

**Después:**
```html
<div class="alert alert-info">
    <i class="fas fa-lightbulb"></i> <strong>Generación Multi-nivel Automática</strong>
    <p>La IA generará un menú con pesos específicos para todos los niveles:</p>
    <ul>
        <li>Preescolar</li>
        <li>Primaria (1°, 2° y 3°)</li>
        <li>Primaria (4° y 5°)</li>
        <li>Secundaria</li>
        <li>Media y Ciclo Complementario</li>
    </ul>
    <p>⏱️ Este proceso puede tardar 15-30 segundos.</p>
</div>
```

---

### **3. Frontend: `static/js/nutricion/menus_avanzado_refactorizado.js`**

**Cambios:**
- Eliminada validación de `nivelEducativoIA`
- No se envía `nivel_educativo` en el request body
- Mensajes de éxito/error mejorados

**Antes:**
```javascript
const nivelEducativo = document.getElementById('nivelEducativoIA').value;

if (!modalidadId || !nivelEducativo) {
    alert('Por favor seleccione un nivel educativo.');
    return;
}

body: JSON.stringify({
    programa_id: this.programaActual.id,
    modalidad_id: modalidadId,
    nivel_educativo: nivelEducativo  // Solo 1 nivel
})
```

**Después:**
```javascript
// No se requiere nivel
if (!modalidadId) {
    alert('Error: modalidad no seleccionada.');
    return;
}

body: JSON.stringify({
    programa_id: this.programaActual.id,
    modalidad_id: modalidadId
    // No se envía nivel_educativo - genera todos
})
```

---

## 🎬 Cómo Usar la Nueva Funcionalidad

### **Paso 1: Acceder al módulo de Nutrición**
```
Navegación: Dashboard → Nutrición → Menús
```

### **Paso 2: Seleccionar Programa**
1. Filtrar por **Municipio**
2. Seleccionar **Programa** activo

### **Paso 3: Generar Menú con IA**
1. Dentro de una modalidad (ej: "COMPLEMENTO AM"), hacer clic en el botón:
   ```
   🤖 Generar con IA
   ```

2. Se abre el modal con la información:
   ```
   ┌─────────────────────────────────────────┐
   │ 🤖 Generar Menú con IA (Gemini)         │
   ├─────────────────────────────────────────┤
   │ ℹ️ Generación Multi-nivel Automática    │
   │                                         │
   │ La IA generará pesos para:             │
   │ • Preescolar                            │
   │ • Primaria (1°, 2° y 3°)               │
   │ • Primaria (4° y 5°)                   │
   │ • Secundaria                            │
   │ • Media y Ciclo Complementario         │
   │                                         │
   │ ⏱️ Puede tardar 15-30 segundos          │
   │                                         │
   │ [✨ Generar Menú] [❌ Cancelar]        │
   └─────────────────────────────────────────┘
   ```

3. Hacer clic en **"Generar Menú para Todos los Niveles"**

4. Esperar (15-30 segundos) mientras Gemini genera el menú

5. Al finalizar, se muestra:
   ```
   ┌─────────────────────────────────────────┐
   │ ✅ ¡Menú Generado Exitosamente!         │
   ├─────────────────────────────────────────┤
   │ La IA ha creado el menú: Menú IA - ... │
   │                                         │
   │ ✅ Preparaciones creadas                │
   │ ✅ Ingredientes configurados            │
   │ ✅ Análisis nutricional para 5 niveles  │
   │                                         │
   │ ¿Deseas gestionar las preparaciones?   │
   │ [Sí, ir a preparaciones] [Después]     │
   └─────────────────────────────────────────┘
   ```

---

## 📊 Resultado Final

### **Estructura de datos creada:**

```
TablaMenus (1 menú base)
    ├── Nombre: "Menú IA - COMPLEMENTO AM"
    ├── Modalidad: COMPLEMENTO AM
    └── Programa: [programa seleccionado]

TablaPreparaciones (N preparaciones compartidas)
    ├── "Arroz con Leche"
    ├── "Fruta Fresca"
    └── ...

TablaAnalisisNutricionalMenu (5 análisis - UNO POR NIVEL)
    ├── Preescolar
    │   ├── total_calorias: 450 kcal
    │   ├── total_proteina: 15g
    │   └── TablaIngredientesPorNivel
    │       ├── Arroz: 50g neto, 58.8g bruto
    │       ├── Leche: 200ml neto, 200ml bruto
    │       └── ... (con nutrientes calculados)
    │
    ├── Primaria 1-3
    │   ├── total_calorias: 520 kcal
    │   └── TablaIngredientesPorNivel (pesos diferentes)
    │
    ├── Primaria 4-5
    ├── Secundaria
    └── Media y Ciclo Complementario
```

---

## ✅ Beneficios

1. **Eficiencia**:
   - Antes: 5 clics → 5 llamadas a Gemini → 5 menús incompletos
   - Ahora: 1 clic → 1 llamada a Gemini → 1 menú completo

2. **Consistencia**:
   - Todas las preparaciones compartidas entre niveles
   - Pesos ajustados según necesidades nutricionales de cada nivel

3. **Tiempo**:
   - Ahorra ~4 minutos por menú (5 generaciones vs 1)

4. **Experiencia de usuario**:
   - Menos decisiones, más automatización
   - Interfaz más clara y directa

5. **Costo**:
   - Mismo consumo de tokens API (1 llamada grande vs 5 pequeñas)
   - Mejor aprovechamiento del contexto de la IA

---

## ⚠️ Requisitos Previos

1. **Clave API de Gemini configurada**:
   ```bash
   # Archivo: erp_chvs/.env
   GEMINI_API_KEY=tu-clave-api-aquí
   ```

2. **Minuta Patrón configurada**:
   - Archivo: `nutricion/data/minuta_patron.json`
   - Debe contener patrones para la modalidad seleccionada

3. **Alimentos ICBF en base de datos**:
   - Tabla: `TablaAlimentos2018Icbf`
   - Debe tener alimentos con valores nutricionales

---

## 🧪 Testing

### **Prueba manual:**
```bash
cd erp_chvs/
python test_gemini.py
```

**Verificar**:
- ✅ Se crea 1 menú
- ✅ Se crean N preparaciones
- ✅ Se crean 5 análisis nutricionales (uno por nivel)
- ✅ Cada análisis tiene pesos y nutrientes calculados
- ✅ Los totales nutricionales están poblados

---

## 🐛 Troubleshooting

### **Error: "Clave API de Gemini no configurada"**
**Solución**: Verificar archivo `.env` y reiniciar servidor Django

### **Error: "No se encontraron Minutas Patrón"**
**Solución**: Verificar que `minuta_patron.json` tenga datos para la modalidad seleccionada

### **Error: "La IA no pudo generar una propuesta válida"**
**Causas posibles**:
- Conexión a Gemini API fallida
- Token API inválido o expirado
- Minuta Patrón mal formateada
- No hay alimentos ICBF suficientes

---

## 📝 Notas Adicionales

- El servicio `MenuService` ya soportaba multi-nivel desde antes
- Esta mejora solo sincroniza el frontend con la capacidad del backend
- El modelo de IA usado es `gemini-2.5-flash` con `temperature=0.2`
- La generación toma más tiempo (15-30s) porque genera más datos
- Los menús generados son editables posteriormente por el usuario

---

## 🔮 Mejoras Futuras (Opcional)

1. **Opción de selección parcial de niveles**:
   - Permitir generar solo para 2-3 niveles específicos
   - Útil si el programa no atiende todos los niveles

2. **Regeneración por nivel**:
   - Permitir regenerar solo un nivel si el usuario no está conforme

3. **Comparación de menús**:
   - Mostrar comparativa de porciones entre niveles

4. **Export multi-nivel**:
   - Exportar Excel con todos los niveles en una sola hoja

---

## ✅ Conclusión

La mejora implementada **elimina la desincronización** entre frontend y backend, permitiendo que los usuarios aprovechen al máximo la capacidad del servicio de IA. Los menús generados ahora están **completos desde el inicio** con análisis nutricional para todos los niveles educativos.
