# 🧪 Tests del Paso 1: Sincronización de Gramajes

## 📋 Descripción

Este conjunto de tests verifica que el **Paso 1** de la migración funciona correctamente:
- Los gramajes guardados en `TablaPreparacionIngredientes` se usan como peso inicial
- La función de sincronización crea correctamente los registros en `TablaIngredientesPorNivel`
- Los cálculos nutricionales son correctos
- Los totales y porcentajes se calculan bien
- La semaforización funciona correctamente

## 🚀 Cómo Ejecutar los Tests

### Opción 1: Usando el script (recomendado)

#### En Linux/WSL:
```bash
cd erp_chvs/
./run_tests_paso1.sh
```

#### En Windows:
```cmd
cd erp_chvs
run_tests_paso1.bat
```

### Opción 2: Comando directo

```bash
cd erp_chvs/
python manage.py test nutricion.tests_sincronizacion_pesos --verbosity=2
```

### Opción 3: Con pytest (si está instalado)

```bash
cd erp_chvs/
pytest nutricion/tests_sincronizacion_pesos.py -v
```

## 📊 Tests Incluidos

### Suite 1: `SincronizacionPesosTestCase`

1. **test_obtener_preparaciones_usa_gramaje**
   - ✅ Verifica que `_obtener_preparaciones_con_ingredientes()` usa el gramaje guardado
   - Espera: Peso de 150g para leche, 80g para arroz

2. **test_obtener_preparaciones_usa_100g_sin_gramaje**
   - ✅ Verifica que usa 100g cuando no hay gramaje
   - Espera: Peso de 100g por defecto

3. **test_sincronizar_pesos_crea_ingredientes_por_nivel**
   - ✅ Verifica que crea registros en `TablaIngredientesPorNivel`
   - Espera: 2 ingredientes sincronizados

4. **test_sincronizar_pesos_calcula_valores_nutricionales**
   - ✅ Verifica cálculos nutricionales
   - Espera: Calorías = 60 Kcal/100g × 150g = 90 Kcal

5. **test_recalcular_totales_analisis**
   - ✅ Verifica suma de totales
   - Espera: Total calorías = 90 + 104 = 194 Kcal

6. **test_recalcular_porcentajes_adecuacion**
   - ✅ Verifica cálculo de porcentajes
   - Espera: 194 / 276 × 100 ≈ 70.3%

7. **test_semaforizacion_estados**
   - ✅ Verifica estados de semaforización
   - Espera: Estado "aceptable" o "alto" según porcentaje

8. **test_sincronizar_no_sobrescribe_si_false**
   - ✅ Verifica que respeta flag `sobrescribir_existentes=False`
   - Espera: No sobrescribe datos existentes

9. **test_sincronizar_si_sobrescribe_si_true**
   - ✅ Verifica que sobrescribe con `sobrescribir_existentes=True`
   - Espera: Actualiza de 150g a 200g

10. **test_obtener_analisis_completo_usa_gramaje**
    - ✅ Verifica que el análisis completo usa gramajes automáticamente
    - Espera: Pesos correctos sin sincronización explícita

### Suite 2: `APIEndpointTestCase`

1. **test_api_requiere_autenticacion**
   - ✅ Verifica que el endpoint requiere login
   - Espera: Código 302 o 403

2. **test_api_requiere_metodo_post**
   - ✅ Verifica que solo acepta POST
   - Espera: Código 405 para GET

3. **test_api_requiere_parametros**
   - ✅ Verifica validación de parámetros
   - Espera: Error 400 si faltan parámetros

4. **test_api_responde_correctamente**
   - ✅ Verifica respuesta exitosa
   - Espera: JSON con success=True

## 📝 Salida Esperada

Al ejecutar los tests, deberías ver algo similar a:

