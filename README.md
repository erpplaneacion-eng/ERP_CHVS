# Documentación de la Base de Datos - ERP_CHVS

Este documento detalla la estructura de la base de datos del proyecto ERP_CHVS, organizada por módulos (aplicaciones de Django).

## Módulo: `facturacion`

### Tabla: `listados_focalizacion` (`ListadosFocalizacion`)

Almacena los listados de focalización procesados.

| Columna                                | Tipo de Dato        | Descripción                               |
| -------------------------------------- | ------------------- | ----------------------------------------- |
| `id_listados` (PK)                     | `CharField(50)`     | ID único del listado.                     |
| `ano`                                  | `IntegerField`      | Año del listado.                          |
| `etc`                                  | `CharField(100)`    | Entidad Territorial Certificada.          |
| `institucion`                          | `CharField(200)`    | Institución Educativa.                    |
| `sede`                                 | `CharField(200)`    | Sede Educativa.                           |
| `tipodoc`                              | `CharField(10)`     | Tipo de Documento del titular.            |
| `doc`                                  | `CharField(50)`     | Número de Documento del titular.          |
| `apellido1`                            | `CharField(100)`    | Primer Apellido.                          |
| `apellido2`                            | `CharField(100)`    | Segundo Apellido.                         |
| `nombre1`                              | `CharField(100)`    | Primer Nombre.                            |
| `nombre2`                              | `CharField(100)`    | Segundo Nombre.                           |
| `fecha_nacimiento`                     | `CharField(20)`     | Fecha de Nacimiento.                      |
| `edad`                                 | `IntegerField`      | Edad del titular.                         |
| `etnia`                                | `CharField(50)`     | Etnia del titular.                        |
| `genero`                               | `CharField(10)`     | Género del titular.                       |
| `grado_grupos`                         | `CharField(20)`     | Grado y grupo del titular.                |
| `complemento_alimentario_preparado_am` | `CharField(10)`     | Indica si recibe complemento AM.          |
| `complemento_alimentario_preparado_pm` | `CharField(10)`     | Indica si recibe complemento PM.          |
| `almuerzo_jornada_unica`               | `CharField(10)`     | Indica si recibe almuerzo en jornada única. |
| `refuerzo_complemento_am_pm`           | `CharField(10)`     | Indica si recibe refuerzo.                |
| `focalizacion`                         | `CharField(10)`     | Tipo de focalización.                     |
| `fecha_creacion`                       | `DateTimeField`     | Fecha de creación del registro.           |
| `fecha_actualizacion`                  | `DateTimeField`     | Fecha de última actualización.            |

---

## Módulo: `nutricion`

### Tabla: `TABLA_ALIMENTOS_2018_ICBF` (`TablaAlimentos2018Icbf`)

Tabla de composición nutricional de alimentos según ICBF 2018.

