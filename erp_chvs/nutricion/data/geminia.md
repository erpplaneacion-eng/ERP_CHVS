Plan de Implementación: Generador de Menús con Gemini AI


  Paso 1: Infraestructura de IA (gemini_service.py)
  Crearemos un servicio centralizado que gestione la comunicación con la API.
   * Tarea: Implementar nutricion/services/gemini_service.py.
   * Lógica: Este archivo cargará la GEMINI_API_KEY, configurará el modelo (sugiero gemini-1.5-flash por velocidad y costo) y manejará los errores
     de conexión.
   * Contexto: Implementará una función para "comprimir" la tabla de alimentos ICBF 2018, enviando a la IA solo los datos esenciales (Nombre,
     Energía, Proteína, etc.) para ahorrar tokens.


  Paso 2: Motor de Reglas (Prompt Engineering)
  Diseñaremos el "cerebro" del generador.
   * Tarea: Crear la lógica que lee el archivo minuta_patron.json y lo inyecta en el prompt de Gemini.
   * Restricciones: El prompt obligará a la IA a seguir las frecuencias semanales (ej. Fruta 3 veces por semana) y a mantenerse dentro de los
     rangos de adecuación (0-35% de requerimiento).
   * Formato: La IA debe responder en formato JSON puro para que el sistema pueda procesarlo sin intervención humana.


  Paso 3: Integración y Persistencia en Base de Datos
  Convertiremos la sugerencia de la IA en registros reales.
   * Tarea: Actualizar nutricion/services/menu_service.py.
   * Flujo:
       1. Recibir el JSON de la IA.
       2. Hacer Fuzzy Matching (búsqueda difusa) para vincular los nombres de ingredientes de la IA con los codigo de TablaAlimentos2018Icbf.
       3. Crear automáticamente el objeto TablaMenus, sus TablaPreparaciones y los TablaIngredientesPorNivel con los pesos sugeridos.


  Paso 4: Validación y Seguridad Nutricional
   * Tarea: Ejecutar el CalculoService interno sobre el menú de la IA.
   * Objetivo: No confiamos ciegamente en la matemática de la IA. El sistema recalculará todo usando nuestras fórmulas de Django para asegurar que
     los aportes nutricionales sean 100% precisos antes de guardar.


  Paso 5: Interfaz de Usuario (UI)
   * Tarea: Crear la vista generar_menu_ia.html.
   * Funcionalidad: Un botón de "Generar con IA" que, al hacer clic, muestre un "Cargando..." y luego presente el menú propuesto con su semáforo
     de adecuación (Verde/Amarillo/Rojo) para aprobación del usuario.

  ---


  Archivos y Tablas Involucradas:
   1. Tablas de Entrada: minuta_patron.json, TablaAlimentos2018Icbf, TablaGradosEscolaresUapa.
   2. Tablas de Salida: TablaMenus, TablaPreparaciones, TablaIngredientesPorNivel, TablaAnalisisNutricionalMenu.


  ¿Deseas que comencemos con el Paso 1: Crear el `gemini_service.py` y la lógica para extraer los alimentos de la base de datos?