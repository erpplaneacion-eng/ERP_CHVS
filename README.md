# 🏛️ ERP CHVS - Sistema de Gestión Integral
### *Sistema de Gestión Empresarial para CHVS (Programa de Alimentación Escolar)*

---

## 📋 **Información General del Proyecto**

| **Atributo** | **Descripción** |
|-------------|----------------|
| **Nombre** | ERP CHVS |
| **Descripción** | Sistema integral de gestión para el programa de alimentación escolar de CHVS |
| **Framework** | Django 4.x + Python 3.x |
| **Base de Datos** | SQLite (desarrollo) |
| **Frontend** | HTML5, CSS3, JavaScript (jQuery), Bootstrap |
| **Arquitectura** | Modular por funcionalidades (6 módulos principales) |

---

## 🏗️ **Estructura del Proyecto**

```
ERP_CHVS/
├── 📦 erp_chvs/                    # Proyecto Django principal
│   ├── 🏛️ principal/              # Módulo de datos maestros
│   ├── 📊 dashboard/               # Módulo de tablero de control
│   ├── 🍎 nutricion/               # Módulo de gestión nutricional
│   ├── 📋 planeacion/              # Módulo de planeación y programas
│   ├── 💰 facturacion/             # Módulo de facturación y focalización
│   ├── 📄 ocr_validation/          # Módulo de validación OCR de documentos
│   ├── 🖼️ media/                   # Archivos multimedia
│   ├── 🎨 static/                  # Archivos estáticos (CSS, JS, imágenes)
│   └── 📝 templates/               # Plantillas HTML
├── 📊 archivos excel/              # Archivos Excel de datos
└── 📖 README.md                    # Este documento
```

---

## 🗄️ **Base de Datos - Tablas por Módulo**

### 🏛️ **MÓDULO PRINCIPAL** *(Datos Maestros)*

#### **1. PrincipalDepartamento**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `codigo_departamento` | CharField(100) [PK] | Código único del departamento |
| `nombre_departamento` | CharField(100) | Nombre del departamento |

#### **2. PrincipalMunicipio**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | BigAutoField [PK] | ID único autogenerado |
| `codigo_municipio` | IntegerField | Código DANE del municipio |
| `nombre_municipio` | CharField(100) | Nombre del municipio |
| `codigo_departamento` | CharField(100) | Código del departamento |

#### **3. TipoDocumento**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_documento` | CharField(10) [PK] | ID único del tipo de documento |
| `tipo_documento` | CharField(100) | Nombre del tipo de documento |
| `codigo_documento` | IntegerField | Código numérico del documento |

#### **4. TipoGenero**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_genero` | CharField(10) [PK] | ID único del género |
| `genero` | CharField(50) | Descripción del género |
| `codigo_genero` | IntegerField | Código numérico del género |

#### **5. ModalidadesDeConsumo**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_modalidades` | CharField(10) [PK] | ID único de la modalidad |
| `modalidad` | CharField(150) | Nombre de la modalidad |
| `cod_modalidad` | CharField(20) | Código de la modalidad |

#### **6. MunicipioModalidades** *(Tabla Intermedia)*
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | BigAutoField [PK] | ID único autogenerado |
| `municipio` | FK → PrincipalMunicipio | Municipio asignado |
| `modalidad` | FK → ModalidadesDeConsumo | Modalidad disponible |

#### **7. TablaGradosEscolaresUapa**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_grado_escolar_uapa` | CharField(50) [PK] | Código del grado escolar UAPA |
| `nivel_escolar_uapa` | CharField(100) | Descripción del nivel escolar |

#### **8. NivelGradoEscolar**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_grado_escolar` | CharField(50) [PK] | ID único del grado escolar |
| `grados_sedes` | CharField(200) | Grados por sede |
| `nivel_escolar_uapa` | FK → TablaGradosEscolaresUapa | Nivel escolar UAPA |

---

### 📋 **MÓDULO PLANEACIÓN** *(Programas y Planificación)*