| Columna                      | Tipo de Dato         | Descripción                                  |
| ---------------------------- | -------------------- | -------------------------------------------- |
| `codigo` (PK)                | `CharField(20)`      | Código del alimento.                         |
| `nombre_del_alimento`        | `CharField(200)`     | Nombre del alimento.                         |
| `parte_analizada`            | `CharField(100)`     | Parte del alimento que fue analizada.        |
| `humedad_g`                  | `DecimalField(10, 2)`| Gramos de Humedad.                           |
| `energia_kcal`               | `IntegerField`       | Energía en Kilocalorías.                     |
| `energia_kj`                 | `IntegerField`       | Energía en Kilojulios.                       |
| `proteina_g`                 | `DecimalField(10, 2)`| Gramos de Proteína.                          |
| `lipidos_g`                  | `DecimalField(10, 2)`| Gramos de Lípidos.                           |
| `carbohidratos_totales_g`    | `DecimalField(10, 2)`| Gramos de Carbohidratos Totales.             |
| `carbohidratos_disponibles_g`| `DecimalField(10, 2)`| Gramos de Carbohidratos Disponibles.         |
| `fibra_dietaria_g`           | `DecimalField(10, 2)`| Gramos de Fibra Dietaria.                    |
| `cenizas_g`                  | `DecimalField(10, 2)`| Gramos de Cenizas.                           |
| `calcio_mg`                  | `IntegerField`       | Miligramos de Calcio.                        |
| `hierro_mg`                  | `DecimalField(10, 2)`| Miligramos de Hierro.                        |
| `sodio_mg`                   | `IntegerField`       | Miligramos de Sodio.                         |
| `fosforo_mg`                 | `IntegerField`       | Miligramos de Fósforo.                       |
| `yodo_mg`                    | `DecimalField(10, 2)`| Miligramos de Yodo.                          |
| `zinc_mg`                    | `DecimalField(10, 2)`| Miligramos de Zinc.                          |
| `magnesio_mg`                | `IntegerField`       | Miligramos de Magnesio.                      |
| `potasio_mg`                 | `IntegerField`       | Miligramos de Potasio.                       |
| `tiamina_mg`                 | `DecimalField(10, 2)`| Miligramos de Tiamina.                       |
| `riboflavina_mg`             | `DecimalField(10, 2)`| Miligramos de Riboflavina.                   |
| `niacina_mg`                 | `DecimalField(10, 2)`| Miligramos de Niacina.                       |
| `folatos_mcg`                | `DecimalField(10, 2)`| Microgramos de Folatos.                      |
| `vitamina_b12_mcg`           | `DecimalField(10, 2)`| Microgramos de Vitamina B12.                 |
| `vitamina_c_mg`              | `IntegerField`       | Miligramos de Vitamina C.                    |
| `vitamina_a_er`              | `IntegerField`       | Microgramos de Retinol de Vitamina A.        |
| `grasa_saturada_g`           | `DecimalField(10, 2)`| Gramos de Grasa Saturada.                    |
| `grasa_monoinsaturada_g`     | `DecimalField(10, 2)`| Gramos de Grasa Monoinsaturada.              |
| `grasa_poliinsaturada_g`     | `DecimalField(10, 2)`| Gramos de Grasa Poliinsaturada.              |
| `colesterol_mg`              | `IntegerField`       | Miligramos de Colesterol.                    |
| `parte_comestible_field`     | `IntegerField`       | Porcentaje de la parte comestible.           |

### Tabla: `tabla_menus` (`TablaMenus`)

Gestiona los menús del programa de alimentación.

| Columna               | Tipo de Dato         | Descripción                                      |
| --------------------- | -------------------- | ------------------------------------------------ |
| `id_menu` (PK)        | `AutoField`          | ID único del menú.                               |
| `menu`                | `CharField(255)`     | Nombre del menú.                                 |
| `id_modalidad` (FK)   | `ForeignKey`         | Referencia a `ModalidadesDeConsumo`.             |
| `id_contrato` (FK)    | `ForeignKey`         | Referencia a `planeacion.Programa`.              |
| `fecha_creacion`      | `DateTimeField`      | Fecha de creación del registro.                  |
| `fecha_actualizacion` | `DateTimeField`      | Fecha de última actualización.                   |

### Tabla: `tabla_preparaciones` (`TablaPreparaciones`)

Gestiona las preparaciones o recetas asociadas a un menú.

| Columna          | Tipo de Dato      | Descripción                             |
| ---------------- | ----------------- | --------------------------------------- |
| `id_preparacion` (PK) | `AutoField`       | ID único de la preparación.             |
| `preparacion`    | `CharField(255)`  | Nombre de la preparación.               |
| `id_menu` (FK)   | `ForeignKey`      | Referencia a `TablaMenus`.              |
| `fecha_creacion` | `DateTimeField`   | Fecha de creación del registro.         |

### Tabla: `tabla_ingredientes_siesa` (`TablaIngredientesSiesa`)

Gestiona los ingredientes del inventario Siesa.

| Columna                  | Tipo de Dato      | Descripción                             |
| ------------------------ | ----------------- | --------------------------------------- |
| `id_ingrediente_siesa` (PK) | `CharField(50)`   | Código único del ingrediente.           |
| `nombre_ingrediente`     | `CharField(255)`  | Nombre del ingrediente.                 |

### Tabla: `tabla_preparacion_ingredientes` (`TablaPreparacionIngredientes`)

Tabla de relación muchos-a-muchos entre preparaciones e ingredientes.

| Columna                  | Tipo de Dato   | Descripción                             |
| ------------------------ | -------------- | --------------------------------------- |
| `id` (PK)                | `AutoField`    | ID único de la relación.                |
| `id_preparacion` (FK)    | `ForeignKey`   | Referencia a `TablaPreparaciones`.      |
| `id_ingrediente_siesa` (FK) | `ForeignKey`   | Referencia a `TablaIngredientesSiesa`.  |

