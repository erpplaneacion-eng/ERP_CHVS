# Módulo de Facturación

## Descripción General

El módulo de **Facturación** es responsable de procesar, validar y almacenar los listados de focalización del Programa de Alimentación Escolar (PAE). Originalmente un archivo monolítico, ha sido refactorizado a una **arquitectura orientada a servicios (SOA)** para mejorar la mantenibilidad, escalabilidad y testabilidad del código.

La lógica principal se divide en capas, donde cada archivo tiene una responsabilidad única y bien definida.

## Estructura de Archivos

```
facturacion/
├── admin.py                # Configuración del panel de administración de Django.
├── apps.py                 # Configuración de la aplicación.
├── config.py               # Constantes y configuraciones del módulo.
├── data_processors.py      # Lógica para transformar y limpiar datos.
├── excel_utils.py          # Utilidades para leer y validar archivos Excel.
├── exceptions.py           # Excepciones personalizadas para un manejo de errores claro.
├── fuzzy_matching.py       # Algoritmos para coincidencia difusa de nombres (ej. sedes).
├── logging_config.py       # Configuración centralizada del sistema de logging.
├── models.py               # Definición de los modelos de la base de datos (ORM de Django).
├── persistence_service.py  # Capa de acceso a datos (interactúa con models.py).
├── services.py             # Orquestador principal de la lógica de negocio.
├── urls.py                 # Definición de las rutas (URLs) del módulo.
├── validators.py           # Reglas de validación de datos.
├── views.py                # Controladores que manejan las peticiones HTTP y respuestas.
├── migrations/             # Migraciones de la base de datos.
├── static/
│   └── css/modules/
│       └── facturacion.css # Estilos CSS específicos para este módulo.
└── templates/
    └── facturacion/        # Plantillas HTML para las vistas.
        ├── index.html
        ├── lista_listados.html
        └── procesar_listados.html
```

---

## Detalle de Componentes

### Archivos Estándar de Django

#### `models.py`
- **Rol**: **Capa de Datos (Definición)**.
- **Descripción**: Define la estructura de la base de datos a través de clases de Python (Modelos). Aquí se encuentra el modelo `ListadosFocalizacion`, que representa la tabla donde se almacenan los registros procesados. Define campos, tipos de datos, longitudes máximas y relaciones.

#### `views.py`
- **Rol**: **Capa de Presentación (Controlador)**.
- **Descripción**: Actúa como el intermediario entre el usuario y la aplicación. Sus responsabilidades son:
  1.  Recibir las peticiones HTTP (GET, POST).
  2.  Llamar a los servicios (`ProcesamientoService`, `PersistenceService`) para ejecutar la lógica de negocio. No contiene lógica de negocio compleja.
  3.  Manejar la sesión del usuario para flujos de varios pasos (como el procesamiento en dos etapas).
  4.  Renderizar las plantillas HTML (`templates`) con el contexto adecuado o devolver respuestas JSON para peticiones AJAX.
- **Ejemplo clave**: `procesar_listados_view` orquesta el flujo de carga, validación y guardado en dos etapas.

#### `urls.py`
- **Rol**: **Enrutador**.
- **Descripción**: Mapea las URLs a las vistas correspondientes en `views.py`. Define los endpoints a los que los usuarios pueden acceder, como `/facturacion/procesar/` o `/facturacion/api/listados/`.

#### `admin.py`
- **Rol**: **Interfaz de Administración**.
- **Descripción**: Registra los modelos de `models.py` en el panel de administración de Django. Esto permite a los administradores del sistema ver, crear, editar y eliminar registros de la base de datos a través de una interfaz web autogenerada y segura.

### Capa de Servicios (Lógica de Negocio)

#### `services.py`
- **Rol**: **Orquestador de Lógica de Negocio**.
- **Descripción**: Es el cerebro de la aplicación. Las vistas llaman a los servicios definidos aquí para realizar tareas complejas. El `ProcesamientoService` coordina a los demás componentes (`ExcelProcessor`, `DataTransformer`, `FuzzyMatcher`, `PersistenceService`) para ejecutar el flujo completo de procesamiento de un archivo. Desacopla la lógica de negocio de la capa de presentación.

#### `persistence_service.py`
- **Rol**: **Capa de Persistencia**.
- **Descripción**: Es el único componente que debe comunicarse directamente con la base de datos para escribir o modificar datos. Abstrae toda la lógica de guardado, como:
  - Creación de objetos del modelo.
  - Inserciones masivas (`bulk_create`) para un alto rendimiento.
  - Manejo de transacciones atómicas para garantizar la integridad de los datos.
  - Lógica de fallback para guardar registros uno por uno si una inserción masiva falla.
  - Generación de IDs únicos.