#### **9. InstitucionesEducativas**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `codigo_ie` | CharField(50) [PK] | Código único de la institución |
| `nombre_institucion` | CharField(255) | Nombre de la institución |
| `id_municipios` | FK → PrincipalMunicipio | Municipio de la institución |

#### **10. SedesEducativas**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `cod_interprise` | CharField(50) [PK] | Código Interprise de la sede |
| `cod_dane` | CharField(50) | Código DANE de la sede |
| `nombre_sede_educativa` | CharField(255) | Nombre de la sede educativa |
| `nombre_generico_sede` | CharField(255) | Nombre genérico de la sede |
| `zona` | CharField(1) | Zona (U/R) |
| `direccion` | CharField(255) | Dirección de la sede |
| `preparado` | CharField(50) | Tipo preparado |
| `industrializado` | CharField(50) | Tipo industrializado |
| `codigo_ie` | FK → InstitucionesEducativas | Institución educativa |

#### **11. Programa**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | AutoField [PK] | ID único autogenerado |
| `programa` | CharField(200) | Nombre del programa |
| `fecha_inicial` | DateField | Fecha de inicio del programa |
| `fecha_final` | DateField | Fecha de finalización |
| `estado` | CharField(8) | Estado (activo/inactivo) |
| `imagen` | ImageField | Imagen del programa |
| `contrato` | CharField(100) | Número de contrato |
| `municipio` | FK → PrincipalMunicipio | Municipio del programa |

#### **12. PlanificacionRaciones**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | AutoField [PK] | ID único autogenerado |
| `etc` | FK → PrincipalMunicipio | ETC (Municipio) |
| `focalizacion` | CharField(10) | Tipo de focalización (F1, F2, F3) |
| `sede_educativa` | FK → SedesEducativas | Sede educativa |
| `nivel_escolar` | FK → NivelGradoEscolar | Nivel escolar |
| `ano` | IntegerField | Año de planificación |
| `cap_am` | IntegerField | CAP AM (Complemento Preparado AM) |
| `cap_pm` | IntegerField | CAP PM (Complemento Preparado PM) |
| `almuerzo_ju` | IntegerField | Almuerzo Jornada Única |
| `refuerzo` | IntegerField | Refuerzo Complemento AM/PM |
| `fecha_creacion` | DateTimeField | Fecha de creación |
| `fecha_actualizacion` | DateTimeField | Fecha de actualización |

---

### 🍎 **MÓDULO NUTRICIÓN** *(Gestión Nutricional)*

#### **13. TablaAlimentos2018Icbf** *(Datos Nutricionales ICBF)*
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `codigo` | CharField(20) [PK] | Código único del alimento |
| `nombre_del_alimento` | CharField(200) | Nombre del alimento |
| `parte_analizada` | CharField(100) | Parte analizada del alimento |
| `humedad_g` | DecimalField(10,2) | Humedad en gramos |
| `energia_kcal` | IntegerField | Energía en kilocalorías |
| `energia_kj` | IntegerField | Energía en kilojulios |
| `proteina_g` | DecimalField(10,2) | Proteína en gramos |
| `lipidos_g` | DecimalField(10,2) | Lípidos en gramos |
| `carbohidratos_totales_g` | DecimalField(10,2) | Carbohidratos totales |
| `carbohidratos_disponibles_g` | DecimalField(10,2) | Carbohidratos disponibles |
| `fibra_dietaria_g` | DecimalField(10,2) | Fibra dietaria |
| `cenizas_g` | DecimalField(10,2) | Cenizas |
| `calcio_mg` | IntegerField | Calcio en miligramos |
| `hierro_mg` | DecimalField(10,2) | Hierro en miligramos |
| `sodio_mg` | IntegerField | Sodio en miligramos |
| `fosforo_mg` | IntegerField | Fósforo en miligramos |
| `yodo_mg` | DecimalField(10,2) | Yodo en miligramos |
| `zinc_mg` | DecimalField(10,2) | Zinc en miligramos |
| `magnesio_mg` | IntegerField | Magnesio en miligramos |
| `potasio_mg` | IntegerField | Potasio en miligramos |
| `tiamina_mg` | DecimalField(10,2) | Tiamina (Vitamina B1) |
| `riboflavina_mg` | DecimalField(10,2) | Riboflavina (Vitamina B2) |
| `niacina_mg` | DecimalField(10,2) | Niacina (Vitamina B3) |
| `folatos_mcg` | DecimalField(10,2) | Folatos en microgramos |
| `vitamina_b12_mcg` | DecimalField(10,2) | Vitamina B12 |
| `vitamina_c_mg` | IntegerField | Vitamina C |
| `vitamina_a_er` | IntegerField | Vitamina A (ER) |
| `grasa_saturada_g` | DecimalField(10,2) | Grasa saturada |
| `grasa_monoinsaturada_g` | DecimalField(10,2) | Grasa monoinsaturada |
| `grasa_poliinsaturada_g` | DecimalField(10,2) | Grasa poliinsaturada |
| `colesterol_mg` | IntegerField | Colesterol |
| `parte_comestible_field` | IntegerField | Porcentaje parte comestible |