### Tabla: `tabla_requerimientos_nutricionales` (`TablaRequerimientosNutricionales`)

Define los requerimientos nutricionales por nivel escolar.

| Columna                         | Tipo de Dato         | Descripción                                      |
| ------------------------------- | -------------------- | ------------------------------------------------ |
| `id_requerimiento_nutricional` (PK) | `CharField(50)`      | ID único del requerimiento.                      |
| `calorias_kcal`                 | `DecimalField(10, 1)`| Calorías en Kcal.                                |
| `proteina_g`                    | `DecimalField(10, 1)`| Proteína en gramos.                              |
| `grasa_g`                       | `DecimalField(10, 1)`| Grasa en gramos.                                 |
| `cho_g`                         | `DecimalField(10, 1)`| Carbohidratos en gramos.                         |
| `calcio_mg`                     | `DecimalField(10, 1)`| Calcio en miligramos.                            |
| `hierro_mg`                     | `DecimalField(10, 1)`| Hierro en miligramos.                            |
| `sodio_mg`                      | `DecimalField(10, 1)`| Sodio en miligramos.                             |
| `id_nivel_escolar_uapa` (FK)    | `ForeignKey`         | Referencia a `principal.TablaGradosEscolaresUapa`. |

### Tabla: `tabla_analisis_nutricional_menu` (`TablaAnalisisNutricionalMenu`)

Guarda los análisis nutricionales de menús por nivel escolar.

| Columna                   | Tipo de Dato         | Descripción                                      |
| ------------------------- | -------------------- | ------------------------------------------------ |
| `id_analisis` (PK)        | `AutoField`          | ID único del análisis.                           |
| `id_menu` (FK)            | `ForeignKey`         | Referencia a `TablaMenus`.                       |
| `id_nivel_escolar_uapa` (FK) | `ForeignKey`         | Referencia a `principal.TablaGradosEscolaresUapa`. |
| `total_calorias`          | `DecimalField(10, 2)`| Total de calorías.                               |
| `total_proteina`          | `DecimalField(10, 2)`| Total de proteína.                               |
| `total_grasa`             | `DecimalField(10, 2)`| Total de grasa.                                  |
| `total_cho`               | `DecimalField(10, 2)`| Total de carbohidratos.                          |
| `total_calcio`            | `DecimalField(10, 2)`| Total de calcio.                                 |
| `total_hierro`            | `DecimalField(10, 2)`| Total de hierro.                                 |
| `total_sodio`             | `DecimalField(10, 2)`| Total de sodio.                                  |
| `total_peso_neto`         | `DecimalField(10, 2)`| Total de peso neto.                              |
| `total_peso_bruto`        | `DecimalField(10, 2)`| Total de peso bruto.                             |
| `porcentaje_calorias`     | `DecimalField(5, 2)` | Porcentaje de adecuación de calorías.            |
| `porcentaje_proteina`     | `DecimalField(5, 2)` | Porcentaje de adecuación de proteína.            |
| `porcentaje_grasa`        | `DecimalField(5, 2)` | Porcentaje de adecuación de grasa.               |
| `porcentaje_cho`          | `DecimalField(5, 2)` | Porcentaje de adecuación de carbohidratos.       |
| `porcentaje_calcio`       | `DecimalField(5, 2)` | Porcentaje de adecuación de calcio.              |
| `porcentaje_hierro`       | `DecimalField(5, 2)` | Porcentaje de adecuación de hierro.              |
| `porcentaje_sodio`        | `DecimalField(5, 2)` | Porcentaje de adecuación de sodio.               |
| `estado_calorias`         | `CharField(20)`      | Estado de adecuación de calorías.                |
| `estado_proteina`         | `CharField(20)`      | Estado de adecuación de proteína.                |
| `estado_grasa`            | `CharField(20)`      | Estado de adecuación de grasa.                   |
| `estado_cho`              | `CharField(20)`      | Estado de adecuación de carbohidratos.           |
| `estado_calcio`           | `CharField(20)`      | Estado de adecuación de calcio.                  |
| `estado_hierro`           | `CharField(20)`      | Estado de adecuación de hierro.                  |
| `estado_sodio`            | `CharField(20)`      | Estado de adecuación de sodio.                   |
| `fecha_creacion`          | `DateTimeField`      | Fecha de creación del registro.                  |
| `fecha_actualizacion`     | `DateTimeField`      | Fecha de última actualización.                   |
| `usuario_modificacion`    | `CharField(100)`     | Usuario que realizó la última modificación.      |
| `notas`                   | `TextField`          | Notas u observaciones.                           |

