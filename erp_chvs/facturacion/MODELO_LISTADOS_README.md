# Modelo ListadosFocalizacion - Documentación

## Descripción General

Se ha implementado una nueva tabla `listados_focalizacion` para persistir los datos procesados de los archivos Excel del Programa Alimentario Escolar (PAE). Esta implementación incluye un modelo Django completo con servicios de persistencia, vistas y templates.

## Estructura de la Tabla

### Tabla: `listados_focalizacion`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id_listados` | VARCHAR(50) | PK, NOT NULL, UNIQUE | ID único del listado |
| `ano` | INTEGER | NOT NULL, >= 2020 | Año del registro |
| `etc` | VARCHAR(100) | NOT NULL | Entidad Territorial (ETC) |
| `institucion` | VARCHAR(200) | NOT NULL | Institución Educativa |
| `sede` | VARCHAR(200) | NOT NULL | Sede Educativa |
| `tipodoc` | VARCHAR(10) | NOT NULL | Tipo de Documento |
| `doc` | VARCHAR(20) | NOT NULL | Número de Documento |
| `apellido1` | VARCHAR(100) | NULLABLE | Primer Apellido |
| `apellido2` | VARCHAR(100) | NULLABLE | Segundo Apellido |
| `nombre1` | VARCHAR(100) | NOT NULL | Primer Nombre |
| `nombre2` | VARCHAR(100) | NULLABLE | Segundo Nombre |
| `fecha_nacimiento` | VARCHAR(20) | NOT NULL | Fecha de Nacimiento |
| `edad` | INTEGER | NOT NULL, >= 0 | Edad calculada |
| `etnia` | VARCHAR(50) | NULLABLE | Etnia |
| `genero` | VARCHAR(10) | NOT NULL | Género |
| `grado_grupos` | VARCHAR(20) | NOT NULL | Grado y Grupos |
| `complemento_alimentario_preparado_am` | VARCHAR(10) | NULLABLE | Complemento AM |
| `complemento_alimentario_preparado_pm` | VARCHAR(10) | NULLABLE | Complemento PM |
| `almuerzo_jornada_unica` | VARCHAR(10) | NULLABLE | Almuerzo JU |
| `refuerzo_complemento_am_pm` | VARCHAR(10) | NULLABLE | Refuerzo |
| `focalizacion` | VARCHAR(10) | NOT NULL | Focalización |
| `fecha_creacion` | DATETIME | AUTO | Fecha de creación |
| `fecha_actualizacion` | DATETIME | AUTO | Fecha de actualización |

### Índices y Restricciones

**Índices:**
- `ano, etc` (compuesto)
- `focalizacion`
- `sede`
- `doc`
- `fecha_creacion`

**Restricciones:**
- Constraint único: `doc, ano, focalizacion`

## Archivos Implementados

### 1. Modelo Django
- **Archivo:** `facturacion/models.py`
- **Clase:** `ListadosFocalizacion`
- **Características:**
  - Validaciones con `MinValueValidator`
  - Métodos auxiliares: `get_nombre_completo()`, `tiene_complemento_alimentario()`
  - Property: `complementos_activos`

### 2. Panel de Administración
- **Archivo:** `facturacion/admin.py`
- **Clase:** `ListadosFocalizacionAdmin`
- **Características:**
  - Filtros por año, ETC, focalización, género
  - Búsqueda por ID, documento, nombres, apellidos
  - Acciones personalizadas: exportar Excel, marcar complementos
  - Visualización con colores para complementos

### 3. Servicio de Persistencia
- **Archivo:** `facturacion/persistence_service.py`
- **Clase:** `PersistenceService`
- **Métodos principales:**
  - `guardar_listados_focalizacion()`: Guarda en batch con manejo de duplicados
  - `verificar_duplicados()`: Verifica registros existentes
  - `obtener_estadisticas_bd()`: Estadísticas generales
  - `_generar_id_listado()`: Genera IDs únicos

### 4. Servicios Actualizados
- **Archivo:** `facturacion/services.py`
- **Método agregado:** `procesar_y_guardar_excel()`
- **Funcionalidad:** Procesa archivo y guarda automáticamente en BD