#### **14. TablaMenus**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_menu` | AutoField [PK] | ID único del menú |
| `menu` | CharField(255) | Nombre del menú |
| `id_modalidad` | FK → ModalidadesDeConsumo | Modalidad de consumo |
| `id_contrato` | FK → Programa | Programa/Contrato |
| `fecha_creacion` | DateTimeField | Fecha de creación |
| `fecha_actualizacion` | DateTimeField | Fecha de actualización |

#### **15. TablaPreparaciones**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_preparacion` | AutoField [PK] | ID único de la preparación |
| `preparacion` | CharField(255) | Nombre de la preparación |
| `id_menu` | FK → TablaMenus | Menú al que pertenece |
| `fecha_creacion` | DateTimeField | Fecha de creación |

#### **16. TablaIngredientesSiesa**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_ingrediente_siesa` | CharField(50) [PK] | Código del ingrediente en Siesa |
| `nombre_ingrediente` | CharField(255) | Nombre del ingrediente |

#### **17. TablaPreparacionIngredientes** *(Tabla Intermedia)*
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_preparacion` | FK → TablaPreparaciones | Preparación |
| `id_ingrediente_siesa` | FK → TablaIngredientesSiesa | Ingrediente |

#### **18. TablaRequerimientosNutricionales**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_requerimiento_nutricional` | CharField(50) [PK] | ID del requerimiento |
| `calorias_kcal` | DecimalField(10,1) | Requerimiento de calorías |
| `proteina_g` | DecimalField(10,1) | Requerimiento de proteína |
| `grasa_g` | DecimalField(10,1) | Requerimiento de grasa |
| `cho_g` | DecimalField(10,1) | Requerimiento de CHO |
| `calcio_mg` | DecimalField(10,1) | Requerimiento de calcio |
| `hierro_mg` | DecimalField(10,1) | Requerimiento de hierro |
| `sodio_mg` | DecimalField(10,1) | Requerimiento de sodio |
| `id_nivel_escolar_uapa` | FK → TablaGradosEscolaresUapa | Nivel escolar UAPA |

