# Integración Formato Anexo 6A SIMAT — Estado y Pendientes

## Contexto

El Anexo 6A es un reporte exportado directamente desde el sistema SIMAT del MEN (Ministerio de Educación Nacional). Contiene la nómina completa de estudiantes matriculados por sede educativa. En ocasiones se debe usar como fuente de focalización PAE en lugar del archivo habitual (formato original BUGA/YUMBO).

**Fecha de análisis inicial:** 2026-04-21  
**Archivo de referencia:** `anexo 6a abril.xlsx` (13.884 filas × 62 columnas, municipio 892 = **YUMBO**)

---

## Diferencias clave con el formato habitual

| Aspecto | Formato habitual (original) | Anexo 6A SIMAT |
|---|---|---|
| Identificación de sede | Nombre de texto (`SEDE`) | Código numérico `CONS_SEDE` (14 dígitos) |
| Identificación de IE | Nombre de texto (`INSTITUCION`) | Código numérico `CODIGO_DANE` (12 dígitos) |
| Municipio | Nombre de texto (`ETC`) | Código numérico `MUN_CODIGO` (ej: 892) |
| Jornada | Texto (`ÚNICA`, `MAÑANA`, `TARDE`) | Entero SIMAT (2, 3, 6) |
| Grado | Texto (`GRADO_COD`) | Entero SIMAT (-2, -1, 0, 1-11, 21-26, 99) |
| Tipo de documento | Texto | Entero SIMAT (1=RC, 2=TI, 3=CC…) |
| Complemento alimentario | Columnas explícitas | No existe → se deriva de la jornada |
| Filtro de matrícula | Columnas `ESTADO`/`SECTOR` | Filtro por `TIPO_JORNADA` ∈ {2, 3, 6} |

---

## Columnas clave del Anexo 6A

| Columna | Tipo | Descripción |
|---|---|---|
| `ANO_INF` | int64 | Año del informe |
| `MUN_CODIGO` | int64 | Código SIMAT del municipio (892 = BUGA) |
| `CODIGO_DANE` | int64 | Código SIMAT de la IE (12 dígitos) |
| `DANE_ANTERIOR` | int64 | Código SIMAT anterior (mismo sistema, 12 dígitos) |
| `CONS_SEDE` | int64 | Código SIMAT de la sede (14 dígitos) |
| `ZONA` | object | `'URBANA'` / `'RURAL'` |
| `TIPO_DOCUMENTO` | int64 | Código de tipo de documento (1=RC, 2=TI, 3=CC, 5=PA, 8=NUI, 11=PEP, 13=PPT) |
| `NRO_DOCUMENTO` | object | Número de documento (único por fila) |
| `APELLIDO1/2` | object | Apellidos — APELLIDO2 tiene 76 nulos |
| ` NOMBRE1` | object | **Tiene espacio al inicio** — se limpia con `.strip()` |
| `NOMBRE2` | object | Segundo nombre — 3.807 nulos |
| `FECHA_NACIMIENTO` | datetime64 | Sin nulos |
| `GENERO` | object | `'F'` / `'M'` |
| `GRADO` | int64 | Código numérico SIMAT (ver mapeo abajo) |
| `GRUPO` | int64 | Código numérico (ej: 2401 = grado 24, grupo 01) |
| `TIPO_JORNADA` | int64 | 2=Mañana, 3=Tarde, 6=Única. **4 y 5 no son PAE** |
| `ETNIA` | int64 | 0 = sin etnia |
| `SISBEN IV` | object | Categorías A1-D21 + `'NO APLICA'` — 477 nulos |
| `CAMPESINO` | object | 86% nulos |
| `PAIS_NACIMIENTO` | float64 | 86% nulos |
| `CATEGORIA_AULA` | float64 | 99.5% nulos |

**Columnas completamente vacías:** `PROVIENE_OTR_MUN`, `CODIGO_VALORACION_1`, `CODIGO_VALORACION_2`, `NUM_CONVENIO`

---

## Mapeo de códigos SIMAT

