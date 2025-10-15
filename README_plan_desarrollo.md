# Plan de Desarrollo: Reporte Maestro de Análisis Nutricional por Modalidad

## 1. Objetivo

El objetivo de este plan es desarrollar una nueva funcionalidad que permita generar un reporte consolidado en formato Excel para una modalidad de atención completa dentro de un contrato específico. Este "reporte maestro" agrupará los análisis nutricionales de todos los menús de una modalidad en un único archivo, facilitando una visión global y reduciendo la necesidad de descargas individuales.

El reporte será accesible a través de un nuevo botón de descarga ubicado en la interfaz de gestión de menús.

---

## 2. Estructura del Reporte Final

El archivo Excel generado tendrá las siguientes características:

- **Archivo Único:** Se generará un solo archivo `.xlsx` por cada modalidad.
- **Múltiples Pestañas:** El archivo contendrá una pestaña por cada **Nivel Escolar** configurado en el sistema (ej. 5 pestañas).
- **Contenido por Pestaña:** Cada pestaña contendrá el análisis nutricional completo de los **20 menús** pertenecientes a la modalidad, calculados específicamente para el nivel escolar de esa pestaña.
- **Diseño Consistente:**
    - Los 20 análisis se apilarán verticalmente, uno debajo del otro.
    - Se insertará un **salto de página** entre cada análisis para asegurar una impresión limpia y ordenada.
    - Cada análisis individual mantendrá la **misma estructura y diseño** del reporte que ya existe, incluyendo el logo del contrato en la esquina superior izquierda y el título "ANÁLISIS NUTRICIONAL" a su derecha.

---

## 3. Plan de Implementación

El desarrollo se dividirá en tres fases principales para asegurar un proceso modular y ordenado.

### Fase 1: Backend - El Motor de Datos y Generación

Esta fase se centra en crear la lógica para reunir los datos y construir el archivo Excel.

#### 1.1. Nuevo Servicio de "Análisis Maestro"
- **Archivo a modificar:** `erp_chvs/nutricion/services/analisis_service.py`
- **Acción:** Crear una nueva función `obtener_analisis_masivo_por_modalidad(programa_id, modalidad_id)`.
- **Lógica:** Esta función orquestará la recolección de datos. Iterará sobre los 20 menús de la modalidad y, para cada uno, ejecutará el análisis nutricional completo para todos los niveles escolares. Devolverá una estructura de datos grande y anidada, lista para ser consumida por el generador de Excel.

#### 1.2. Refactorización de la Lógica de Dibujo de Excel
- **Nuevo Archivo:** `erp_chvs/nutricion/excel_drawing_utils.py`
- **Acción:** Para evitar la duplicación de código y mantener los archivos manejables, se creará este nuevo archivo de utilidades.
- **Lógica:** Se moverán las funciones y clases genéricas para "dibujar" un análisis individual (estilos, cabeceras, filas de ingredientes, etc.) desde `excel_generator.py` a este nuevo archivo.

#### 1.3. Creación del Nuevo "Generador Maestro"
- **Nuevo Archivo:** `erp_chvs/nutricion/master_excel_generator.py`
- **Acción:** Crear la clase `MasterNutritionalExcelGenerator`.
- **Lógica:** Esta clase importará las utilidades de `excel_drawing_utils.py`. Su responsabilidad será:
    1. Recibir los datos masivos del servicio maestro (Paso 1.1).
    2. Crear el libro de Excel y las pestañas por nivel escolar.
    3. Iterar sobre los datos y usar las utilidades de dibujo para renderizar cada uno de los 20 análisis en la pestaña correspondiente, controlando la posición de las filas y los saltos de página.

#### 1.4. Simplificación del Generador Original
- **Archivo a modificar:** `erp_chvs/nutricion/excel_generator.py`
- **Acción:** Se refactorizará la clase `NutritionalAnalysisExcelGenerator` para que también consuma las utilidades del nuevo archivo `excel_drawing_utils.py`. Esto reducirá su tamaño y centralizará la lógica de dibujo.

### Fase 2: Backend - El Punto de Acceso (API)

Esta fase expone la nueva funcionalidad a través de una URL.

#### 2.1. Nueva URL de Descarga
- **Archivo a modificar:** `erp_chvs/nutricion/urls.py`
- **Acción:** Añadir una nueva ruta para la descarga del reporte maestro. Ejemplo: `path('exportar-modalidad-excel/<int:programa_id>/<int:modalidad_id>/', ...)`.

#### 2.2. Nueva Vista de Descarga
- **Archivo a modificar:** `erp_chvs/nutricion/views.py`
- **Acción:** Crear la función `download_modalidad_excel` que será llamada por la nueva URL.
- **Lógica:** La vista recibirá los IDs del programa y la modalidad, llamará al servicio (1.1) y al generador maestro (1.3), y devolverá el archivo Excel resultante en un `HttpResponse` para que el usuario pueda descargarlo.

### Fase 3: Frontend - La Interfaz de Usuario

Esta fase conecta la nueva funcionalidad con la interfaz que el usuario ve.

#### 3.1. Modificación del Script del Frontend
- **Archivo a modificar:** `erp_chvs/static/js/nutricion/menus_avanzado.js`
- **Acción:** Localizar el código que construye dinámicamente el acordeón de modalidades.
- **Lógica:** Inyectar un nuevo botón (ej. "Descargar Excel Modalidad") en la cabecera de cada panel del acordeón. El enlace (`href`) de este botón apuntará a la nueva URL de descarga (2.1), pasando los IDs del programa y la modalidad correspondientes a ese panel.