```
==========================================
EJECUTANDO TESTS - PASO 1
Sincronización de Gramajes
==========================================

Creating test database for alias 'default'...
System check identified no issues (0 silenced).

test_obtener_preparaciones_usa_gramaje (nutricion.tests_sincronizacion_pesos.SincronizacionPesosTestCase) ... ✅ Test 1 OK: _obtener_preparaciones_con_ingredientes usa gramaje
ok

test_obtener_preparaciones_usa_100g_sin_gramaje (nutricion.tests_sincronizacion_pesos.SincronizacionPesosTestCase) ... ✅ Test 2 OK: Usa 100g cuando no hay gramaje
ok

test_sincronizar_pesos_crea_ingredientes_por_nivel (nutricion.tests_sincronizacion_pesos.SincronizacionPesosTestCase) ... ✅ Test 3 OK: Sincronización crea registros en TablaIngredientesPorNivel
ok

... (más tests)

----------------------------------------------------------------------
Ran 14 tests in 0.234s

OK

==========================================
✅ TODOS LOS TESTS PASARON
==========================================
```

## ❌ Si Hay Errores

### Error: ModuleNotFoundError

```
ModuleNotFoundError: No module named 'nutricion'
```

**Solución**: Asegúrate de estar en el directorio `erp_chvs/`:
```bash
cd erp_chvs/
python manage.py test nutricion.tests_sincronizacion_pesos
```

### Error: Database Error

```
django.db.utils.OperationalError: (1045, "Access denied...")
```

**Solución**: Verifica que la base de datos de prueba pueda crearse:
- Asegúrate que PostgreSQL esté corriendo
- Verifica credenciales en `.env`
- Django usa `test_` + DB_NAME para tests

### Error: Import Error

```
ImportError: cannot import name 'AnalisisNutricionalService'
```

**Solución**: Verifica que el archivo `analisis_service.py` tenga los cambios del Paso 1.

## 🔍 Verificación Manual Adicional

Después de que pasen los tests, puedes verificar manualmente:

1. **En Django shell**:
```python
python manage.py shell

from nutricion.models import *
from nutricion.services import AnalisisNutricionalService

# Ver gramajes guardados
TablaPreparacionIngredientes.objects.filter(gramaje__gt=0).values('id_preparacion__preparacion', 'id_ingrediente_siesa__nombre_del_alimento', 'gramaje')

# Sincronizar
resultado = AnalisisNutricionalService.sincronizar_pesos_desde_preparaciones(
    id_menu=1,
    id_nivel_escolar='prescolar',
    sobrescribir_existentes=True
)
print(resultado)

# Ver resultado
TablaIngredientesPorNivel.objects.filter(id_analisis__id_menu_id=1).values('id_ingrediente_siesa__nombre_ingrediente', 'peso_neto', 'calorias')
```

2. **Verificar en BD directamente** (PostgreSQL):
```sql
-- Ver gramajes guardados
SELECT
    p.preparacion,
    a.nombre_del_alimento,
    pi.gramaje
FROM nutricion_tabla_preparacion_ingredientes pi
JOIN nutricion_tabla_preparaciones p ON pi.id_preparacion_id = p.id_preparacion
JOIN nutricion_tabla_alimentos_2018_icb a ON pi.id_ingrediente_siesa_id = a.codigo
WHERE pi.gramaje IS NOT NULL;

-- Ver ingredientes por nivel después de sincronizar
SELECT
    i.nombre_ingrediente,
    inp.peso_neto,
    inp.calorias,
    inp.proteina
FROM nutricion_tabla_ingredientes_por_nivel inp
JOIN tabla_ingredientes_siesa i ON inp.id_ingrediente_siesa_id = i.id_ingrediente_siesa
WHERE inp.id_analisis_id = 1;
```

## 📈 Próximos Pasos

Una vez que todos los tests pasen:
1. ✅ **Paso 1 completado**: Sincronización de gramajes funciona
2. ⏭️ **Paso 2**: Migrar análisis nutricional a vista de preparaciones
3. ⏭️ **Paso 3**: Filtrar rangos por nivel escolar
4. ⏭️ **Paso 4**: Mejorar UI con sliders
5. ⏭️ **Paso 5**: Funciones auxiliares de optimización

## 💡 Notas Importantes

- Los tests usan una **base de datos de prueba temporal** que se elimina después
- **No afectan tus datos reales**
- Cada test se ejecuta en una transacción que se hace rollback
- Los datos de prueba se crean automáticamente en `setUpTestData()`

## 🐛 Reportar Problemas

Si encuentras algún error en los tests:
1. Copia el output completo del error
2. Incluye el comando que ejecutaste
3. Menciona tu sistema operativo
4. Indica si estás en WSL o Windows nativo