### Tabla: `tabla_ingredientes_por_nivel` (`TablaIngredientesPorNivel`)

Guarda los pesos configurados de cada ingrediente por nivel escolar para un análisis.

| Columna                  | Tipo de Dato         | Descripción                                      |
| ------------------------ | -------------------- | ------------------------------------------------ |
| `id_ingrediente_nivel` (PK) | `AutoField`          | ID único del registro.                           |
| `id_analisis` (FK)       | `ForeignKey`         | Referencia a `TablaAnalisisNutricionalMenu`.     |
| `id_preparacion` (FK)    | `ForeignKey`         | Referencia a `TablaPreparaciones`.               |
| `id_ingrediente_siesa` (FK) | `ForeignKey`         | Referencia a `TablaIngredientesSiesa`.           |
| `peso_neto`              | `DecimalField(10, 2)`| Peso neto del ingrediente en gramos.             |
| `peso_bruto`             | `DecimalField(10, 2)`| Peso bruto del ingrediente en gramos.            |
| `parte_comestible`       | `DecimalField(5, 2)` | Porcentaje de parte comestible.                  |
| `calorias`               | `DecimalField(10, 2)`| Calorías calculadas para el peso.                |
| `proteina`               | `DecimalField(10, 2)`| Proteína calculada para el peso.                 |
| `grasa`                  | `DecimalField(10, 2)`| Grasa calculada para el peso.                    |
| `cho`                    | `DecimalField(10, 2)`| Carbohidratos calculados para el peso.           |
| `calcio`                 | `DecimalField(10, 2)`| Calcio calculado para el peso.                   |
| `hierro`                 | `DecimalField(10, 2)`| Hierro calculado para el peso.                   |
| `sodio`                  | `DecimalField(10, 2)`| Sodio calculado para el peso.                    |
| `codigo_icbf`            | `CharField(20)`      | Código del alimento en la tabla ICBF.            |

---

## Módulo: `ocr_validation`

### Tabla: `ocr_pdf_validation` (`PDFValidation`)

Almacena los resultados de la validación OCR de archivos PDF.

| Columna                 | Tipo de Dato      | Descripción                                      |
| ----------------------- | ----------------- | ------------------------------------------------ |
| `id` (PK)               | `AutoField`       | ID único de la validación.                       |
| `archivo_nombre`        | `CharField(255)`  | Nombre del archivo PDF.                          |
| `archivo_path`          | `CharField(500)`  | Ruta del archivo PDF.                            |
| `sede_educativa`        | `CharField(200)`  | Sede educativa a la que pertenece el documento.  |
| `mes_atencion`          | `CharField(20)`   | Mes de atención del documento.                   |
| `ano`                   | `IntegerField`    | Año de atención del documento.                   |
| `tipo_complemento`      | `CharField(20)`   | Tipo de complemento alimentario.                 |
| `usuario_creador` (FK)  | `ForeignKey`      | Usuario que inició la validación.                |
| `estado`                | `CharField(20)`   | Estado del procesamiento (`procesando`, `completado`, `error`). |
| `total_errores`         | `IntegerField`    | Conteo total de errores encontrados.             |
| `errores_criticos`      | `IntegerField`    | Conteo de errores críticos.                      |
| `errores_advertencia`   | `IntegerField`    | Conteo de advertencias.                          |
| `fecha_procesamiento`   | `DateTimeField`   | Fecha en que se inició el procesamiento.         |
| `fecha_completado`      | `DateTimeField`   | Fecha en que se completó el procesamiento.       |
| `tiempo_procesamiento`  | `FloatField`      | Duración del procesamiento en segundos.          |
| `metodo_ocr`            | `CharField(20)`   | Método OCR utilizado (e.g., `landingai`).        |
| `datos_estructurados`   | `JSONField`       | Datos tabulares extraídos del PDF.               |
| `metadatos_extraccion`  | `JSONField`       | Metadatos sobre el proceso de extracción.        |
| `texto_completo`        | `TextField`       | Texto completo extraído del PDF.                 |
| `observaciones`         | `TextField`       | Observaciones adicionales.                       |

