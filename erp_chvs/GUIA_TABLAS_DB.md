# Guía de Tablas - Base de Datos ERP_CHVS

Esta guía contiene un barrido completo de las tablas identificadas en la base de datos `erp_chvs`.

## 1. Módulo de Nutrición
Tablas encargadas de la gestión de alimentos, preparaciones, menús y análisis nutricional.

*   **TABLA_ALIMENTOS_2018_ICBF**: Tabla de composición de alimentos (TCAC) según ICBF 2018.
*   **nutricion_grupos_alimento**: Clasificación general de grupos de alimentos.
*   **nutricion_componentes_alimentos**: Componentes específicos (ej. Proteico, Cereal) asociados a grupos.
*   **nutricion_tabla_preparaciones**: Nombres de las preparaciones (recetas).
*   **nutricion_tabla_preparacion_ingredientes**: Relación M2M entre preparaciones e ingredientes de Siesa.
*   **nutricion_tabla_menus**: Definición de menús por contrato y modalidad.
*   **nutricion_tabla_analisis_nutricional_menu**: Resultados consolidados del análisis nutricional por menú y nivel.
*   **nutricion_tabla_ingredientes_por_nivel**: Detalle de pesos y aportes de cada ingrediente en un análisis específico.
*   **nutricion_requerimientos_semanales**: Configuración de frecuencias por modalidad y componente.
*   **nutricion_total_aporte_promedio_diario**: Metas/Recomendaciones nutricionales por nivel y modalidad.
*   **tabla_ingredientes_siesa**: Catálogo de ingredientes según el sistema Siesa.

## 2. Módulo de Planeación y Ciclos
Gestión de programas y la estructura de menús en el tiempo.

*   **planeacion_programa**: Programas/Contratos activos (ej. PAE Cali).
*   **ciclo_menu_semanal**: Estructura de una semana de menús con sus promedios y adecuaciones.
*   **menu_diario_ciclo**: Relación de qué menú corresponde a cada día de un ciclo semanal.

## 3. Módulo de Focalización y Sedes
Gestión de beneficiarios, instituciones y raciones.

*   **listados_focalizacion**: Datos maestros de beneficiarios cargados desde Excel.
*   **instituciones_educativas**: Sedes principales (IE).
*   **sedes_educativas**: Sedes físicas con sus códigos DANE e Interprise.
*   **planificacion_raciones**: Proyección de raciones por sede, grado y año.
*   **tabla_grados_escolares_uapa**: Niveles estándar definidos por la UAPA (Preescolar, Primaria, etc.).
*   **nivel_grado_escolar**: Mapeo de grados específicos a niveles UAPA.

## 4. Tablas Maestras y Geografía
*   **principal_departamento**: Departamentos de Colombia.
*   **principal_municipio**: Municipios con sus códigos.
*   **municipio_modalidades**: Relación de qué modalidades aplican en cada municipio.
*   **modalidades_de_consumo**: Definición de modalidades (Preparada en Sitio, Industrializada, etc.).
*   **tipo_documento**: Catálogo de tipos de identificación.
*   **tipo_genero**: Catálogo de géneros.

## 5. Sistema (Django)
*   **auth_user**: Usuarios del sistema.
*   **auth_group / auth_permission**: Gestión de permisos y roles.
*   **django_admin_log**: Historial de acciones en el panel de administración.
*   **django_migrations**: Registro de migraciones aplicadas.
*   **django_session**: Sesiones activas de usuarios.
