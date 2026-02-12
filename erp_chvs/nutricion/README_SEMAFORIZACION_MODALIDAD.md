# Semaforización por Nivel Escolar y Modalidad

## 📋 Resumen de Cambios

**Fecha**: Febrero 2025
**Objetivo**: Ajustar el sistema de semaforización para que considere **NIVEL ESCOLAR + MODALIDAD DE CONSUMO**

### ❌ Antes (Sistema Antiguo)

```
TablaRequerimientosNutricionales
├── id_nivel_escolar_uapa  ✅
├── id_modalidad           ❌ NO EXISTÍA
└── valores nutricionales (calorias, proteinas, etc.)

Problema:
- Todos los menús (CAJM/JT, Almuerzo, etc.) usaban los mismos requerimientos
- Un menú de 276 Kcal se comparaba contra 1300 Kcal diarias (21%)
- No reflejaba el aporte esperado según el tipo de complemento alimentario
```

### ✅ Después (Sistema Nuevo)

```
TablaRequerimientosNutricionales
├── id_nivel_escolar_uapa  ✅
├── id_modalidad           ✅ NUEVO
└── valores nutricionales según Minuta Patrón ICBF

Solución:
- Cada modalidad tiene requerimientos específicos:
  · CAJM/JT Preescolar: 276 Kcal (100% para esta modalidad)
  · Almuerzo Preescolar: 417 Kcal (100% para esta modalidad)
- La semaforización es precisa y relevante para cada tipo de menú
```

---

## 🎯 ¿Por qué este cambio?

### Problema Identificado

El sistema anterior comparaba todos los menús contra los **requerimientos diarios totales** (1300 Kcal para preescolar), sin considerar que:

- **CAJM/JT** (Complemento Alimentario Jornada Mañana/Tarde) debe aportar ~20% del requerimiento diario
- **Almuerzo** debe aportar ~32% del requerimiento diario

**Resultado**: La semaforización no era útil porque todos los menús aparecían en verde (0-35%) sin importar si estaban bien diseñados para su modalidad.

### Solución Implementada

Ahora cada modalidad tiene su propio 100% de referencia basado en la **Minuta Patrón ICBF**:

| Modalidad | Nivel | Requerimiento (100%) | Significado |
|-----------|-------|---------------------|-------------|
| CAJM/JT | Preescolar | 276 Kcal | Aporte esperado para desayuno/media mañana |
| Almuerzo | Preescolar | 417 Kcal | Aporte esperado para almuerzo |

**Ejemplo práctico**:

- Un menú CAJM/JT con **280 Kcal** → 280/276 = **101%** → 🔴 ALTO (excede ligeramente)
- El mismo menú en Almuerzo con **280 Kcal** → 280/417 = **67%** → 🟡 ACEPTABLE (aún puede mejorarse)

---

## 📊 Valores de la Minuta Patrón

Los siguientes valores se usaron para poblar la tabla (fuente: `MINUTA_PATRON_RESOLUCION.md`):

### CAJM/JT (Jornada Mañana/Tarde)

| Nivel Escolar | Cal (Kcal) | Prot (g) | Grasa (g) | CHO (g) | Ca (mg) | Fe (mg) | Na (mg) |
|---------------|------------|----------|-----------|---------|---------|---------|---------|
| Preescolar | 276 | 9.9 | 9.6 | 36.5 | 159 | 1.5 | 95 |
| Primaria 1-3 | 334 | 11.8 | 11.2 | 45.0 | 171 | 1.9 | 108 |
| Primaria 4-5 | 407 | 14.9 | 13.3 | 54.8 | 191 | 2.4 | 139 |
| Secundaria | 509 | 18.3 | 17.0 | 68.2 | 230 | 3.0 | 172 |
| Media y Ciclo Comp. | 592 | 21.1 | 19.9 | 79.3 | 245 | 3.5 | 191 |

### Almuerzo

| Nivel Escolar | Cal (Kcal) | Prot (g) | Grasa (g) | CHO (g) | Ca (mg) | Fe (mg) | Na (mg) |
|---------------|------------|----------|-----------|---------|---------|---------|---------|
| Preescolar | 417 | 15.6 | 13.4 | 56.3 | 110 | 2.9 | 132 |
| Primaria 1-3 | 457 | 16.8 | 14.5 | 61.8 | 126 | 3.4 | 144 |
| Primaria 4-5 | 550 | 19.9 | 17.2 | 74.8 | 145 | 4.2 | 173 |
| Secundaria | 682 | 24.6 | 21.9 | 92.0 | 173 | 5.2 | 213 |
| Media y Ciclo Comp. | 791 | 28.6 | 25.7 | 106.6 | 184 | 6.1 | 235 |