#### **19. TablaAnalisisNutricionalMenu** *(Sistema de Análisis Avanzado)*
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_analisis` | AutoField [PK] | ID único del análisis |
| `id_menu` | FK → TablaMenus | Menú analizado |
| `id_nivel_escolar_uapa` | FK → TablaGradosEscolaresUapa | Nivel escolar |
| **Totales Calculados** | | |
| `total_calorias` | DecimalField(10,2) | Total de calorías calculadas |
| `total_proteina` | DecimalField(10,2) | Total de proteína calculada |
| `total_grasa` | DecimalField(10,2) | Total de grasa calculada |
| `total_cho` | DecimalField(10,2) | Total de CHO calculado |
| `total_calcio` | DecimalField(10,2) | Total de calcio calculado |
| `total_hierro` | DecimalField(10,2) | Total de hierro calculado |
| `total_sodio` | DecimalField(10,2) | Total de sodio calculado |
| `total_peso_neto` | DecimalField(10,2) | Total peso neto |
| `total_peso_bruto` | DecimalField(10,2) | Total peso bruto |
| **Porcentajes de Adecuación** | | |
| `porcentaje_calorias` | DecimalField(5,2) | % Adecuación calorías |
| `porcentaje_proteina` | DecimalField(5,2) | % Adecuación proteína |
| `porcentaje_grasa` | DecimalField(5,2) | % Adecuación grasa |
| `porcentaje_cho` | DecimalField(5,2) | % Adecuación CHO |
| `porcentaje_calcio` | DecimalField(5,2) | % Adecuación calcio |
| `porcentaje_hierro` | DecimalField(5,2) | % Adecuación hierro |
| `porcentaje_sodio` | DecimalField(5,2) | % Adecuación sodio |
| **Estados de Adecuación** | | |
| `estado_calorias` | CharField(20) | Estado calorías (óptimo/aceptable/alto) |
| `estado_proteina` | CharField(20) | Estado proteína |
| `estado_grasa` | CharField(20) | Estado grasa |
| `estado_cho` | CharField(20) | Estado CHO |
| `estado_calcio` | CharField(20) | Estado calcio |
| `estado_hierro` | CharField(20) | Estado hierro |
| `estado_sodio` | CharField(20) | Estado sodio |
| **Metadatos** | | |
| `fecha_creacion` | DateTimeField | Fecha de creación |
| `fecha_actualizacion` | DateTimeField | Fecha de actualización |
| `usuario_modificacion` | CharField(100) | Usuario que modificó |
| `notas` | TextField | Notas u observaciones |

#### **20. TablaIngredientesPorNivel** *(Configuración Detallada por Nivel)*
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_ingrediente_nivel` | AutoField [PK] | ID único |
| `id_analisis` | FK → TablaAnalisisNutricionalMenu | Análisis nutricional |
| `id_preparacion` | FK → TablaPreparaciones | Preparación |
| `id_ingrediente_siesa` | FK → TablaIngredientesSiesa | Ingrediente |
| **Pesos Configurados** | | |
| `peso_neto` | DecimalField(10,2) | Peso neto configurado |
| `peso_bruto` | DecimalField(10,2) | Peso bruto calculado |
| `parte_comestible` | DecimalField(5,2) | % Parte comestible |
| **Valores Nutricionales Calculados** | | |
| `calorias` | DecimalField(10,2) | Calorías para este peso |
| `proteina` | DecimalField(10,2) | Proteína para este peso |
| `grasa` | DecimalField(10,2) | Grasa para este peso |
| `cho` | DecimalField(10,2) | CHO para este peso |
| `calcio` | DecimalField(10,2) | Calcio para este peso |
| `hierro` | DecimalField(10,2) | Hierro para este peso |
| `sodio` | DecimalField(10,2) | Sodio para este peso |
| `codigo_icbf` | CharField(20) | Referencia a alimento ICBF |

---

### 💰 **MÓDULO FACTURACIÓN** *(Focalización y Facturación)*

#### **21. ListadosFocalizacion**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id_listados` | CharField(50) [PK] | ID único del listado |
| `ano` | IntegerField | Año de focalización |
| `etc` | CharField(100) | ETC (Entidad Territorial) |
| `institucion` | CharField(200) | Institución educativa |
| `sede` | CharField(200) | Sede educativa |
| **Información del Titular** | | |
| `tipodoc` | CharField(10) | Tipo de documento |
| `doc` | CharField(50) | Número de documento |
| `apellido1` | CharField(100) | Primer apellido |
| `apellido2` | CharField(100) | Segundo apellido |
| `nombre1` | CharField(100) | Primer nombre |
| `nombre2` | CharField(100) | Segundo nombre |
| `fecha_nacimiento` | CharField(20) | Fecha de nacimiento |
| `edad` | IntegerField | Edad |
| `etnia` | CharField(50) | Etnia |
| `genero` | CharField(10) | Género |
| `grado_grupos` | CharField(20) | Grado y grupos |
| **Complementos Alimentarios** | | |
| `complemento_alimentario_preparado_am` | CharField(10) | CAP AM |
| `complemento_alimentario_preparado_pm` | CharField(10) | CAP PM |
| `almuerzo_jornada_unica` | CharField(10) | Almuerzo JU |
| `refuerzo_complemento_am_pm` | CharField(10) | Refuerzo |
| `focalizacion` | CharField(10) | Tipo de focalización |
| `fecha_creacion` | DateTimeField | Fecha de creación |
| `fecha_actualizacion` | DateTimeField | Fecha de actualización |

