# 🔧 SOLUCIÓN: Error 400 al Agregar Ingrediente

## 🐛 Error Detectado

```
POST http://127.0.0.1:8000/nutricion/api/menus/365/guardar-preparaciones-editor/ 400 (Bad Request)
```

## 🔍 Análisis del Problema

### Frontend (preparaciones_editor.js - Línea 518)

```javascript
return {
    id_preparacion: modo === 'existente' ? parseInt(idPrep) : null,
    preparacion_nombre: modo === 'nueva' ? nomPrep : '',
    id_ingrediente: idIng,
    gramaje: parseFloat(gramaje) || 0  // ← PROBLEMA: envía 0 si está vacío
};
```

### Backend (views/preparaciones_editor.py - Línea 388-402)

```python
gramaje = None
if gramaje_raw not in (None, '', 'null'):
    gramaje = Decimal(str(gramaje_raw))
    if gramaje < 0:
        raise InvalidOperation('Gramaje negativo')

# Validación de rangos
if gramaje is not None and minimo is not None and gramaje < minimo:
    errores.append(f"Fila {idx + 1}: gramaje {gramaje}g por debajo del mínimo {minimo}g")
    continue  # ← AQUÍ SE RECHAZA SI GRAMAJE = 0 Y MÍNIMO > 0
```

## ⚠️ **Causas Posibles del Error 400**

### 1. **Gramaje 0 está fuera del rango mínimo**

Si el usuario NO ingresa un gramaje (campo vacío):
- Frontend envía: `gramaje: 0`
- Backend valida: `0 < minimo` (ej: si mínimo es 50g)
- **Resultado**: Error 400 con mensaje "gramaje por debajo del mínimo"

### 2. **Ingrediente no seleccionado**

Si el usuario no selecciona un ingrediente:
- Frontend envía: `id_ingrediente: ""`
- Backend en línea 372: `if not id_ingrediente: continue`
- **Resultado**: Error 400 (sin errores específicos pero sin guardar nada)

### 3. **Preparación no especificada**

Si selecciona "nueva preparación" pero no escribe el nombre:
- Frontend debería validarlo pero podría fallar
- Backend en línea 377-379: error si `preparacion_nombre` está vacío
- **Resultado**: Error 400 con mensaje "nombre de preparación requerido"

## ✅ SOLUCIÓN

### Opción 1: Permitir gramaje NULL en el backend (Recomendado)

El backend ya maneja `gramaje = None` correctamente, pero el frontend está enviando `0` en lugar de `null`.

**Modificar JavaScript** (línea 518):

```javascript
// ANTES
gramaje: parseFloat(gramaje) || 0

// DESPUÉS
gramaje: gramaje && gramaje.trim() !== '' ? parseFloat(gramaje) : null
```

**Modificar Backend** (línea 388-391) para aceptar NULL como valor válido:

```python
gramaje = None
if gramaje_raw not in (None, '', 'null', 0):  # ← Agregar 0 a la lista
    gramaje = Decimal(str(gramaje_raw))
    if gramaje < 0:
        raise InvalidOperation('Gramaje negativo')
```

### Opción 2: Validar en el frontend antes de enviar

**Modificar JavaScript** (línea 503-520):

```javascript
preConfirm: () => {
    const modo = document.getElementById('agregarModoPrep').value;
    const idPrep = document.getElementById('agregarPreparacionExistente').value;
    const nomPrep = document.getElementById('agregarPreparacionNueva').value.trim();
    const idIng = document.getElementById('agregarIngredienteId').value;
    const gramajeInput = document.getElementById('agregarGramaje').value;

    // Validaciones mejoradas
    if (!idIng) {
        return Swal.showValidationMessage('Debes seleccionar un ingrediente');
    }

    if (modo === 'existente' && !idPrep) {
        return Swal.showValidationMessage('Debes seleccionar una preparación');
    }

    if (modo === 'nueva' && !nomPrep) {
        return Swal.showValidationMessage('Debes escribir el nombre de la preparación');
    }

    // NUEVO: Validar gramaje
    let gramaje = null;
    if (gramajeInput && gramajeInput.trim() !== '') {
        gramaje = parseFloat(gramajeInput);
        if (isNaN(gramaje) || gramaje < 0) {
            return Swal.showValidationMessage('El gramaje debe ser un número positivo');
        }
    }

    return {
        id_preparacion: modo === 'existente' ? parseInt(idPrep) : null,
        preparacion_nombre: modo === 'nueva' ? nomPrep : '',
        id_ingrediente: idIng,
        gramaje: gramaje  // Ahora puede ser null
    };
}
```