---

## 🚀 Pasos para Aplicar los Cambios

### 1️⃣ Aplicar la Migración

```bash
cd erp_chvs/
python manage.py migrate nutricion 0002_agregar_modalidad_requerimientos
```

**Resultado**: Se agrega el campo `id_modalidad` a la tabla `tabla_requerimientos_nutricionales`.

### 2️⃣ Poblar los Requerimientos con Datos de la Minuta Patrón

```bash
python manage.py shell < nutricion/poblar_requerimientos_modalidad.py
```

**O desde el shell interactivo**:

```python
python manage.py shell
>>> exec(open('nutricion/poblar_requerimientos_modalidad.py').read())
```

**Resultado**:
- Elimina requerimientos antiguos (sin modalidad)
- Crea requerimientos específicos por nivel + modalidad
- Usa los valores de la Minuta Patrón ICBF

### 3️⃣ Verificar los Datos

```python
python manage.py shell

>>> from nutricion.models import TablaRequerimientosNutricionales
>>> reqs = TablaRequerimientosNutricionales.objects.all()
>>> for req in reqs:
...     print(req)

# Debería mostrar algo como:
# Preescolar - CAJM/JT - 276.0 Kcal
# Preescolar - Almuerzo - 417.0 Kcal
# Primaria (primero, segundo y tercero) - CAJM/JT - 334.0 Kcal
# ... etc
```

---

## 🔍 Cambios en el Código

### 1. Modelo (`nutricion/models.py`)

```python
class TablaRequerimientosNutricionales(models.Model):
    # ... campos existentes ...

    # NUEVO CAMPO
    id_modalidad = models.ForeignKey(
        ModalidadesDeConsumo,
        on_delete=models.PROTECT,
        db_column='id_modalidad',
        verbose_name="Modalidad de Consumo",
        related_name='requerimientos_nutricionales',
        null=True,  # Permitir NULL para compatibilidad
        blank=True
    )

    class Meta:
        # CAMBIO: Ahora unique_together considera nivel + modalidad
        unique_together = [['id_nivel_escolar_uapa', 'id_modalidad']]
```

### 2. Servicio de Análisis (`nutricion/services/analisis_service.py`)

```python
@staticmethod
def obtener_analisis_completo(id_menu: int) -> Dict:
    menu = TablaMenus.objects.select_related('id_contrato', 'id_modalidad').get(id_menu=id_menu)

    # CAMBIO: Filtrar por modalidad del menú
    if menu.id_modalidad:
        requerimientos = TablaRequerimientosNutricionales.objects.filter(
            id_modalidad=menu.id_modalidad
        )
    else:
        # Fallback para compatibilidad
        requerimientos = TablaRequerimientosNutricionales.objects.filter(
            id_modalidad__isnull=True
        )
```

### 3. Frontend (sin cambios)

El frontend (`AnalisisNutricionalManager.js`) **NO requiere cambios** porque:
- Ya calcula porcentajes dinámicamente: `(total / requerimiento) * 100`
- Los rangos de semáforo (0-35%, 35-70%, >70%) siguen siendo los mismos
- Solo cambian los valores de referencia que vienen del backend

---

## 🎨 Rangos de Semaforización (sin cambios)

Los rangos de evaluación **permanecen iguales**:

| Estado | Rango | Color | Interpretación |
|--------|-------|-------|----------------|
| **ÓPTIMO** | 0-35% | 🟢 Verde | Aporte bajo pero seguro para la modalidad |
| **ACEPTABLE** | 35.1-70% | 🟡 Amarillo | Aporte moderado para la modalidad |
| **ALTO** | >70% | 🔴 Rojo | Aporte elevado, cerca del límite máximo para la modalidad |

**Diferencia**: Ahora el 100% es **específico para cada modalidad**, no el requerimiento diario total.

---

## ⚠️ Consideraciones Importantes

### Compatibilidad con Datos Existentes

1. **Menús sin modalidad asignada**: El sistema hace fallback a requerimientos sin modalidad
2. **Requerimientos antiguos**: Se eliminan automáticamente al ejecutar el script de población
3. **Análisis guardados**: Seguirán funcionando, pero se recalcularán con los nuevos requerimientos

### Requisitos Previos

Antes de ejecutar el script de población, asegúrate de que existan en la BD:

1. **Modalidades de Consumo** con códigos:
   - `CAJM/JT` o similar (jornada mañana/tarde)
   - `ALMUERZO` o similar

2. **Niveles Escolares UAPA**:
   - Preescolar
   - Primaria (primero, segundo y tercero)
   - Primaria (cuarto y quinto)
   - Secundaria
   - Nivel medio y ciclo complementario

Si los nombres son diferentes, ajusta el script `poblar_requerimientos_modalidad.py`.

---

## 🧪 Testing

### Pruebas Manuales

1. **Crear menú CAJM/JT** para Preescolar con ingredientes que sumen ~280 Kcal
   - **Esperado**: Porcentaje ~101% → 🔴 ALTO

2. **Crear menú Almuerzo** para Preescolar con los mismos ingredientes (~280 Kcal)
   - **Esperado**: Porcentaje ~67% → 🟡 ACEPTABLE

3. **Verificar colores** en el modal de análisis nutricional
   - Los badges deben reflejar correctamente el estado según la modalidad

### Pruebas Unitarias (recomendado crear)

```python
# tests/test_semaforizacion_modalidad.py
def test_requerimientos_por_modalidad():
    """Verifica que existan requerimientos por nivel + modalidad"""
    from nutricion.models import TablaRequerimientosNutricionales

    cajm = ModalidadesDeConsumo.objects.get(cod_modalidad__icontains='CAJM')
    preescolar = TablaGradosEscolaresUapa.objects.get(nivel_escolar_uapa__icontains='prescolar')

    req = TablaRequerimientosNutricionales.objects.get(
        id_nivel_escolar_uapa=preescolar,
        id_modalidad=cajm
    )

    assert req.calorias_kcal == 276
    assert req.proteina_g == 9.9
```

---

## 📝 Actualizar Documentación

No olvides actualizar `CLAUDE.md` con esta información:

```markdown
### Semaforización (Febrero 2025)

El sistema de semaforización considera:
- ✅ Nivel escolar (preescolar, primaria, secundaria, etc.)
- ✅ Modalidad de consumo (CAJM/JT, Almuerzo, etc.)
- ✅ Rangos uniformes (0-35%, 35-70%, >70%)

Los requerimientos nutricionales son específicos por nivel + modalidad,
basados en la Minuta Patrón ICBF (Resolución UAPA).
```

---

## 🐛 Troubleshooting

### Error: "Modalidad CAJM/JT no encontrada"

**Solución**: Ajusta los filtros en `poblar_requerimientos_modalidad.py`:

```python
# Línea ~130
modalidad_cajm = ModalidadesDeConsumo.objects.get(
    cod_modalidad__icontains='CAJM'  # Ajusta según tu BD
)
```

### Error: "Nivel escolar no encontrado en minuta patrón"

**Solución**: Verifica los nombres de niveles escolares en la BD y ajusta el mapeo en el script:

```python
# Línea ~155
if 'prescolar' in nivel_str or 'preescolar' in nivel_str:
    nivel_key = 'prescolar'
# ... ajusta según tus datos
```

### Error: "duplicate key value violates unique constraint"

**Solución**: Elimina requerimientos duplicados manualmente:

```python
python manage.py shell

>>> from nutricion.models import TablaRequerimientosNutricionales
>>> TablaRequerimientosNutricionales.objects.all().delete()
>>> # Luego ejecuta el script de población nuevamente
```

---

## 📚 Referencias

- **Minuta Patrón ICBF**: `nutricion/MINUTA_PATRON_RESOLUCION.md`
- **Modelo de Requerimientos**: `nutricion/models.py` (línea 277)
- **Servicio de Análisis**: `nutricion/services/analisis_service.py`
- **Script de Población**: `nutricion/poblar_requerimientos_modalidad.py`

---

## ✅ Checklist de Implementación

- [ ] Aplicar migración: `python manage.py migrate nutricion 0002`
- [ ] Verificar modalidades en BD (CAJM/JT, Almuerzo)
- [ ] Ejecutar script de población: `python manage.py shell < nutricion/poblar_requerimientos_modalidad.py`
- [ ] Verificar requerimientos creados: `TablaRequerimientosNutricionales.objects.count()` debe ser ~10
- [ ] Crear menú de prueba y verificar semaforización
- [ ] Actualizar `CLAUDE.md` con esta información
- [ ] Probar en diferentes modalidades y niveles escolares
- [ ] Documentar cualquier ajuste necesario según los datos de producción

---

**¿Preguntas o problemas?** Revisa la sección de Troubleshooting o consulta el código fuente de los archivos mencionados.