---

### 📄 **MÓDULO OCR VALIDATION** *(Validación de Documentos)*

#### **22. PDFValidation**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | AutoField [PK] | ID único autogenerado |
| `archivo_nombre` | CharField(255) | Nombre del archivo PDF |
| `archivo_path` | CharField(500) | Ruta del archivo |
| `sede_educativa` | CharField(200) | Sede educativa |
| `mes_atencion` | CharField(20) | Mes de atención |
| `ano` | IntegerField | Año |
| `tipo_complemento` | CharField(20) | Tipo de complemento |
| `usuario_creador` | FK → User | Usuario que creó la validación |
| `estado` | CharField(20) | Estado (procesando/completado/error) |
| `total_errores` | IntegerField | Total de errores encontrados |
| `errores_criticos` | IntegerField | Errores críticos |
| `errores_advertencia` | IntegerField | Advertencias |
| `fecha_procesamiento` | DateTimeField | Fecha de procesamiento |
| `fecha_completado` | DateTimeField | Fecha de completado |
| `tiempo_procesamiento` | FloatField | Tiempo en segundos |
| `observaciones` | TextField | Observaciones |

#### **23. ValidationError**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | AutoField [PK] | ID único autogenerado |
| `validacion` | FK → PDFValidation | Validación padre |
| `tipo_error` | CharField(50) | Tipo de error |
| `descripcion` | CharField(255) | Descripción del error |
| `pagina` | IntegerField | Página donde ocurrió |
| `fila_estudiante` | IntegerField | Fila del estudiante |
| `columna_campo` | CharField(100) | Campo/Columna |
| `valor_esperado` | CharField(255) | Valor esperado |
| `valor_encontrado` | CharField(255) | Valor encontrado |
| `coordenada_x` | FloatField | Coordenada X |
| `coordenada_y` | FloatField | Coordenada Y |
| `severidad` | CharField(20) | Severidad (crítico/advertencia/info) |
| `resuelto` | BooleanField | Estado de resolución |
| `fecha_creacion` | DateTimeField | Fecha de creación |

#### **24. OCRConfiguration**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | AutoField [PK] | ID único autogenerado |
| `tesseract_config` | TextField | Configuración Tesseract |
| `confianza_minima` | FloatField | Confianza mínima OCR (%) |
| `tolerancia_posicion_x` | FloatField | Tolerancia posición X |
| `tolerancia_posicion_y` | FloatField | Tolerancia posición Y |
| `permitir_texto_parcial` | BooleanField | Permitir texto parcial |
| `detectar_firmas` | BooleanField | Detectar presencia de firmas |
| `procesar_imagenes` | BooleanField | Procesar imágenes adjuntas |
| `guardar_imagenes_temporales` | BooleanField | Guardar imágenes temporales |
| `fecha_actualizacion` | DateTimeField | Fecha de actualización |

#### **25. FieldValidationRule**
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| `id` | AutoField [PK] | ID único autogenerado |
| `nombre_campo` | CharField(100) | Nombre del campo |
| `descripcion_campo` | CharField(255) | Descripción del campo |
| `tipo_campo` | CharField(20) | Tipo (texto/numero/fecha/firma/celda_x/total) |
| `pagina_tipica` | IntegerField | Página típica |
| `posicion_x_relativa` | FloatField | Posición X relativa |
| `posicion_y_relativa` | FloatField | Posición Y relativa |
| `obligatorio` | BooleanField | Campo obligatorio |
| `patron_validacion` | CharField(255) | Patrón de validación (Regex) |
| `valor_minimo` | CharField(100) | Valor mínimo |
| `valor_maximo` | CharField(100) | Valor máximo |
| `detectar_posicion_x` | BooleanField | Detectar posición exacta de X |
| `tolerancia_posicion` | FloatField | Tolerancia de posición |
| `activo` | BooleanField | Regla activa |
| `fecha_creacion` | DateTimeField | Fecha de creación |