### Opción 3: Hacer el campo gramaje obligatorio

**Modificar el HTML del modal** (línea 489-490):

```javascript
<label style="font-size:13px;font-weight:600;">Gramaje base (REQUERIDO)</label>
<input id="agregarGramaje"
       class="swal2-input"
       type="number"
       min="1"      // ← Establecer mínimo en 1
       step="0.1"
       style="margin:0;"
       placeholder="Ej: 100"
       required />   // ← Marcar como requerido
```

Y validar en `preConfirm`:

```javascript
if (!gramajeInput || gramajeInput.trim() === '') {
    return Swal.showValidationMessage('Debes ingresar un gramaje');
}
```

## 🎯 RECOMENDACIÓN FINAL

**Aplicar Opción 1 + Opción 2 combinadas:**

1. **Permitir NULL en backend** para flexibilidad
2. **Validar mejor en frontend** para evitar errores del usuario
3. **Mejorar mensajes de error** para que el usuario sepa qué falta

## 📝 Mensajes de Error Mejorados

**Modificar Backend** (línea 360):

```python
except Exception as e:
    import traceback
    error_detail = str(e)
    print(f"ERROR en guardar-preparaciones-editor: {error_detail}")
    print(traceback.format_exc())
    return JsonResponse({
        'success': False,
        'error': f'JSON inválido o datos incorrectos: {error_detail}'
    }, status=400)
```

**Modificar Frontend** (línea 532-533):

```javascript
const data = await response.json();
if (!data.success) {
    const errorMsg = data.error || 'Error desconocido al agregar ingrediente';

    // Si hay errores específicos, mostrarlos
    if (data.errores && data.errores.length > 0) {
        throw new Error(`Errores:\n${data.errores.join('\n')}`);
    }

    throw new Error(errorMsg);
}
```

## 🚀 Prueba de Verificación

Después de aplicar los cambios, probar:

1. **Caso 1**: Agregar ingrediente SIN gramaje
   - ✅ Debería permitirlo y asignar NULL

2. **Caso 2**: Agregar ingrediente CON gramaje válido (ej: 100g)
   - ✅ Debería funcionar normalmente

3. **Caso 3**: Agregar ingrediente CON gramaje negativo
   - ❌ Debería mostrar error claro

4. **Caso 4**: NO seleccionar ingrediente
   - ❌ Debería mostrar error claro

## 📊 Ejemplo de Debugging

Para ver el error exacto, abrir consola del navegador:

```javascript
// En la pestaña Network del DevTools
// Click en la petición fallida (400)
// Ver la respuesta JSON:

{
    "success": false,
    "error": "Fila 1: gramaje 0g por debajo del mínimo 50g",
    "errores": ["Fila 1: gramaje 0g por debajo del mínimo 50g"]
}
```

Esto confirmaría que el problema es el gramaje 0.

## 🔧 Archivo a Modificar

1. **Frontend**: `/static/js/nutricion/preparaciones_editor.js`
   - Líneas 503-520 (validación `preConfirm`)
   - Línea 518 (conversión de gramaje)

2. **Backend**: `/nutricion/views/preparaciones_editor.py`
   - Líneas 388-391 (manejo de gramaje NULL/0)
   - Línea 360 (mejores mensajes de error)

---

**Última actualización:** Febrero 2026
**Prioridad:** ALTA
**Impacto:** Bloquea funcionalidad de agregar ingredientes