### 5. Vistas Nuevas
- **Archivo:** `facturacion/views.py`
- **Vistas agregadas:**
  - `procesar_y_guardar_view()`: Vista principal con persistencia
  - `obtener_estadisticas_bd()`: AJAX para estadísticas de BD

### 6. URLs Actualizadas
- **Archivo:** `facturacion/urls.py`
- **Rutas agregadas:**
  - `/procesar-y-guardar/`: Vista principal con persistencia
  - `/estadisticas-bd/`: AJAX para estadísticas

### 7. Templates
- **Archivo:** `templates/facturacion/procesar_y_guardar.html`
- **Características:**
  - Estadísticas en tiempo real de la BD
  - Formulario con opción de activar/desactivar guardado
  - Indicadores visuales de persistencia
  - Información detallada de resultados

### 8. Migración
- **Archivo:** `facturacion/migrations/0001_initial.py`
- **Contenido:** Creación de tabla con todos los campos, índices y restricciones

## Características Principales

### 1. Generación de IDs Únicos
```python
def _generar_id_listado(row: pd.Series) -> str:
    # Estrategia: año + ETC + documento + focalizacion + timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # ... lógica completa
```

### 2. Inserción en Batch Optimizada
```python
def _insertar_en_batch(registros: List[ListadosFocalizacion], batch_size: int = 1000):
    # Usa bulk_create con ignore_conflicts para manejar duplicados
    ListadosFocalizacion.objects.bulk_create(
        lote, ignore_conflicts=True, batch_size=batch_size
    )
```

### 3. Cálculo Automático de Edad
```python
def _calcular_edad(fecha_nacimiento, edad_existente) -> int:
    # Calcula edad desde fecha de nacimiento o usa existente
    # Maneja múltiples formatos de fecha
```

### 4. Manejo de Duplicados
- **Constraint único:** `doc + ano + focalizacion`
- **Estrategia:** `ignore_conflicts=True` en bulk_create
- **Logging:** Registro detallado de duplicados encontrados

## Flujo de Trabajo

1. **Usuario sube archivo Excel** → Vista `procesar_y_guardar_view`
2. **Procesamiento** → Servicio `procesar_y_guardar_excel`
3. **Validación** → Validaciones existentes de sedes y datos
4. **Transformación** → Aplicación de mapeos y lógica de negocio
5. **Persistencia** → `PersistenceService.guardar_listados_focalizacion`
6. **Resultado** → Template con estadísticas e información de guardado

## Comandos de Instalación

```bash
# 1. Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# 2. Generar migraciones
python manage.py makemigrations facturacion

# 3. Aplicar migraciones
python manage.py migrate

# 4. Crear superusuario (si no existe)
python manage.py createsuperuser

# 5. Ejecutar servidor
python manage.py runserver
```

## URLs Disponibles

- `/facturacion/` - Dashboard principal
- `/facturacion/generar-listados/` - Procesamiento solo
- `/facturacion/procesar-y-guardar/` - Procesamiento con persistencia
- `/facturacion/estadisticas-bd/` - AJAX estadísticas BD
- `/admin/facturacion/listadosfocalizacion/` - Panel de administración

## Características de Seguridad

1. **Validación de archivos**: Tipo MIME y extensión
2. **Transacciones atómicas**: Rollback automático en errores
3. **Logging completo**: Registro de todas las operaciones
4. **Manejo de excepciones**: Captura y manejo robusto de errores
5. **Sanitización de datos**: Limpieza automática de campos string

## Rendimiento

- **Inserción en batch**: 1000 registros por lote (configurable)
- **Índices optimizados**: Para consultas frecuentes
- **Ignore conflicts**: Manejo eficiente de duplicados
- **Select related**: Optimización de consultas en admin

## Extensiones Futuras

1. **Exportación Excel**: Implementar en acción de admin
2. **API REST**: Para integración con sistemas externos
3. **Dashboard analytics**: Visualizaciones avanzadas
4. **Validaciones adicionales**: Reglas de negocio específicas
5. **Histórico de versiones**: Tracking de cambios en registros