#### `excel_utils.py`
- **Rol**: **Utilidad de Archivos**.
- **Descripción**: Contiene toda la lógica relacionada con la manipulación de archivos Excel. Sus responsabilidades incluyen:
  - Validar si un archivo es un Excel válido (`.xls`, `.xlsx`).
  - Leer el contenido del archivo y cargarlo en un DataFrame de Pandas.
  - Verificar que el archivo tenga la estructura esperada (columnas requeridas).

#### `data_processors.py`
- **Rol**: **Transformador de Datos**.
- **Descripción**: Se encarga de la limpieza, normalización y transformación de los datos una vez leídos del Excel. Por ejemplo:
  - Aplicar mapeos (ej. "M" -> "Masculino").
  - Calcular nuevos campos (ej. `edad` a partir de `fecha_nacimiento`).
  - Adaptar los datos de diferentes formatos de archivo a una estructura común.

#### `fuzzy_matching.py`
- **Rol**: **Utilidad de Coincidencia Difusa**.
- **Descripción**: Contiene algoritmos especializados para comparar cadenas de texto que no son exactamente iguales. Su uso principal es validar los nombres de las sedes educativas del archivo Excel contra los nombres oficiales en la base de datos, permitiendo pequeñas variaciones o errores de tipeo.

#### `validators.py`
- **Rol**: **Validador de Reglas de Negocio**.
- **Descripción**: Centraliza las reglas de validación de los datos. Por ejemplo, verifica que un campo numérico contenga solo números, que una fecha tenga el formato correcto o que un valor se encuentre dentro de una lista permitida.

### Configuración y Soporte

#### `config.py`
- **Rol**: **Configuración Centralizada**.
- **Descripción**: Almacena constantes, umbrales, nombres de columnas y mensajes de texto en un solo lugar. Evita tener valores "mágicos" (hardcodeados) dispersos por el código, facilitando el mantenimiento y la configuración.

#### `exceptions.py`
- **Rol**: **Manejo de Errores Personalizado**.
- **Descripción**: Define clases de excepción propias del dominio de la aplicación (ej. `ArchivoInvalidoException`, `ColumnasFaltantesException`). Esto permite un manejo de errores más específico y claro en lugar de usar excepciones genéricas de Python.

#### `logging_config.py`
- **Rol**: **Sistema de Registro (Logging)**.
- **Descripción**: Configura un logger específico para el módulo de facturación. Permite registrar eventos importantes, advertencias y errores en un formato estructurado, lo cual es fundamental para la depuración y el monitoreo de la aplicación en producción.

### Frontend

#### `templates/facturacion/`
- **Rol**: **Capa de Presentación (Vista)**.
- **Descripción**: Son los archivos HTML que definen la interfaz de usuario. Usan el sistema de plantillas de Django para mostrar dinámicamente los datos enviados desde `views.py`.
- **Ejemplo clave**: `procesar_listados.html` implementa la interfaz para el flujo de dos etapas, mostrando los resultados de la validación y el botón para guardar.

#### `static/css/modules/facturacion.css`
- **Rol**: **Estilos Visuales**.
- **Descripción**: Contiene las reglas de CSS que aplican estilo exclusivamente a las páginas del módulo de facturación. Esto mantiene los estilos organizados y evita conflictos con otros módulos de la aplicación.

---

## Flujo de Trabajo Típico (Procesar un Archivo)

1.  **Usuario**: Sube un archivo Excel a través de la interfaz en `procesar_listados.html`.
2.  **`views.py`**: Recibe la petición y llama a `ProcesamientoService.procesar_excel_...()`.
3.  **`services.py`**: Orquesta el proceso:
    a.  Usa `excel_utils.py` para leer y validar el archivo.
    b.  Usa `data_processors.py` para limpiar y transformar los datos.
    c.  Usa `fuzzy_matching.py` para validar las sedes.
    d.  Devuelve los datos procesados y las estadísticas a la vista.
4.  **`views.py`**: Renderiza de nuevo `procesar_listados.html` mostrando los datos para que el usuario los verifique (Etapa 1).
5.  **Usuario**: Hace clic en "Guardar en Base de Datos".
6.  **`views.py`**: Recibe la nueva petición y esta vez llama a `PersistenceService.guardar_listados_focalizacion()`.
7.  **`persistence_service.py`**: Toma el DataFrame, lo convierte en objetos del modelo `ListadosFocalizacion` y los guarda en la base de datos de manera eficiente.
8.  **`views.py`**: Muestra un mensaje de éxito al usuario (Etapa 2).

```