### TIPO_JORNADA → complemento PAE

| Código | Jornada | BUGA | YUMBO |
|---|---|---|---|
| 2 | MAÑANA | CAP AM | CAP AM + REFUERZO |
| 3 | TARDE | CAP AM | CAP AM + REFUERZO |
| 6 | ÚNICA | CAP AM + ALMUERZO JU | CAP AM + ALMUERZO JU |
| 4, 5 | No PAE | Se excluyen del procesamiento | Se excluyen del procesamiento |

### GRADO SIMAT → nivel educativo

| Códigos | Nivel |
|---|---|
| -2, -1 | `prescolar` |
| 0 | `prescolar` |
| 1-3 | `primaria_1_2_3` |
| 4-5 | `primaria_4_5` |
| 6-9 | `secundaria` |
| 10-11 | `media_ciclo_complementario` |
| 21-26 | `media_ciclo_complementario` (ciclo complementario adultos) |
| 99 | `prescolar` |

### MUN_CODIGO → ETC (nombre interno del sistema)

| Código SIMAT | ETC |
|---|---|
| 892 | `YUMBO` |
| (pendiente) | `GUADALAJARA DE BUGA` — confirmar código cuando se tenga archivo de BUGA |

---

## Lo que se implementó (2026-04-21)

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `config.py` | Constantes: `TIPO_PROCESAMIENTO_SIMAT_6A`, `COLUMNAS_FIRMA_SIMAT_6A`, `COLUMNAS_SIMAT_6A` (incluye `DANE_ANTERIOR`), `MAPEO_MUNICIPIO_CODIGO`, `MAPEO_TIPO_JORNADA_SIMAT`, `JORNADAS_PAE_SIMAT`, `FALLBACK_NIVEL_GRADO_SIMAT` |
| `excel_utils.py` | Método `ExcelProcessor.validar_estructura_simat_6a()` |
| `data_processors.py` | Método `DataTransformer.procesar_formato_simat_6a()` — matching por `DANE_ANTERIOR` → `cod_dane` BD + fallback para grados SIMAT en `_procesar_grados_escolares()` |
| `services.py` | Método `ProcesamientoService.procesar_excel_simat_6a()` |
| `views.py` | Auto-detección por firma de columnas + rama para `simat_6a` en Etapa 1 |

### Cómo funciona la auto-detección

En `views.py` Etapa 1, antes de llamar al service, se hace un peek de las columnas:

```python
df_peek = pd.read_excel(archivo, nrows=0)
cols_peek = set(df_peek.columns.str.strip().str.upper())
if ProcesamientoConfig.COLUMNAS_FIRMA_SIMAT_6A.issubset(cols_peek):
    tipo_procesamiento = ProcesamientoConfig.TIPO_PROCESAMIENTO_SIMAT_6A
```

`COLUMNAS_FIRMA_SIMAT_6A = {'ANO_INF', 'MUN_CODIGO', 'CODIGO_DANE', 'CONS_SEDE'}`

### Columna de matching: `DANE_ANTERIOR`

El matching de sedes usa `DANE_ANTERIOR` (código sede física, coincide con `SedesEducativas.cod_dane`).  
**No** se usa `CONS_SEDE` (código SIMAT interno, no existe en BD) ni `CODIGO_DANE` (código IE, baja granularidad).

Si el archivo NO tiene estas 4 columnas, el flujo sigue siendo el habitual sin ningún cambio.

---

## Estado del matching — YUMBO ✅ FUNCIONANDO

### Cómo funciona el matching para YUMBO

El matching se hace usando **`DANE_ANTERIOR`** del archivo contra **`SedesEducativas.cod_dane`** en la BD.

**Verificación empírica realizada (2026-04-21) con archivo de YUMBO (MUN_CODIGO=892):**

| Columna del archivo | Nivel | Únicos | Coincidencias en BD |
|---|---|---|---|
| `CONS_SEDE` (14 dígitos) | Sede física | 43 | 0 de 43 ❌ |
| `CODIGO_DANE` (12 dígitos) | IE (institución) | 13 | 13 de 13 ✅ |
| `DANE_ANTERIOR` (12-14 dígitos) | Sede física | 43 | **42 de 43 ✅** |