---

### 📊 **MÓDULO DASHBOARD** *(Tablero de Control)*

#### **26. PermisosNutricion** *(Solo Permisos)*
| **Campo** | **Tipo** | **Descripción** |
|-----------|----------|----------------|
| *Meta class only* | - | Define permisos del módulo de nutrición |

*Este módulo actualmente no tiene tablas de datos, solo define permisos.*

---

## 🔗 **Relaciones entre Módulos**

### **🔄 Relaciones Principales:**

1. **Principal** ↔ **Planeación**
   - `Programa.municipio` → `PrincipalMunicipio`
   - `InstitucionesEducativas.id_municipios` → `PrincipalMunicipio`

2. **Principal** ↔ **Nutrición**
   - `TablaMenus.id_modalidad` → `ModalidadesDeConsumo`
   - `TablaRequerimientosNutricionales.id_nivel_escolar_uapa` → `TablaGradosEscolaresUapa`

3. **Planeación** ↔ **Nutrición**
   - `TablaMenus.id_contrato` → `Programa`
   - `PlanificacionRaciones.nivel_escolar` → `NivelGradoEscolar`

4. **Nutrición** ↔ **Facturación**
   - Relación indirecta a través de focalizaciones y modalidades

5. **OCR Validation** ↔ **Otros Módulos**
   - Procesa documentos relacionados con las entidades de otros módulos

---

## 🎯 **Funcionalidades Principales por Módulo**

### 🏛️ **PRINCIPAL**
- ✅ **Gestión de datos maestros** (departamentos, municipios, tipos)
- ✅ **Configuración de modalidades** de consumo
- ✅ **Gestión de niveles escolares** y grados UAPA

### 📋 **PLANEACIÓN**
- ✅ **Gestión de programas** y contratos
- ✅ **Instituciones y sedes** educativas
- ✅ **Planificación de raciones** por modalidad y nivel
- ✅ **Asignación de complementos** alimentarios

### 🍎 **NUTRICIÓN**
- ✅ **Base de datos nutricional** ICBF 2018 (25+ nutrientes)
- ✅ **Gestión de menús** y preparaciones
- ✅ **Análisis nutricional avanzado** con cálculos bidireccionales
- ✅ **Configuración de ingredientes** por nivel escolar
- ✅ **Requerimientos nutricionales** por grupo etario
- ✅ **Auto-save** y persistencia de configuraciones
- ✅ **Sistema de % adecuación** nutricional

### 💰 **FACTURACIÓN**
- ✅ **Gestión de listados** de focalización
- ✅ **Datos de titulares** de derecho
- ✅ **Complementos alimentarios** asignados
- ✅ **Procesamiento de archivos** Excel masivos

### 📄 **OCR VALIDATION**
- ✅ **Validación automática** de PDFs diligenciados
- ✅ **Detección de errores** en documentos
- ✅ **Configuración de reglas** de validación
- ✅ **Procesamiento OCR** con Tesseract
- ✅ **Gestión de errores** por severidad

### 📊 **DASHBOARD**
- ✅ **Tablero de control** centralizado
- ✅ **Sistema de permisos** por módulo
- ✅ **Navegación integrada** entre módulos

---

## 🚀 **Tecnologías y Arquitectura**

### **Backend:**
- **Django 4.x** - Framework principal
- **Python 3.x** - Lenguaje de programación
- **SQLite** - Base de datos (desarrollo)
- **Django ORM** - Mapeo objeto-relacional