### Tabla: `ocr_validation_errors` (`ValidationError`)

Almacena los errores específicos encontrados durante una validación OCR.

| Columna             | Tipo de Dato      | Descripción                                      |
| ------------------- | ----------------- | ------------------------------------------------ |
| `id` (PK)           | `AutoField`       | ID único del error.                              |
| `validacion` (FK)   | `ForeignKey`      | Referencia a `PDFValidation`.                    |
| `tipo_error`        | `CharField(50)`   | Categoría del error.                             |
| `descripcion`       | `CharField(255)`  | Descripción del error.                           |
| `pagina`            | `IntegerField`    | Página del PDF donde se encontró el error.       |
| `fila_estudiante`   | `IntegerField`    | Fila de la tabla de estudiantes (si aplica).     |
| `columna_campo`     | `CharField(100)`  | Columna o campo donde se encontró el error.      |
| `valor_esperado`    | `CharField(255)`  | Valor que se esperaba encontrar.                 |
| `valor_encontrado`  | `CharField(255)`  | Valor que se encontró.                           |
| `coordenada_x`      | `FloatField`      | Coordenada X aproximada del error en el PDF.     |
| `coordenada_y`      | `FloatField`      | Coordenada Y aproximada del error en el PDF.     |
| `severidad`         | `CharField(20)`   | Severidad del error (`critico`, `advertencia`, `info`). |
| `resuelto`          | `BooleanField`    | Indica si el error ha sido resuelto.             |
| `fecha_creacion`    | `DateTimeField`   | Fecha de creación del registro.                  |

### Tabla: `ocr_configuration` (`OCRConfiguration`)

Almacena parámetros de configuración para el motor OCR y las validaciones.

| Columna                       | Tipo de Dato     | Descripción                                      |
| ----------------------------- | ---------------- | ------------------------------------------------ |
| `id` (PK)                     | `AutoField`      | ID único de la configuración.                    |
| `modelo_landingai`            | `CharField(50)`  | Nombre del modelo de LandingAI a utilizar.       |
| `confianza_minima`            | `FloatField`     | Umbral de confianza mínimo para la extracción.   |
| `tolerancia_posicion_x`       | `FloatField`     | Tolerancia en el eje X para la detección de campos. |
| `tolerancia_posicion_y`       | `FloatField`     | Tolerancia en el eje Y para la detección de campos. |
| `permitir_texto_parcial`      | `BooleanField`   | Indica si se permiten coincidencias parciales.   |
| `detectar_firmas`             | `BooleanField`   | Indica si se debe detectar la presencia de firmas. |
| `procesar_imagenes`           | `BooleanField`   | Indica si se deben procesar imágenes adjuntas.   |
| `guardar_imagenes_temporales` | `BooleanField`   | Indica si se guardan imágenes temporales de debug. |
| `fecha_actualizacion`         | `DateTimeField`  | Fecha de última actualización.                   |

### Tabla: `ocr_field_validation_rules` (`FieldValidationRule`)

Define reglas de validación específicas para cada campo que se espera encontrar en el PDF.

| Columna                 | Tipo de Dato      | Descripción                                      |
| ----------------------- | ----------------- | ------------------------------------------------ |
| `id` (PK)               | `AutoField`       | ID único de la regla.                            |
| `nombre_campo`          | `CharField(100)`  | Nombre del campo a validar.                      |
| `descripcion_campo`     | `CharField(255)`  | Descripción del campo.                           |
| `tipo_campo`            | `CharField(20)`   | Tipo de campo (`texto`, `numero`, `fecha`, etc.). |
| `pagina_tipica`         | `IntegerField`    | Página donde se espera encontrar el campo.       |
| `posicion_x_relativa`   | `FloatField`      | Posición X relativa esperada.                    |
| `posicion_y_relativa`   | `FloatField`      | Posición Y relativa esperada.                    |
| `obligatorio`           | `BooleanField`    | Indica si el campo es obligatorio.               |
| `patron_validacion`     | `CharField(255)`  | Expresión regular para validar el valor.         |
| `valor_minimo`          | `CharField(100)`  | Valor mínimo permitido (para números/fechas).    |
| `valor_maximo`          | `CharField(100)`  | Valor máximo permitido (para números/fechas).    |
| `detectar_posicion_x`   | `BooleanField`    | Indica si se debe detectar la posición de una 'X'. |
| `tolerancia_posicion`   | `FloatField`      | Tolerancia de posición para la detección.        |
| `activo`                | `BooleanField`    | Indica si la regla está activa.                  |
| `fecha_creacion`        | `DateTimeField`   | Fecha de creación del registro.                  |