**Por qué `DANE_ANTERIOR` y no `CODIGO_DANE` ni `CONS_SEDE`:**
- `DANE_ANTERIOR` = código de sede física que coincide con `cod_dane` en BD (resolución a nivel de sede, no IE).
- `CODIGO_DANE` agrupa todas las sedes físicas de una IE bajo un único registro → baja granularidad.
- `CONS_SEDE` = código SIMAT interno de 14 dígitos; la BD no lo almacena en ningún campo.
- La única sede no encontrada por `DANE_ANTERIOR` es `276892000404` (~37 estudiantes excluidos).

**Resultado del procesamiento completo (con DANE_ANTERIOR):**
- 13.484 filas procesadas (de 13.884 — se excluyen jornadas 4 y 5 + 1 sede sin match)
- 1 sede inválida: `276892000404` (no existe en BD)
- 39 sedes físicas resueltas
- ETC = 'YUMBO' correctamente derivado de MUN_CODIGO=892
- Complementos YUMBO aplicados: CAP AM (13.484) + REFUERZO (10.096 jornadas 2/3) + ALMUERZO JU (3.388 jornada 6)
- Niveles educativos: todos mapeados sin nulos

## Pendiente: BUGA

Cuando se tenga un Anexo 6A de BUGA se debe verificar:
1. ¿Cuál es el `MUN_CODIGO` de BUGA en SIMAT? (probablemente distinto de 892)
2. ¿El `CODIGO_DANE` del archivo de BUGA coincide con `cod_dane` de BUGA en BD?
3. Si no coincide, agregar el código de BUGA a `MAPEO_MUNICIPIO_CODIGO` en `config.py` y evaluar estrategia de matching.

Si para BUGA el `CODIGO_DANE` del archivo NO coincide con `cod_dane` en BD, la solución sería agregar un campo `cod_simat` a `SedesEducativas` y poblarlo manualmente.

---

## Estado funcional actual

| Escenario | Estado |
|---|---|
| Carga habitual BUGA (formato original) | ✅ Funciona sin cambios |
| Carga habitual YUMBO (formato original) | ✅ Funciona sin cambios |
| Carga habitual CALI (LOTE==3) | ✅ Funciona sin cambios |
| Carga Anexo 6A SIMAT — auto-detección | ✅ Detecta correctamente el formato |
| Carga Anexo 6A SIMAT — transformaciones | ✅ Normaliza columnas, filtra jornadas, mapea jornada/grado/ETC |
| Carga Anexo 6A SIMAT — matching sedes YUMBO | ✅ Funciona: `CODIGO_DANE` archivo = `cod_dane` BD |
| Carga Anexo 6A SIMAT — matching sedes BUGA | ⚠️ Pendiente: verificar cuando se tenga archivo de BUGA |
| PDFs, ZIPs, transferencia de grados, rectores | ✅ Sin cambios |

---

## Notas adicionales para sesiones futuras

- El campo `NOMBRE1` en el Anexo 6A tiene un **espacio al inicio** en el header. Esto se corrige automáticamente con `.str.strip()` en el procesador.
- `TIPODOC` se almacena como string numérico (ej: `"3"` para CC). No pasa por el mapeo de `TipoDocumento` porque SIMAT usa códigos enteros, no textos descriptivos. Considerar crear un mapeo en `config.py` si se requiere normalizar.
- `GENERO` ya viene como `F`/`M`, compatible con el modelo sin transformación adicional.
- `ETNIA` con valor `0` se normaliza a `None` (sin etnia).
- Los grados SIMAT `-2`, `-1`, `21-26`, `99` no están en `NivelGradoEscolar` de la BD — se usa el dict `FALLBACK_NIVEL_GRADO_SIMAT` en `config.py` como respaldo.
- Jornadas 4 y 5 del SIMAT no pertenecen al PAE y se excluyen antes del procesamiento.