### **Frontend:**
- **HTML5/CSS3** - Estructura y estilos
- **JavaScript ES6+** - Funcionalidad dinámica
- **jQuery 3.x** - Manipulación DOM
- **Bootstrap 5** - Framework CSS
- **Font Awesome** - Iconografía

### **JavaScript Arquitectura:**
```
static/js/nutricion/
├── 📦 core/                    # Módulos centralizados
│   ├── utils.js               # Utilidades comunes
│   ├── modal-manager.js       # Gestión de modales
│   └── api-client.js          # Cliente API centralizado
├── 🍽️ menus_avanzado.js      # Sistema principal (1,622 líneas)
├── 🥘 preparaciones.js        # Gestión de preparaciones
├── 🥕 ingredientes.js         # Gestión de ingredientes
├── 🍎 alimentos.js            # Gestión de alimentos
└── 🚀 main.js                 # Inicializador principal
```

### **Características Técnicas:**
- ✅ **Arquitectura modular** por funcionalidades
- ✅ **Sistema de auto-guardado** en tiempo real
- ✅ **Cálculos nutricionales** bidireccionales
- ✅ **Validación OCR** con inteligencia artificial
- ✅ **API REST** para comunicación frontend-backend
- ✅ **Sistema de permisos** granular
- ✅ **Procesamiento de archivos** Excel masivos

---

## 📈 **Estadísticas del Proyecto**

| **Métrica** | **Cantidad** |
|-------------|-------------|
| **Módulos principales** | 6 |
| **Tablas de base de datos** | 26 |
| **Modelos Django** | 26 |
| **Archivos JavaScript** | 8 |
| **Líneas de código JS** | ~3,500+ |
| **Templates HTML** | 15+ |
| **Archivos CSS** | 5+ |
| **APIs REST** | 20+ endpoints |

---

## 🎯 **Casos de Uso Principales**

### 👥 **Para Nutricionistas:**
1. **Crear y gestionar menús** por modalidad
2. **Configurar preparaciones** e ingredientes
3. **Realizar análisis nutricional** avanzado
4. **Ajustar pesos** para cumplir % adecuación
5. **Generar reportes** nutricionales

### 📋 **Para Planificadores:**
1. **Gestionar programas** y contratos
2. **Planificar raciones** por sede y nivel
3. **Asignar modalidades** por municipio
4. **Configurar instituciones** y sedes

### 💰 **Para Área de Facturación:**
1. **Procesar listados** de focalización
2. **Validar complementos** asignados
3. **Generar reportes** de atención
4. **Gestionar titulares** de derecho

### 📄 **Para Control de Calidad:**
1. **Validar PDFs** diligenciados
2. **Detectar errores** automáticamente
3. **Configurar reglas** de validación
4. **Generar reportes** de cumplimiento

---

## 🏆 **Características Destacadas**

### 🔄 **Sistema de Análisis Nutricional Bidireccional**
- Edición por **peso neto** → recalcula % adecuación
- Edición por **% adecuación** → redistribuye pesos automáticamente
- **Auto-save** en tiempo real
- **Validación nutricional** automática

### 🎯 **Gestión Integral de Modalidades**
- **CAP AM/PM** (Complemento Alimentario Preparado)
- **Almuerzo Jornada Única**
- **Refuerzo Complemento**
- **Configuración por nivel escolar**

### 📊 **Base de Datos Nutricional Completa**
- **25+ nutrientes** por alimento
- **Datos oficiales ICBF 2018**
- **Cálculos automáticos** de peso bruto/neto
- **Parte comestible** configurable

### 🤖 **Validación OCR Inteligente**
- **Procesamiento automático** de PDFs
- **Detección de errores** por IA
- **Configuración flexible** de reglas
- **Reportes detallados** de validación

---

## 📞 **Información de Contacto**

**Proyecto:** ERP CHVS - Sistema de Gestión Integral  
**Organización:** CHVS (Programa de Alimentación Escolar)  
**Tecnología:** Django + Python + JavaScript  
**Estado:** En desarrollo activo  

---

*Documento generado automáticamente desde la estructura del proyecto Django.*  
*Última actualización: Octubre 2025*