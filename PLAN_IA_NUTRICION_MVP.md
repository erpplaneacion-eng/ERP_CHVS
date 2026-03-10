# PLAN MVP IA NUTRICION

## 1. Objetivo

Implementar una primera version de apoyo con IA para que la nutricionista pueda generar un borrador completo de preparaciones para un menu, con revision humana obligatoria antes de guardar en la base de datos.

La IA no sera fuente de verdad nutricional ni normativa. Su rol sera proponer:

- preparaciones del menu,
- ingredientes de cada preparacion,
- componente sugerido,
- grupo sugerido,
- observaciones o justificacion opcional.

## 2. Problema actual

Hoy la app `nutricion` permite:

- crear menus por programa y modalidad,
- crear preparaciones por menu,
- asignar ingredientes ICBF a cada preparacion,
- ajustar pesos por nivel escolar,
- calcular analisis nutricional,
- validar reglas semanales y minuta,
- exportar Excel y PDF.

La carga manual de preparaciones e ingredientes por menu consume tiempo operativo a la nutricionista. El objetivo del MVP es acelerar esa etapa sin romper el flujo actual.

## 3. Vision del MVP

Desde un menu existente, la nutricionista podra pulsar una accion tipo `Generar borrador con IA`.

El sistema tomara contexto del menu y devolvera un borrador estructurado con:

- lista de preparaciones sugeridas,
- ingredientes sugeridos por preparacion,
- componente principal sugerido,
- grupo sugerido si aplica,
- alertas de validacion.

La nutricionista revisara, editara, aceptara o descartara el borrador antes de persistirlo en:

- `nutricion.TablaPreparaciones`
- `nutricion.TablaPreparacionIngredientes`

## 4. Alcance funcional del MVP

Incluye:

- generacion de borrador para un solo menu por ejecucion,
- uso exclusivo por parte de nutricionistas o usuarios autorizados,
- revision humana obligatoria,
- validacion contra catalogo ICBF existente,
- validacion basica de componente y grupo,
- trazabilidad de prompt, respuesta y aprobacion,
- persistencia final usando las tablas actuales de `nutricion`.

No incluye en esta fase:

- guardado automatico sin aprobacion,
- generacion masiva de todo el ciclo semanal o los 20 menus,
- ajuste automatico de pesos por nivel,
- cumplimiento garantizado de minuta o requerimiento semanal,
- reemplazo del analisis nutricional existente,
- autonomia completa del agente.

## 5. Recomendacion de arquitectura

### 5.1 Crear una app nueva

Se recomienda crear una app nueva, por ejemplo:

- `ai_assistant`

Razon:

- evita cargar mas la app `nutricion`,
- permite reutilizar la capacidad de IA en otros modulos,
- separa claramente dominio nutricional de orquestacion LLM,
- facilita auditoria, historico y cambio de proveedor de IA.

### 5.2 Responsabilidades por app

`nutricion`:

- reglas de negocio del menu,
- catalogo ICBF,
- componentes y grupos,
- minuta patron,
- analisis nutricional,
- persistencia final aprobada.

`ai_assistant`:

- construccion del contexto para el LLM,
- ejecucion de prompts,
- almacenamiento de sesiones,
- almacenamiento de respuesta cruda y parseada,
- validacion estructural inicial,
- borradores pendientes de aprobacion.

## 6. Flujo propuesto del usuario

### 6.1 Flujo principal

1. La nutricionista entra a un menu en `nutricion`.
2. Pulsa `Generar borrador con IA`.
3. El sistema construye contexto del menu:
   - programa,
   - modalidad,
   - menu actual,
   - preparaciones previas similares,
   - catalogo ICBF filtrado,
   - componentes y grupos validos.
4. El LLM devuelve un JSON estructurado.
5. El backend valida y clasifica cada sugerencia:
   - valida,
   - valida con duda,
   - invalida.
6. La UI muestra el borrador.
7. La nutricionista corrige si hace falta.
8. Al aprobar, se crean preparaciones e ingredientes reales en `nutricion`.

### 6.2 Regla clave

La IA nunca debe escribir directamente en las tablas productivas sin paso de aprobacion humana.

## 7. Contrato de salida del LLM

La salida debe ser JSON estricto. Ejemplo conceptual:

```json
{
  "menu_objetivo": {
    "id_menu": 123,
    "modalidad_id": "20501"
  },
  "preparaciones": [
    {
      "nombre": "Arroz con pollo",
      "componente_principal_sugerido": "C001",
      "grupo_sugerido": "G04",
      "ingredientes": [
        {
          "codigo_icbf": "A123",
          "nombre": "Arroz blanco",
          "cantidad_referencial": null
        },
        {
          "codigo_icbf": "B456",
          "nombre": "Pollo sin piel",
          "cantidad_referencial": null
        }
      ],
      "justificacion": "Preparacion usual para esta modalidad"
    }
  ]
}
```

## 8. Validaciones minimas del MVP

Antes de permitir aprobacion:

- cada preparacion debe tener nombre,
- cada preparacion debe tener al menos un ingrediente,
- cada ingrediente debe existir en `TablaAlimentos2018Icbf`,
- componente sugerido debe existir en `ComponentesAlimentos`,
- grupo sugerido debe existir en `GruposAlimentos` si viene informado,
- no se deben duplicar ingredientes dentro de la misma preparacion,
- no se deben duplicar preparaciones identicas en el mismo borrador sin aviso,
- si una sugerencia no mapea a catalogo real, debe quedar marcada para correccion manual.

## 9. Integracion con la app actual

Puntos de integracion recomendados:

- boton nuevo en `lista_menus` o en el editor de preparaciones,
- vista nueva de revision del borrador IA,
- accion final `Aprobar e importar al menu`.

El flujo actual de:

- `TablaPreparaciones`
- `TablaPreparacionIngredientes`
- editor por nivel
- analisis nutricional

debe mantenerse intacto.

La IA entra antes de la etapa de ajuste por nivel y antes del analisis final.

## 10. Modelo de datos sugerido para la nueva app

### 10.1 Sesion de generacion

Tabla sugerida: `GeneracionIA`

Campos tentativos:

- id
- modulo_origen
- entidad_objetivo
- entidad_id
- usuario_solicitante
- prompt_final
- modelo_llm
- estado
- respuesta_cruda
- respuesta_parseada
- errores_validacion
- fecha_creacion
- fecha_aprobacion
- usuario_aprobador

### 10.2 Borrador de salida

Tabla sugerida: `BorradorMenuIA`

Campos tentativos:

- id
- generacion
- id_menu
- modalidad_id
- estado_revision
- resumen_validacion

### 10.3 Detalle de borrador

Tabla sugerida: `BorradorPreparacionIA`

Campos tentativos:

- id
- borrador
- nombre_preparacion
- componente_sugerido
- grupo_sugerido
- estado_validacion
- observaciones

Tabla sugerida: `BorradorIngredienteIA`

Campos tentativos:

- id
- borrador_preparacion
- codigo_icbf
- nombre_sugerido
- estado_validacion
- observaciones

## 11. Proveedor LLM

Para el MVP conviene abstraer el proveedor desde el inicio.

Interfaz esperada:

- construir prompt,
- enviar solicitud,
- recibir respuesta,
- parsear JSON,
- manejar reintentos.

Debe quedar desacoplado de un proveedor especifico para poder usar:

- Gemini,
- OpenAI,
- otro proveedor futuro.

## 12. Estrategia de contexto para el LLM

No conviene enviar toda la base.

Contexto recomendado:

- modalidad del menu,
- programa,
- ejemplos de preparaciones ya existentes de esa modalidad,
- subconjunto de ingredientes ICBF relevantes,
- componentes validos de la modalidad,
- grupos permitidos,
- reglas resumidas de negocio.

En el MVP, la validacion fuerte se deja al backend. El contexto solo debe reducir alucinaciones.

## 13. Riesgos principales

### 13.1 Riesgo funcional

Que la IA proponga ingredientes inexistentes o combinaciones poco realistas.

Mitigacion:

- JSON estricto,
- catalogo filtrado,
- revision humana,
- validadores backend.

### 13.2 Riesgo de negocio

Que se confunda una sugerencia de IA con una formulacion nutricional aprobada.

Mitigacion:

- etiquetar siempre como `borrador IA`,
- no guardar automatico,
- auditoria completa.

### 13.3 Riesgo tecnico

Acoplar la IA directamente al dominio `nutricion` y volver mas fragil la app.

Mitigacion:

- app nueva,
- capas bien separadas,
- persistencia final delegada a `nutricion`.

## 14. Fases de implementacion sugeridas

### Fase 1. Fundacion

- crear app `ai_assistant`,
- definir modelos de sesion y borrador,
- definir proveedor LLM abstracto,
- definir esquema JSON de salida.

### Fase 2. Generacion controlada

- construir servicio para generar borrador de un menu,
- tomar contexto minimo desde `nutricion`,
- guardar prompt y respuesta.

### Fase 3. Validacion y revision

- validar ingredientes, componentes y grupos,
- crear UI de revision,
- permitir correccion manual.

### Fase 4. Importacion a nutricion

- convertir borrador aprobado en:
  - `TablaPreparaciones`
  - `TablaPreparacionIngredientes`

### Fase 5. Endurecimiento

- logs,
- metricas,
- historial,
- pruebas con casos reales de nutricionistas.

## 15. Criterios de exito del MVP

El MVP se considerara exitoso si:

- la nutricionista puede generar un borrador de un menu en pocos minutos,
- el borrador puede revisarse sin salir del flujo de `nutricion`,
- la mayoria de ingredientes sugeridos mapean al catalogo ICBF real,
- la aprobacion humana sigue siendo clara y obligatoria,
- el sistema no rompe el editor ni el analisis nutricional actual.

## 16. Decision recomendada

Se recomienda implementar esta funcionalidad como un MVP asistido, con una app nueva reutilizable y con aprobacion humana obligatoria.

La IA debe acelerar la construccion inicial del menu, no sustituir la validacion profesional ni la logica normativa ya implementada en `nutricion`.