---

## Módulo: `planeacion`

### Tabla: `instituciones_educativas` (`InstitucionesEducativas`)

Catálogo de instituciones educativas.

| Columna                | Tipo de Dato     | Descripción                                      |
| ---------------------- | ---------------- | ------------------------------------------------ |
| `codigo_ie` (PK)       | `CharField(50)`  | Código único de la institución educativa.        |
| `nombre_institucion`   | `CharField(255)` | Nombre de la institución.                        |
| `id_municipios` (FK)   | `ForeignKey`     | Referencia a `principal.PrincipalMunicipio`.     |

### Tabla: `sedes_educativas` (`SedesEducativas`)

Catálogo de sedes educativas.

| Columna                 | Tipo de Dato      | Descripción                                      |
| ----------------------- | ----------------- | ------------------------------------------------ |
| `cod_interprise` (PK)   | `CharField(50)`   | Código único de la sede (Interprise).            |
| `cod_dane`              | `CharField(50)`   | Código DANE de la sede.                          |
| `nombre_sede_educativa` | `CharField(255)`  | Nombre de la sede.                               |
| `nombre_generico_sede`  | `CharField(255)`  | Nombre genérico de la sede.                      |
| `zona`                  | `CharField(1)`    | Zona (Urbana/Rural).                             |
| `direccion`             | `CharField(255)`  | Dirección de la sede.                            |
| `preparado`             | `CharField(50)`   | Tipo de preparación.                             |
| `industrializado`       | `CharField(50)`   | Tipo de industrialización.                       |
| `codigo_ie` (FK)        | `ForeignKey`      | Referencia a `InstitucionesEducativas`.          |

### Tabla: `programa` (`Programa`)

Gestiona los programas o contratos.

| Columna         | Tipo de Dato     | Descripción                                      |
| --------------- | ---------------- | ------------------------------------------------ |
| `id` (PK)       | `AutoField`      | ID único del programa.                           |
| `programa`      | `CharField(200)` | Nombre del programa.                             |
| `fecha_inicial` | `DateField`      | Fecha de inicio del programa.                    |
| `fecha_final`   | `DateField`      | Fecha de fin del programa.                       |
| `estado`        | `CharField(8)`   | Estado del programa (`activo`, `inactivo`).      |
| `imagen`        | `ImageField`     | Imagen representativa del programa.              |
| `contrato`      | `CharField(100)` | Identificador del contrato.                      |
| `municipio` (FK)| `ForeignKey`     | Referencia a `principal.PrincipalMunicipio`.     |

### Tabla: `planificacion_raciones` (`PlanificacionRaciones`)

Almacena la planificación de raciones por sede, focalización y nivel.

| Columna           | Tipo de Dato    | Descripción                                      |
| ----------------- | --------------- | ------------------------------------------------ |
| `id` (PK)         | `AutoField`     | ID único de la planificación.                    |
| `etc` (FK)        | `ForeignKey`    | Referencia a `principal.PrincipalMunicipio`.     |
| `focalizacion`    | `CharField(10)` | Tipo de focalización.                            |
| `sede_educativa` (FK) | `ForeignKey`    | Referencia a `SedesEducativas`.                  |
| `nivel_escolar` (FK) | `ForeignKey`    | Referencia a `principal.NivelGradoEscolar`.      |
| `ano`             | `IntegerField`  | Año de la planificación.                         |
| `cap_am`          | `IntegerField`  | Cantidad de Complemento Alimentario Preparado AM. |
| `cap_pm`          | `IntegerField`  | Cantidad de Complemento Alimentario Preparado PM. |
| `almuerzo_ju`     | `IntegerField`  | Cantidad de Almuerzo en Jornada Única.           |
| `refuerzo`        | `IntegerField`  | Cantidad de Refuerzo.                            |
| `fecha_creacion`  | `DateTimeField` | Fecha de creación del registro.                  |
| `fecha_actualizacion` | `DateTimeField` | Fecha de última actualización.                   |

---

## Módulo: `principal`

### Tabla: `principal_departamento` (`PrincipalDepartamento`)

Catálogo de departamentos.

| Columna                 | Tipo de Dato     | Descripción                             |
| ----------------------- | ---------------- | --------------------------------------- |
| `codigo_departamento` (PK) | `CharField(100)` | Código único del departamento.          |
| `nombre_departamento`   | `CharField(100)` | Nombre del departamento.                |

### Tabla: `principal_municipio` (`PrincipalMunicipio`)

Catálogo de municipios.

| Columna             | Tipo de Dato     | Descripción                             |
| ------------------- | ---------------- | --------------------------------------- |
| `id` (PK)           | `BigAutoField`   | ID único del municipio.                 |
| `codigo_municipio`  | `IntegerField`   | Código del municipio.                   |
| `nombre_municipio`  | `CharField(100)` | Nombre del municipio.                   |
| `codigo_departamento` | `CharField(100)` | Código del departamento al que pertenece. |

### Tabla: `tipo_documento` (`TipoDocumento`)

Catálogo de tipos de documento de identidad.

| Columna            | Tipo de Dato     | Descripción                             |
| ------------------ | ---------------- | --------------------------------------- |
| `id_documento` (PK)| `CharField(10)`  | ID único del tipo de documento.         |
| `tipo_documento`   | `CharField(100)` | Nombre del tipo de documento.           |
| `codigo_documento` | `IntegerField`   | Código numérico del tipo de documento.  |

### Tabla: `tipo_genero` (`TipoGenero`)

Catálogo de géneros.

| Columna         | Tipo de Dato     | Descripción                             |
| --------------- | ---------------- | --------------------------------------- |
| `id_genero` (PK)| `CharField(10)`  | ID único del género.                    |
| `genero`        | `CharField(50)`  | Nombre del género.                      |
| `codigo_genero` | `IntegerField`   | Código numérico del género.             |

### Tabla: `modalidades_de_consumo` (`ModalidadesDeConsumo`)

Catálogo de modalidades de consumo.

| Columna         | Tipo de Dato      | Descripción                             |
| --------------- | ----------------- | --------------------------------------- |
| `id_modalidades` (PK)| `CharField(10)`   | ID único de la modalidad.               |
| `modalidad`     | `CharField(150)`  | Nombre de la modalidad.                 |
| `cod_modalidad` | `CharField(20)`   | Código de la modalidad.                 |

### Tabla: `municipio_modalidades` (`MunicipioModalidades`)

Tabla de relación muchos-a-muchos entre municipios y modalidades de consumo.

| Columna         | Tipo de Dato   | Descripción                             |
| --------------- | -------------- | --------------------------------------- |
| `id` (PK)       | `BigAutoField` | ID único de la relación.                |
| `municipio` (FK)| `ForeignKey`   | Referencia a `PrincipalMunicipio`.      |
| `modalidad` (FK)| `ForeignKey`   | Referencia a `ModalidadesDeConsumo`.    |

### Tabla: `nivel_grado_escolar` (`NivelGradoEscolar`)

Catálogo de niveles y grados escolares.

| Columna                | Tipo de Dato      | Descripción                                      |
| ---------------------- | ----------------- | ------------------------------------------------ |
| `id_grado_escolar` (PK)| `CharField(50)`   | ID único del grado escolar.                      |
| `grados_sedes`         | `CharField(200)`  | Descripción de los grados.                       |
| `nivel_escolar_uapa` (FK)| `ForeignKey`      | Referencia a `TablaGradosEscolaresUapa`.         |

### Tabla: `tabla_grados_escolares_uapa` (`TablaGradosEscolaresUapa`)

Catálogo de grados escolares según UAPA.

| Columna                   | Tipo de Dato      | Descripción                             |
| ------------------------- | ----------------- | --------------------------------------- |
| `id_grado_escolar_uapa` (PK)| `CharField(50)`   | ID único del grado UAPA.                |
| `nivel_escolar_uapa`      | `CharField(100)`  | Nombre del nivel escolar UAPA.          |
